"""
Authentication & Authorization Middleware

Provides pluggable authentication for the Curriculum Mapping Service.
Supports: JWT, API Keys, OAuth2, and custom auth providers.
"""

from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from typing import Optional, Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication/Authorization error"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BaseAuthProvider:
    """Base class for authentication providers"""

    def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """
        Authenticate a request.

        Returns:
            User info dict if authenticated, None otherwise
        """
        raise NotImplementedError

    def get_token(self, user_info: Dict[str, Any]) -> str:
        """Generate a token for the user"""
        raise NotImplementedError


class JWTAuthProvider(BaseAuthProvider):
    """JWT-based authentication"""

    def __init__(self, secret_key: str, expiry_hours: int = 24, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
        self.algorithm = algorithm

        # Try to import PyJWT
        try:
            import jwt
            self.jwt = jwt
        except ImportError:
            logger.warning("PyJWT not installed. Install with: pip install PyJWT")
            self.jwt = None

    def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Validate JWT token from Authorization header"""
        if not self.jwt:
            raise AuthError("JWT authentication not available", 500)

        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            payload = self.jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check expiration
            exp = payload.get('exp')
            if exp and datetime.utcnow().timestamp() > exp:
                raise AuthError("Token expired")

            return {
                'user_id': payload.get('sub'),
                'email': payload.get('email'),
                'permissions': payload.get('permissions', []),
                'metadata': payload.get('metadata', {})
            }

        except self.jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {str(e)}")

    def get_token(self, user_info: Dict[str, Any]) -> str:
        """Generate a JWT token"""
        if not self.jwt:
            raise AuthError("JWT authentication not available", 500)

        payload = {
            'sub': user_info.get('user_id'),
            'email': user_info.get('email'),
            'permissions': user_info.get('permissions', []),
            'metadata': user_info.get('metadata', {}),
            'iat': datetime.utcnow().timestamp(),
            'exp': (datetime.utcnow() + timedelta(hours=self.expiry_hours)).timestamp()
        }

        return self.jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class APIKeyAuthProvider(BaseAuthProvider):
    """API Key-based authentication"""

    def __init__(self, header_name: str = 'X-API-Key', validate_func: Callable = None):
        self.header_name = header_name
        self.validate_func = validate_func or self._default_validate
        self._api_keys = {}  # In-memory store for demo

    def _default_validate(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Default validation using in-memory store"""
        return self._api_keys.get(api_key)

    def register_key(self, api_key: str, user_info: Dict[str, Any]):
        """Register an API key (for demo/testing)"""
        self._api_keys[api_key] = user_info

    def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Validate API key from header"""
        api_key = request.headers.get(self.header_name)

        if not api_key:
            return None

        user_info = self.validate_func(api_key)

        if not user_info:
            raise AuthError("Invalid API key")

        return user_info

    def get_token(self, user_info: Dict[str, Any]) -> str:
        """Generate an API key (for demo purposes)"""
        import secrets
        api_key = secrets.token_urlsafe(32)
        self._api_keys[api_key] = user_info
        return api_key


class OAuth2AuthProvider(BaseAuthProvider):
    """OAuth2-based authentication"""

    def __init__(self, client_id: str, client_secret: str,
                 authorize_url: str, token_url: str,
                 user_info_url: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.user_info_url = user_info_url

    def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Validate OAuth2 access token"""
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None

        access_token = auth_header[7:]

        if not self.user_info_url:
            raise AuthError("OAuth2 user info URL not configured", 500)

        # Fetch user info from OAuth2 provider
        try:
            import requests as http_requests
            response = http_requests.get(
                self.user_info_url,
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if response.status_code != 200:
                raise AuthError("Invalid access token")

            user_data = response.json()

            return {
                'user_id': user_data.get('sub') or user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'permissions': user_data.get('permissions', [])
            }

        except Exception as e:
            raise AuthError(f"OAuth2 validation failed: {str(e)}")

    def get_token(self, user_info: Dict[str, Any]) -> str:
        """OAuth2 tokens are issued by the OAuth provider, not by us"""
        raise NotImplementedError("Use OAuth2 provider to get tokens")


class CompositeAuthProvider(BaseAuthProvider):
    """Combines multiple auth providers (try each in order)"""

    def __init__(self, providers: list):
        self.providers = providers

    def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Try each provider in order"""
        for provider in self.providers:
            try:
                result = provider.authenticate(request)
                if result:
                    return result
            except AuthError:
                continue
        return None


class AuthMiddleware:
    """
    Authentication middleware for Flask.

    Usage:
        auth = AuthMiddleware(config)

        @app.route('/api/protected')
        @auth.require_auth
        def protected_endpoint():
            user = auth.get_current_user()
            ...

        @app.route('/api/admin')
        @auth.require_permission('admin')
        def admin_endpoint():
            ...
    """

    def __init__(self, config):
        """
        Initialize auth middleware.

        Args:
            config: AuthConfig object
        """
        self.config = config
        self.provider = self._create_provider()

    def _create_provider(self) -> BaseAuthProvider:
        """Create the appropriate auth provider"""
        if not self.config.enabled:
            return None

        if self.config.provider == 'jwt':
            return JWTAuthProvider(
                secret_key=self.config.secret_key,
                expiry_hours=self.config.token_expiry_hours
            )
        elif self.config.provider == 'api_key':
            return APIKeyAuthProvider(
                header_name=self.config.api_key_header
            )
        elif self.config.provider == 'oauth2':
            return OAuth2AuthProvider(
                client_id=self.config.oauth2_client_id,
                client_secret=self.config.oauth2_client_secret,
                authorize_url=self.config.oauth2_authorize_url,
                token_url=self.config.oauth2_token_url
            )
        else:
            raise ValueError(f"Unknown auth provider: {self.config.provider}")

    def require_auth(self, f: Callable) -> Callable:
        """Decorator to require authentication"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.config.enabled:
                return f(*args, **kwargs)

            try:
                user = self.provider.authenticate(request)
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401

                g.current_user = user
                return f(*args, **kwargs)

            except AuthError as e:
                return jsonify({'error': e.message}), e.status_code

        return decorated

    def require_permission(self, permission: str) -> Callable:
        """Decorator to require a specific permission"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated(*args, **kwargs):
                if not self.config.enabled:
                    return f(*args, **kwargs)

                try:
                    user = self.provider.authenticate(request)
                    if not user:
                        return jsonify({'error': 'Authentication required'}), 401

                    permissions = user.get('permissions', [])
                    if permission not in permissions and 'admin' not in permissions:
                        return jsonify({'error': f'Permission denied: {permission} required'}), 403

                    g.current_user = user
                    return f(*args, **kwargs)

                except AuthError as e:
                    return jsonify({'error': e.message}), e.status_code

            return decorated
        return decorator

    def optional_auth(self, f: Callable) -> Callable:
        """Decorator for optional authentication (user info available if provided)"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.config.enabled:
                return f(*args, **kwargs)

            try:
                user = self.provider.authenticate(request)
                g.current_user = user  # May be None
            except AuthError:
                g.current_user = None

            return f(*args, **kwargs)

        return decorated

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user"""
        return getattr(g, 'current_user', None)

    def generate_token(self, user_info: Dict[str, Any]) -> str:
        """Generate a token for a user"""
        if not self.provider:
            raise AuthError("Authentication not enabled", 500)
        return self.provider.get_token(user_info)


def log_action(user_id: str, action: str, details: Dict[str, Any] = None):
    """
    Audit logging for security-sensitive actions.

    Args:
        user_id: The ID of the user performing the action
        action: The action being performed
        details: Additional details about the action
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'action': action,
        'details': details or {},
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None
    }

    logger.info(f"AUDIT: {json.dumps(log_entry)}")

    return log_entry

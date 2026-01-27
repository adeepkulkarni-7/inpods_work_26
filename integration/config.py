"""
Configuration Management for Curriculum Mapping Service

Supports multiple environments and easy integration with existing config systems.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI connection configuration"""
    api_key: str
    endpoint: str
    api_version: str = "2024-02-15-preview"
    deployment: str = "gpt-4"

    def to_dict(self) -> Dict[str, str]:
        return {
            'api_key': self.api_key,
            'azure_endpoint': self.endpoint,
            'api_version': self.api_version,
            'deployment': self.deployment
        }


@dataclass
class StorageConfig:
    """File storage configuration"""
    upload_folder: str = "uploads"
    output_folder: str = "outputs"
    insights_folder: str = "outputs/insights"
    library_folder: str = "outputs/library"
    max_file_size_mb: int = 16
    allowed_extensions: tuple = ('csv', 'xlsx', 'xls', 'ods')


@dataclass
class DatabaseConfig:
    """Database configuration for persistent storage"""
    enabled: bool = False
    url: str = ""  # e.g., "postgresql://user:pass@localhost/dbname"
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class AuthConfig:
    """Authentication configuration"""
    enabled: bool = False
    provider: str = "jwt"  # "jwt", "oauth2", "api_key", "custom"
    secret_key: str = ""
    token_expiry_hours: int = 24
    api_key_header: str = "X-API-Key"

    # OAuth2 settings (if using)
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_authorize_url: str = ""
    oauth2_token_url: str = ""


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    max_questions_per_request: int = 100
    default_batch_size: int = 5
    requests_per_minute: int = 60
    api_call_delay_seconds: float = 0.5


@dataclass
class Config:
    """Main configuration class for the Curriculum Mapping Service"""

    # Service info
    service_name: str = "Curriculum Mapping Service"
    version: str = "2.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5001

    # Component configs
    azure: AzureOpenAIConfig = None
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    # CORS settings
    cors_origins: list = field(default_factory=lambda: ["*"])

    def __post_init__(self):
        """Ensure required directories exist"""
        os.makedirs(self.storage.upload_folder, exist_ok=True)
        os.makedirs(self.storage.output_folder, exist_ok=True)
        os.makedirs(self.storage.insights_folder, exist_ok=True)
        os.makedirs(self.storage.library_folder, exist_ok=True)

    def validate(self) -> tuple:
        """
        Validate configuration.
        Returns: (is_valid: bool, errors: list)
        """
        errors = []

        if not self.azure:
            errors.append("Azure OpenAI configuration is required")
        elif not self.azure.api_key:
            errors.append("Azure OpenAI API key is required")
        elif not self.azure.endpoint:
            errors.append("Azure OpenAI endpoint is required")

        if self.auth.enabled and self.auth.provider == "jwt" and not self.auth.secret_key:
            errors.append("JWT secret key is required when auth is enabled")

        return len(errors) == 0, errors


def get_config(env_file: str = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file

    Returns:
        Config: Populated configuration object
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    azure_config = AzureOpenAIConfig(
        api_key=os.getenv('AZURE_OPENAI_API_KEY', ''),
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
        deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    )

    storage_config = StorageConfig(
        upload_folder=os.getenv('UPLOAD_FOLDER', 'uploads'),
        output_folder=os.getenv('OUTPUT_FOLDER', 'outputs'),
        insights_folder=os.getenv('INSIGHTS_FOLDER', 'outputs/insights'),
        library_folder=os.getenv('LIBRARY_FOLDER', 'outputs/library'),
        max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '16'))
    )

    database_config = DatabaseConfig(
        enabled=os.getenv('DATABASE_ENABLED', 'false').lower() == 'true',
        url=os.getenv('DATABASE_URL', ''),
        pool_size=int(os.getenv('DATABASE_POOL_SIZE', '5'))
    )

    auth_config = AuthConfig(
        enabled=os.getenv('AUTH_ENABLED', 'false').lower() == 'true',
        provider=os.getenv('AUTH_PROVIDER', 'jwt'),
        secret_key=os.getenv('AUTH_SECRET_KEY', ''),
        token_expiry_hours=int(os.getenv('AUTH_TOKEN_EXPIRY_HOURS', '24')),
        api_key_header=os.getenv('AUTH_API_KEY_HEADER', 'X-API-Key')
    )

    rate_limit_config = RateLimitConfig(
        enabled=os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
        max_questions_per_request=int(os.getenv('MAX_QUESTIONS_PER_REQUEST', '100')),
        default_batch_size=int(os.getenv('BATCH_SIZE_DEFAULT', '5')),
        requests_per_minute=int(os.getenv('REQUESTS_PER_MINUTE', '60'))
    )

    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')

    return Config(
        service_name=os.getenv('SERVICE_NAME', 'Curriculum Mapping Service'),
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '5001')),
        azure=azure_config,
        storage=storage_config,
        database=database_config,
        auth=auth_config,
        rate_limit=rate_limit_config,
        cors_origins=cors_origins
    )


def from_dict(config_dict: Dict[str, Any]) -> Config:
    """
    Create Config from a dictionary.
    Useful for integrating with existing platform config systems.

    Example:
        config = from_dict({
            'azure': {
                'api_key': 'your-key',
                'endpoint': 'https://your-resource.openai.azure.com/'
            },
            'auth': {
                'enabled': True,
                'secret_key': 'your-secret'
            }
        })
    """
    azure_dict = config_dict.get('azure', {})
    azure_config = AzureOpenAIConfig(
        api_key=azure_dict.get('api_key', ''),
        endpoint=azure_dict.get('endpoint', ''),
        api_version=azure_dict.get('api_version', '2024-02-15-preview'),
        deployment=azure_dict.get('deployment', 'gpt-4')
    )

    storage_dict = config_dict.get('storage', {})
    storage_config = StorageConfig(**{k: v for k, v in storage_dict.items() if k in StorageConfig.__dataclass_fields__})

    db_dict = config_dict.get('database', {})
    database_config = DatabaseConfig(**{k: v for k, v in db_dict.items() if k in DatabaseConfig.__dataclass_fields__})

    auth_dict = config_dict.get('auth', {})
    auth_config = AuthConfig(**{k: v for k, v in auth_dict.items() if k in AuthConfig.__dataclass_fields__})

    rate_dict = config_dict.get('rate_limit', {})
    rate_config = RateLimitConfig(**{k: v for k, v in rate_dict.items() if k in RateLimitConfig.__dataclass_fields__})

    return Config(
        service_name=config_dict.get('service_name', 'Curriculum Mapping Service'),
        version=config_dict.get('version', '2.0.0'),
        debug=config_dict.get('debug', False),
        host=config_dict.get('host', '0.0.0.0'),
        port=config_dict.get('port', 5001),
        azure=azure_config,
        storage=storage_config,
        database=database_config,
        auth=auth_config,
        rate_limit=rate_config,
        cors_origins=config_dict.get('cors_origins', ['*'])
    )

"""
Flask Application Factory for Curriculum Mapping Microservice

Provides a configurable Flask app with authentication, rate limiting,
and all curriculum mapping endpoints.

Usage:
    # Option 1: Use default config from environment
    from integration import create_app
    app = create_app()
    app.run()

    # Option 2: Use custom config
    from integration import create_app, Config
    config = Config(...)
    app = create_app(config)

    # Option 3: Use with existing Flask app
    from integration.app import register_blueprint
    register_blueprint(existing_app, config)
"""

from flask import Flask, Blueprint, request, jsonify, send_file, g
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import logging

from .config import Config, get_config
from .engine import AuditEngine, LibraryManager
from .visualization import VisualizationEngine
from .auth import AuthMiddleware, log_action

logger = logging.getLogger(__name__)

# Global instances (set during app creation)
_audit_engine = None
_viz_engine = None
_library_manager = None
_auth_middleware = None
_config = None


def create_app(config: Config = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config: Optional Config object. If not provided, loads from environment.

    Returns:
        Configured Flask application
    """
    global _audit_engine, _viz_engine, _library_manager, _auth_middleware, _config

    # Load config
    if config is None:
        config = get_config()

    _config = config

    # Validate config
    is_valid, errors = config.validate()
    if not is_valid:
        raise ValueError(f"Invalid configuration: {errors}")

    # Create Flask app
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.storage.max_file_size_mb * 1024 * 1024

    # Setup CORS
    CORS(app, origins=config.cors_origins)

    # Initialize engines
    print(f"[*] Initializing {config.service_name}...")

    _audit_engine = AuditEngine(config.azure.to_dict())
    if _audit_engine.test_connection():
        print("[OK] Azure OpenAI connected successfully")
    else:
        raise ConnectionError("Failed to connect to Azure OpenAI")

    _viz_engine = VisualizationEngine(output_folder=config.storage.insights_folder)
    _library_manager = LibraryManager(library_folder=config.storage.library_folder)

    # Initialize auth
    _auth_middleware = AuthMiddleware(config.auth)

    # Register blueprint
    app.register_blueprint(create_blueprint(config))

    print(f"\n{'='*50}")
    print(f"{config.service_name} v{config.version}")
    print(f"{'='*50}")
    print(f"[*] Running on http://{config.host}:{config.port}")
    print(f"[*] Auth: {'Enabled' if config.auth.enabled else 'Disabled'}")
    print(f"[*] Database: {'Enabled' if config.database.enabled else 'Disabled (file-based)'}")
    print(f"{'='*50}\n")

    return app


def create_blueprint(config: Config) -> Blueprint:
    """Create the API blueprint with all endpoints."""

    bp = Blueprint('curriculum', __name__, url_prefix='/api')

    # Helper: Check allowed file extensions
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in config.storage.allowed_extensions

    # Helper: Get current user (if authenticated)
    def get_current_user():
        return getattr(g, 'current_user', None)

    # ============================================
    # HEALTH & INFO ENDPOINTS
    # ============================================

    @bp.route('/health', methods=['GET'])
    def health_check():
        """Service health check - no auth required"""
        return jsonify({
            'status': 'ok',
            'service': config.service_name,
            'version': config.version,
            'azure_connected': _audit_engine is not None
        })

    @bp.route('/info', methods=['GET'])
    def service_info():
        """Service information"""
        return jsonify({
            'service': config.service_name,
            'version': config.version,
            'auth_enabled': config.auth.enabled,
            'auth_provider': config.auth.provider if config.auth.enabled else None,
            'supported_dimensions': ['area_topics', 'competency', 'objective', 'skill', 'nmc_competency'],
            'max_file_size_mb': config.storage.max_file_size_mb,
            'allowed_extensions': list(config.storage.allowed_extensions)
        })

    # ============================================
    # MODE A: MAP UNMAPPED QUESTIONS
    # ============================================

    @bp.route('/upload', methods=['POST'])
    @_auth_middleware.optional_auth
    def upload_files():
        """Upload question bank and reference curriculum files"""
        try:
            if 'question_file' not in request.files or 'reference_file' not in request.files:
                return jsonify({'error': 'Both question_file and reference_file required'}), 400

            question_file = request.files['question_file']
            reference_file = request.files['reference_file']

            if question_file.filename == '' or reference_file.filename == '':
                return jsonify({'error': 'No files selected'}), 400

            if not (allowed_file(question_file.filename) and allowed_file(reference_file.filename)):
                return jsonify({'error': 'Only CSV/Excel files allowed'}), 400

            # Save files
            question_filename = secure_filename(question_file.filename)
            reference_filename = secure_filename(reference_file.filename)

            question_path = os.path.join(config.storage.upload_folder, question_filename)
            reference_path = os.path.join(config.storage.upload_folder, reference_filename)

            question_file.save(question_path)
            reference_file.save(reference_path)

            # Read and validate
            question_df = pd.read_csv(question_path) if question_path.endswith('.csv') else pd.read_excel(question_path)
            reference_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)

            # Audit log
            user = get_current_user()
            if user:
                log_action(user.get('user_id'), 'upload_files', {
                    'question_file': question_filename,
                    'reference_file': reference_filename
                })

            return jsonify({
                'status': 'success',
                'question_file': question_filename,
                'reference_file': reference_filename,
                'question_count': len(question_df),
                'reference_count': len(reference_df)
            })

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/run-audit', methods=['POST'])
    @_auth_middleware.optional_auth
    def run_audit():
        """Map questions to curriculum (single-question mode)"""
        try:
            data = request.json
            question_file = data.get('question_file')
            reference_file = data.get('reference_file')
            dimension = data.get('dimension')

            if not all([question_file, reference_file, dimension]):
                return jsonify({'error': 'Missing required parameters'}), 400

            question_path = os.path.join(config.storage.upload_folder, question_file)
            reference_path = os.path.join(config.storage.upload_folder, reference_file)

            result = _audit_engine.run_audit(
                question_csv=question_path,
                reference_csv=reference_path,
                dimension=dimension
            )

            return jsonify(result)

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/run-audit-efficient', methods=['POST'])
    @_auth_middleware.optional_auth
    def run_audit_efficient():
        """Map questions to curriculum (batched mode - 60-70% cost savings)"""
        try:
            data = request.json
            question_file = data.get('question_file')
            reference_file = data.get('reference_file')
            dimension = data.get('dimension')
            batch_size = data.get('batch_size', config.rate_limit.default_batch_size)

            if not all([question_file, reference_file, dimension]):
                return jsonify({'error': 'Missing required parameters'}), 400

            batch_size = max(1, min(10, int(batch_size)))

            question_path = os.path.join(config.storage.upload_folder, question_file)
            reference_path = os.path.join(config.storage.upload_folder, reference_file)

            result = _audit_engine.run_audit_batched(
                question_csv=question_path,
                reference_csv=reference_path,
                dimension=dimension,
                batch_size=batch_size
            )

            return jsonify(result)

        except Exception as e:
            logger.error(f"Batched audit failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/apply-changes', methods=['POST'])
    @_auth_middleware.optional_auth
    def apply_changes():
        """Apply selected recommendations and export Excel"""
        try:
            data = request.json
            question_file = data.get('question_file')
            recommendations = data.get('recommendations')
            selected_indices = data.get('selected_indices')
            dimension = data.get('dimension')

            if not all([question_file, recommendations, selected_indices is not None, dimension]):
                return jsonify({'error': 'Missing required parameters'}), 400

            question_path = os.path.join(config.storage.upload_folder, question_file)

            output_path = _audit_engine.apply_and_export(
                question_csv=question_path,
                recommendations=recommendations,
                selected_indices=selected_indices,
                dimension=dimension,
                output_folder=config.storage.output_folder
            )

            return jsonify({
                'status': 'success',
                'output_file': os.path.basename(output_path),
                'download_url': f'/api/download/{os.path.basename(output_path)}'
            })

        except Exception as e:
            logger.error(f"Apply changes failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/download/<filename>', methods=['GET'])
    def download_file(filename):
        """Download generated Excel file"""
        try:
            file_path = os.path.join(config.storage.output_folder, filename)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ============================================
    # MODE B: RATE EXISTING MAPPINGS
    # ============================================

    @bp.route('/upload-mapped', methods=['POST'])
    @_auth_middleware.optional_auth
    def upload_mapped_file():
        """Upload a file with existing mappings"""
        try:
            if 'mapped_file' not in request.files:
                return jsonify({'error': 'mapped_file required'}), 400

            mapped_file = request.files['mapped_file']
            reference_file = request.files.get('reference_file')

            if mapped_file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            # Save mapped file
            mapped_filename = secure_filename(mapped_file.filename)
            mapped_path = os.path.join(config.storage.upload_folder, mapped_filename)
            mapped_file.save(mapped_path)

            # Read mapped file
            if mapped_path.endswith('.csv'):
                mapped_df = pd.read_csv(mapped_path)
            elif mapped_path.endswith('.ods'):
                mapped_df = pd.read_excel(mapped_path, engine='odf')
            else:
                mapped_df = pd.read_excel(mapped_path, engine='openpyxl')

            response = {
                'status': 'success',
                'mapped_file': mapped_filename,
                'question_count': len(mapped_df),
                'columns': mapped_df.columns.tolist()
            }

            # Save reference file if provided
            if reference_file and reference_file.filename != '':
                reference_filename = secure_filename(reference_file.filename)
                reference_path = os.path.join(config.storage.upload_folder, reference_filename)
                reference_file.save(reference_path)
                reference_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
                response['reference_file'] = reference_filename
                response['reference_count'] = len(reference_df)

            return jsonify(response)

        except Exception as e:
            logger.error(f"Upload mapped failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/rate-mappings', methods=['POST'])
    @_auth_middleware.optional_auth
    def rate_mappings():
        """Rate existing mappings and suggest alternatives"""
        try:
            data = request.json
            mapped_file = data.get('mapped_file')
            reference_file = data.get('reference_file')
            dimension = data.get('dimension', 'area_topics')
            batch_size = data.get('batch_size', config.rate_limit.default_batch_size)

            if not mapped_file:
                return jsonify({'error': 'mapped_file required'}), 400

            if not reference_file:
                return jsonify({'error': 'reference_file required'}), 400

            batch_size = max(1, min(10, int(batch_size)))

            mapped_path = os.path.join(config.storage.upload_folder, mapped_file)
            reference_path = os.path.join(config.storage.upload_folder, reference_file)

            result = _audit_engine.rate_existing_mappings(
                mapped_file=mapped_path,
                reference_csv=reference_path,
                dimension=dimension,
                batch_size=batch_size
            )

            return jsonify(result)

        except Exception as e:
            logger.error(f"Rate mappings failed: {e}")
            return jsonify({'error': str(e)}), 500

    # ============================================
    # MODE C: GENERATE INSIGHTS
    # ============================================

    @bp.route('/generate-insights', methods=['POST'])
    @_auth_middleware.optional_auth
    def generate_insights():
        """Generate visualization charts from mapping data"""
        try:
            data = request.json
            mapped_file = data.get('mapped_file')
            reference_file = data.get('reference_file')

            if not mapped_file:
                return jsonify({'error': 'mapped_file required'}), 400

            mapped_path = os.path.join(config.storage.upload_folder, mapped_file)

            # Load mapped data
            if mapped_path.endswith('.csv'):
                mapped_df = pd.read_csv(mapped_path)
            elif mapped_path.endswith('.ods'):
                mapped_df = pd.read_excel(mapped_path, engine='odf')
            else:
                mapped_df = pd.read_excel(mapped_path, engine='openpyxl')

            # Build mapping data structure
            coverage = {}
            recommendations = []

            for idx, row in mapped_df.iterrows():
                topic = None
                for col in ['mapped_topic', 'mapped_objective', 'objective_id', 'Objective',
                            'mapped_competency', 'competency_id', 'mapped_skill', 'skill_id',
                            'mapped_nmc_competency', 'nmc_competency_id', 'mapped_id']:
                    if col in row and pd.notna(row.get(col)) and row.get(col):
                        topic = str(row.get(col)).strip()
                        break

                if topic:
                    coverage[topic] = coverage.get(topic, 0) + 1

                confidence = row.get('confidence_score', 0.0)
                if pd.isna(confidence):
                    confidence = 0.85

                recommendations.append({
                    'confidence': float(confidence),
                    'question_num': row.get('Question Number', f'Q{idx+1}')
                })

            mapping_data = {
                'coverage': coverage,
                'recommendations': recommendations
            }

            # Get reference topics
            reference_topics = list(coverage.keys())
            if reference_file:
                reference_path = os.path.join(config.storage.upload_folder, reference_file)
                if os.path.exists(reference_path):
                    ref_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
                    if 'Topic Area (CBME)' in ref_df.columns:
                        reference_topics = ref_df['Topic Area (CBME)'].dropna().tolist()
                    elif 'Topic Area' in ref_df.columns:
                        reference_topics = ref_df['Topic Area'].dropna().tolist()

            # Generate all charts
            charts = _viz_engine.generate_all_insights(mapping_data, reference_topics)

            # Return chart URLs
            chart_urls = {}
            for chart_name, filepath in charts.items():
                filename = os.path.basename(filepath)
                chart_urls[chart_name] = f'/api/insights/{filename}'

            return jsonify({
                'status': 'success',
                'charts': chart_urls,
                'summary': {
                    'total_questions': len(recommendations),
                    'topics_covered': len(coverage),
                    'average_confidence': sum(r['confidence'] for r in recommendations) / len(recommendations) if recommendations else 0,
                    'coverage': coverage
                }
            })

        except Exception as e:
            logger.error(f"Generate insights failed: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/insights/<filename>', methods=['GET'])
    def download_insight(filename):
        """Download insight chart image"""
        try:
            file_path = os.path.join(config.storage.insights_folder, filename)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='image/png')
            else:
                return jsonify({'error': 'Chart not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ============================================
    # LIBRARY MANAGEMENT
    # ============================================

    @bp.route('/library', methods=['GET'])
    @_auth_middleware.optional_auth
    def list_library():
        """List all saved mapping sets"""
        try:
            mappings = _library_manager.list_mappings()
            return jsonify({
                'status': 'success',
                'mappings': mappings,
                'total': len(mappings)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/library/save', methods=['POST'])
    @_auth_middleware.optional_auth
    def save_to_library():
        """Save current mapping results to library"""
        try:
            data = request.json
            name = data.get('name', f'Mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            recommendations = data.get('recommendations', [])
            dimension = data.get('dimension', 'area_topics')
            mode = data.get('mode', 'A')
            source_file = data.get('source_file', '')

            if not recommendations:
                return jsonify({'error': 'No recommendations to save'}), 400

            result = _library_manager.save_mapping(
                name=name,
                recommendations=recommendations,
                dimension=dimension,
                mode=mode,
                source_file=source_file
            )

            return jsonify({
                'status': 'success',
                'id': result['id'],
                'name': result['name'],
                'message': f'Saved {len(recommendations)} mappings to library'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/library/<mapping_id>', methods=['GET'])
    @_auth_middleware.optional_auth
    def load_from_library(mapping_id):
        """Load a specific mapping set from library"""
        try:
            data = _library_manager.get_mapping(mapping_id)
            if not data:
                return jsonify({'error': 'Mapping not found'}), 404

            return jsonify({
                'status': 'success',
                'mapping': data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/library/<mapping_id>', methods=['DELETE'])
    @_auth_middleware.optional_auth
    def delete_from_library(mapping_id):
        """Delete a mapping set from library"""
        try:
            success = _library_manager.delete_mapping(mapping_id)
            if not success:
                return jsonify({'error': 'Mapping not found'}), 404

            return jsonify({
                'status': 'success',
                'message': f'Deleted mapping {mapping_id}'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/library/<mapping_id>/export', methods=['GET'])
    @_auth_middleware.optional_auth
    def export_from_library(mapping_id):
        """Export a saved mapping to Excel"""
        try:
            output_path = _library_manager.export_to_excel(
                mapping_id=mapping_id,
                output_folder=config.storage.output_folder
            )

            if not output_path:
                return jsonify({'error': 'Mapping not found'}), 404

            return jsonify({
                'status': 'success',
                'download_url': f'/api/download/{os.path.basename(output_path)}'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ============================================
    # AUTH ENDPOINTS (when auth is enabled)
    # ============================================

    @bp.route('/auth/token', methods=['POST'])
    def get_token():
        """Get authentication token (for testing/demo)"""
        if not config.auth.enabled:
            return jsonify({'error': 'Authentication not enabled'}), 400

        data = request.json
        user_id = data.get('user_id')
        email = data.get('email')

        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        try:
            token = _auth_middleware.generate_token({
                'user_id': user_id,
                'email': email,
                'permissions': data.get('permissions', ['curriculum_mapping'])
            })

            return jsonify({
                'status': 'success',
                'token': token,
                'token_type': 'Bearer'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp


def register_blueprint(app: Flask, config: Config = None):
    """
    Register curriculum mapping endpoints on an existing Flask app.

    Usage:
        from flask import Flask
        from integration.app import register_blueprint

        app = Flask(__name__)
        register_blueprint(app, config)
    """
    global _audit_engine, _viz_engine, _library_manager, _auth_middleware, _config

    if config is None:
        config = get_config()

    _config = config

    # Initialize engines
    _audit_engine = AuditEngine(config.azure.to_dict())
    _viz_engine = VisualizationEngine(output_folder=config.storage.insights_folder)
    _library_manager = LibraryManager(library_folder=config.storage.library_folder)
    _auth_middleware = AuthMiddleware(config.auth)

    # Register blueprint
    app.register_blueprint(create_blueprint(config))


# ============================================
# STANDALONE ENTRY POINT
# ============================================

if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=_config.debug,
        host=_config.host,
        port=_config.port
    )

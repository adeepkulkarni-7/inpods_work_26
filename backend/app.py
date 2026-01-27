"""
Inpods Audit Engine - Flask Backend
Curriculum mapping analysis and improvement system

API Functions designed as discrete tools for future agent integration.
Each endpoint is a self-contained operation with clear inputs/outputs.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import uuid
from dotenv import load_dotenv

from audit_engine import AuditEngine
from visualization_engine import VisualizationEngine

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
INSIGHTS_FOLDER = 'outputs/insights'
LIBRARY_FOLDER = 'outputs/library'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'ods'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(INSIGHTS_FOLDER, exist_ok=True)
os.makedirs(LIBRARY_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['INSIGHTS_FOLDER'] = INSIGHTS_FOLDER
app.config['LIBRARY_FOLDER'] = LIBRARY_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize visualization engine
viz_engine = VisualizationEngine(output_folder=INSIGHTS_FOLDER)

# Initialize audit engine on startup
print("[*] Initializing Inpods Audit Engine...")

azure_config = {
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
    'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
}

# Validate configuration
if not azure_config['api_key'] or not azure_config['azure_endpoint']:
    print("[ERROR] Azure OpenAI credentials not found!")
    print("Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env file")
    print("Copy .env.example to .env and fill in your credentials")
    exit(1)

try:
    audit_engine = AuditEngine(azure_config)
    if audit_engine.test_connection():
        print("[OK] Azure OpenAI connected successfully")
    else:
        print("[ERROR] Failed to connect to Azure OpenAI")
        exit(1)
except Exception as e:
    print(f"[ERROR] Failed to initialize audit engine: {e}")
    exit(1)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Inpods Audit Engine',
        'version': '1.0.0',
        'azure_connected': audit_engine is not None
    })


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload question CSV and reference CSV"""
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
        
        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_filename)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_filename)
        
        question_file.save(question_path)
        reference_file.save(reference_path)
        
        # Read and validate files
        question_df = pd.read_csv(question_path) if question_path.endswith('.csv') else pd.read_excel(question_path)
        reference_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
        
        return jsonify({
            'status': 'success',
            'question_file': question_filename,
            'reference_file': reference_filename,
            'question_count': len(question_df),
            'reference_count': len(reference_df)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run-audit', methods=['POST'])
def run_audit():
    """Run mapping audit for selected dimension"""
    try:
        data = request.json
        question_file = data.get('question_file')
        reference_file = data.get('reference_file')
        dimension = data.get('dimension')  # 'area_topics', 'competency', 'objective', 'skill'
        
        if not all([question_file, reference_file, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)
        
        # Run audit
        result = audit_engine.run_audit(
            question_csv=question_path,
            reference_csv=reference_path,
            dimension=dimension
        )
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run-audit-efficient', methods=['POST'])
def run_audit_efficient():
    """Run mapping audit with batching (60-70% token savings)"""
    try:
        data = request.json
        question_file = data.get('question_file')
        reference_file = data.get('reference_file')
        dimension = data.get('dimension')
        batch_size = data.get('batch_size', 5)  # Default batch size of 5

        if not all([question_file, reference_file, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        # Validate batch_size
        batch_size = max(1, min(10, int(batch_size)))  # Clamp between 1-10

        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)

        # Run batched audit
        result = audit_engine.run_audit_batched(
            question_csv=question_path,
            reference_csv=reference_path,
            dimension=dimension,
            batch_size=batch_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/apply-changes', methods=['POST'])
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
        
        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)
        
        # Apply changes and generate Excel
        output_path = audit_engine.apply_and_export(
            question_csv=question_path,
            recommendations=recommendations,
            selected_indices=selected_indices,
            dimension=dimension,
            output_folder=app.config['OUTPUT_FOLDER']
        )
        
        return jsonify({
            'status': 'success',
            'output_file': os.path.basename(output_path),
            'download_url': f'/download/{os.path.basename(output_path)}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download exported Excel file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MODE B: Rate Existing Mappings
# ============================================

@app.route('/api/upload-mapped', methods=['POST'])
def upload_mapped_file():
    """Upload a file with existing mappings (for Mode B and C)"""
    try:
        if 'mapped_file' not in request.files:
            return jsonify({'error': 'mapped_file required'}), 400

        mapped_file = request.files['mapped_file']
        reference_file = request.files.get('reference_file')

        if mapped_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save mapped file
        mapped_filename = secure_filename(mapped_file.filename)
        mapped_path = os.path.join(app.config['UPLOAD_FOLDER'], mapped_filename)
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
            reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_filename)
            reference_file.save(reference_path)
            reference_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
            response['reference_file'] = reference_filename
            response['reference_count'] = len(reference_df)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rate-mappings', methods=['POST'])
def rate_mappings():
    """Rate existing mappings and suggest alternatives (Mode B)"""
    try:
        data = request.json
        mapped_file = data.get('mapped_file')
        reference_file = data.get('reference_file')
        dimension = data.get('dimension', 'area_topics')
        batch_size = data.get('batch_size', 5)

        if not mapped_file:
            return jsonify({'error': 'mapped_file required'}), 400

        if not reference_file:
            return jsonify({'error': 'reference_file required'}), 400

        batch_size = max(1, min(10, int(batch_size)))

        mapped_path = os.path.join(app.config['UPLOAD_FOLDER'], mapped_file)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)

        # Run rating
        result = audit_engine.rate_existing_mappings(
            mapped_file=mapped_path,
            reference_csv=reference_path,
            dimension=dimension,
            batch_size=batch_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MODE C: Generate Insights & Visualizations
# ============================================

@app.route('/api/generate-insights', methods=['POST'])
def generate_insights():
    """Generate visualization charts from mapping data (Mode C)"""
    try:
        data = request.json
        mapped_file = data.get('mapped_file')
        reference_file = data.get('reference_file')

        if not mapped_file:
            return jsonify({'error': 'mapped_file required'}), 400

        mapped_path = os.path.join(app.config['UPLOAD_FOLDER'], mapped_file)

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
            topic = row.get('mapped_topic', '')
            if pd.notna(topic) and topic:
                coverage[topic] = coverage.get(topic, 0) + 1

            confidence = row.get('confidence_score', 0.0)
            if pd.isna(confidence):
                confidence = 0.85  # Default if missing

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
            reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)
            if os.path.exists(reference_path):
                ref_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
                if 'Topic Area (CBME)' in ref_df.columns:
                    reference_topics = ref_df['Topic Area (CBME)'].dropna().tolist()
                elif 'Topic Area' in ref_df.columns:
                    reference_topics = ref_df['Topic Area'].dropna().tolist()

        # Generate all charts
        charts = viz_engine.generate_all_insights(mapping_data, reference_topics)

        # Return chart URLs
        chart_urls = {}
        for chart_name, filepath in charts.items():
            filename = os.path.basename(filepath)
            chart_urls[chart_name] = f'/insights/{filename}'

        return jsonify({
            'status': 'success',
            'charts': chart_urls,
            'summary': {
                'total_questions': len(recommendations),
                'topics_covered': len(coverage),
                'average_confidence': sum(r['confidence'] for r in recommendations) / len(recommendations) if recommendations else 0
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/<filename>', methods=['GET'])
def download_insight(filename):
    """Download insight chart image"""
    try:
        file_path = os.path.join(app.config['INSIGHTS_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Chart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# LIBRARY: Save & Manage Mapping Sets
# ============================================

@app.route('/api/library', methods=['GET'])
def list_library():
    """
    List all saved mapping sets in the library.
    Tool: list_saved_mappings
    """
    try:
        library_path = app.config['LIBRARY_FOLDER']
        mappings = []

        for filename in os.listdir(library_path):
            if filename.endswith('.json'):
                filepath = os.path.join(library_path, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    mappings.append({
                        'id': data.get('id'),
                        'name': data.get('name'),
                        'created_at': data.get('created_at'),
                        'question_count': data.get('question_count', 0),
                        'dimension': data.get('dimension'),
                        'mode': data.get('mode', 'A')
                    })

        # Sort by created_at descending
        mappings.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return jsonify({
            'status': 'success',
            'mappings': mappings,
            'total': len(mappings)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/save', methods=['POST'])
def save_to_library():
    """
    Save current mapping results to library.
    Tool: save_mapping_to_library
    """
    try:
        data = request.json
        name = data.get('name', f'Mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        recommendations = data.get('recommendations', [])
        dimension = data.get('dimension', 'area_topics')
        mode = data.get('mode', 'A')
        source_file = data.get('source_file', '')

        if not recommendations:
            return jsonify({'error': 'No recommendations to save'}), 400

        mapping_id = str(uuid.uuid4())[:8]

        library_data = {
            'id': mapping_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'dimension': dimension,
            'mode': mode,
            'source_file': source_file,
            'question_count': len(recommendations),
            'recommendations': recommendations
        }

        filepath = os.path.join(app.config['LIBRARY_FOLDER'], f'{mapping_id}.json')
        with open(filepath, 'w') as f:
            json.dump(library_data, f, indent=2)

        return jsonify({
            'status': 'success',
            'id': mapping_id,
            'name': name,
            'message': f'Saved {len(recommendations)} mappings to library'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/<mapping_id>', methods=['GET'])
def load_from_library(mapping_id):
    """
    Load a specific mapping set from library.
    Tool: load_mapping_from_library
    """
    try:
        filepath = os.path.join(app.config['LIBRARY_FOLDER'], f'{mapping_id}.json')

        if not os.path.exists(filepath):
            return jsonify({'error': 'Mapping not found'}), 404

        with open(filepath, 'r') as f:
            data = json.load(f)

        return jsonify({
            'status': 'success',
            'mapping': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/<mapping_id>', methods=['DELETE'])
def delete_from_library(mapping_id):
    """
    Delete a mapping set from library.
    Tool: delete_mapping_from_library
    """
    try:
        filepath = os.path.join(app.config['LIBRARY_FOLDER'], f'{mapping_id}.json')

        if not os.path.exists(filepath):
            return jsonify({'error': 'Mapping not found'}), 404

        os.remove(filepath)

        return jsonify({
            'status': 'success',
            'message': f'Deleted mapping {mapping_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/<mapping_id>/export', methods=['GET'])
def export_from_library(mapping_id):
    """
    Export a saved mapping to Excel/CSV.
    Tool: export_mapping_to_file
    """
    try:
        filepath = os.path.join(app.config['LIBRARY_FOLDER'], f'{mapping_id}.json')

        if not os.path.exists(filepath):
            return jsonify({'error': 'Mapping not found'}), 404

        with open(filepath, 'r') as f:
            data = json.load(f)

        recommendations = data.get('recommendations', [])

        # Build DataFrame
        rows = []
        for rec in recommendations:
            rows.append({
                'Question Number': rec.get('question_num', ''),
                'Question': rec.get('question_text', ''),
                'Mapped Topic': rec.get('mapped_topic', rec.get('recommended_mapping', '')),
                'Mapped Subtopic': rec.get('mapped_subtopic', ''),
                'Confidence': rec.get('confidence', 0),
                'Justification': rec.get('justification', '')
            })

        df = pd.DataFrame(rows)

        output_filename = f"{data.get('name', 'export')}_{mapping_id}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        df.to_excel(output_path, index=False)

        return jsonify({
            'status': 'success',
            'download_url': f'/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n[*] Starting Inpods Audit Engine on http://localhost:5000")
    print("[*] Open http://localhost:8000 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

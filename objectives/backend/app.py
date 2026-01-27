"""
Objectives Mapping API
Flask backend for Learning Objectives (O1-O6) mapping system

Three Tools:
1. Map Unmapped Questions to Objectives
2. Rate Existing Objective Mappings
3. Generate Insights & Visualizations
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from objectives_engine import ObjectivesEngine, OBJECTIVES_REFERENCE
from objectives_viz import ObjectivesVizEngine

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
INSIGHTS_FOLDER = 'outputs/insights'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'ods'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(INSIGHTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['INSIGHTS_FOLDER'] = INSIGHTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize engines
print("[*] Initializing Objectives Mapping Engine...")

azure_config = {
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
    'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
}

if not azure_config['api_key'] or not azure_config['azure_endpoint']:
    print("[ERROR] Azure OpenAI credentials not found!")
    print("Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env file")
    exit(1)

try:
    engine = ObjectivesEngine(azure_config)
    viz_engine = ObjectivesVizEngine(output_folder=INSIGHTS_FOLDER)
    if engine.test_connection():
        print("[OK] Azure OpenAI connected")
    else:
        print("[ERROR] Connection failed")
        exit(1)
except Exception as e:
    print(f"[ERROR] Init failed: {e}")
    exit(1)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# Health & Reference
# ============================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Objectives Mapping Engine',
        'version': '1.0.0'
    })


@app.route('/api/objectives', methods=['GET'])
def get_objectives():
    """Get list of available objectives"""
    return jsonify({
        'objectives': [
            {'id': obj_id, 'description': desc}
            for obj_id, desc in OBJECTIVES_REFERENCE.items()
        ]
    })


# ============================================
# File Upload
# ============================================

@app.route('/api/upload', methods=['POST'])
def upload_questions():
    """Upload question CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV/Excel files allowed'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Read and validate
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith('.ods'):
            df = pd.read_excel(filepath, engine='odf')
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        # Count non-stem questions
        question_count = len([1 for _, r in df.iterrows()
                             if '(Stem)' not in str(r.get('Question Number', ''))])

        return jsonify({
            'status': 'success',
            'filename': filename,
            'total_rows': len(df),
            'question_count': question_count,
            'columns': df.columns.tolist()
        })
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 400


# ============================================
# TOOL 1: Map Unmapped Questions
# ============================================

@app.route('/api/tool1/map', methods=['POST'])
def tool1_map():
    """
    Tool 1: Map unmapped questions to objectives

    Request:
        {
            "filename": "questions.csv",
            "batch_size": 5
        }

    Returns:
        {
            "recommendations": [...],
            "coverage": {...},
            "gaps": [...]
        }
    """
    data = request.json
    filename = data.get('filename')
    batch_size = data.get('batch_size', 5)

    if not filename:
        return jsonify({'error': 'filename required'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        result = engine.map_questions(filepath, batch_size=batch_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tool1/export', methods=['POST'])
def tool1_export():
    """
    Export selected mappings to Excel

    Request:
        {
            "filename": "questions.csv",
            "recommendations": [...],
            "selected_indices": [0, 1, 2]
        }
    """
    data = request.json
    filename = data.get('filename')
    recommendations = data.get('recommendations', [])
    selected = data.get('selected_indices', [])

    if not filename or not recommendations:
        return jsonify({'error': 'filename and recommendations required'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        output_path = engine.apply_and_export(
            filepath, recommendations, selected, app.config['OUTPUT_FOLDER']
        )
        return jsonify({
            'status': 'success',
            'output_file': os.path.basename(output_path),
            'download_url': f'/api/download/{os.path.basename(output_path)}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# TOOL 2: Rate Existing Mappings
# ============================================

@app.route('/api/tool2/rate', methods=['POST'])
def tool2_rate():
    """
    Tool 2: Rate existing objective mappings

    Request:
        {
            "filename": "mapped_questions.xlsx",
            "batch_size": 5
        }

    Returns:
        {
            "ratings": [...],
            "summary": {...},
            "recommendations": [...]
        }
    """
    data = request.json
    filename = data.get('filename')
    batch_size = data.get('batch_size', 5)

    if not filename:
        return jsonify({'error': 'filename required'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        result = engine.rate_mappings(filepath, batch_size=batch_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tool2/export', methods=['POST'])
def tool2_export():
    """
    Export corrected mappings to Excel

    Request:
        {
            "filename": "mapped_questions.xlsx",
            "recommendations": [...],
            "selected_indices": [0, 1, 2]
        }
    """
    data = request.json
    filename = data.get('filename')
    recommendations = data.get('recommendations', [])
    selected = data.get('selected_indices', [])

    if not filename or not recommendations:
        return jsonify({'error': 'filename and recommendations required'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        output_path = engine.apply_and_export(
            filepath, recommendations, selected, app.config['OUTPUT_FOLDER']
        )
        return jsonify({
            'status': 'success',
            'output_file': os.path.basename(output_path),
            'download_url': f'/api/download/{os.path.basename(output_path)}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# TOOL 3: Generate Insights
# ============================================

@app.route('/api/tool3/insights', methods=['POST'])
def tool3_insights():
    """
    Tool 3: Generate visualizations for objective mappings

    Request:
        {
            "filename": "mapped_questions.xlsx"
        }

    Returns:
        {
            "charts": {...},
            "summary": {...}
        }
    """
    data = request.json
    filename = data.get('filename')

    if not filename:
        return jsonify({'error': 'filename required'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Get insights data
        insights_data = engine.get_insights_data(filepath)

        # Generate charts
        charts = viz_engine.generate_all_charts(insights_data)

        # Build chart URLs
        chart_urls = {}
        for name, path in charts.items():
            chart_urls[name] = f'/api/insights/{os.path.basename(path)}'

        # Summary stats
        coverage = insights_data['coverage']
        confidence = insights_data['confidence_scores']
        total = sum(coverage.values())
        avg_conf = sum(confidence) / len(confidence) if confidence else 0

        return jsonify({
            'status': 'success',
            'charts': chart_urls,
            'summary': {
                'total_questions': total,
                'objectives_covered': len([o for o, c in coverage.items() if c > 0]),
                'total_objectives': 6,
                'average_confidence': round(avg_conf, 3),
                'gaps': insights_data['gaps'],
                'coverage': coverage
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/<filename>', methods=['GET'])
def get_insight_image(filename):
    """Serve insight chart images"""
    filepath = os.path.join(app.config['INSIGHTS_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    return jsonify({'error': 'Chart not found'}), 404


# ============================================
# Download
# ============================================

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download exported Excel file"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  OBJECTIVES MAPPING SYSTEM")
    print("  Learning Objectives (O1-O6)")
    print("="*50)
    print("\n  API: http://localhost:5001")
    print("  UI:  http://localhost:8001")
    print("\n  Tools:")
    print("  1. Map unmapped questions")
    print("  2. Rate existing mappings")
    print("  3. Generate insights")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)

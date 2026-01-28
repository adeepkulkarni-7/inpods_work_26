"""
Inpods Audit Engine V2 - Flask Backend
Curriculum mapping analysis and improvement system

V2 Changes:
- Combined save & download functionality
- Full question text preservation
- Tool-ready API design for future agent integration
- Runs on port 5001 (parallel to V1 on 5000)

API Functions designed as discrete tools for future agent integration.
Each endpoint is a self-contained operation with clear inputs/outputs.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

from audit_engine import AuditEngine, LibraryManager
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

# Initialize engines
print("[*] Initializing Inpods Audit Engine V2...")

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

# Initialize other engines
viz_engine = VisualizationEngine(output_folder=INSIGHTS_FOLDER)
library_manager = LibraryManager(library_folder=LIBRARY_FOLDER)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# COMMON ENDPOINTS
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Tool: check_health
    Description: Verify service status and Azure connection
    Inputs: None
    Outputs: {status, service, version, azure_connected}
    """
    return jsonify({
        'status': 'ok',
        'service': 'Inpods Audit Engine V2',
        'version': '2.0.0',
        'azure_connected': audit_engine is not None
    })


# ============================================
# MODE A: Map Unmapped Questions
# ============================================

def extract_reference_metadata(file_path):
    """
    Extract curriculum metadata from a reference file.
    Returns competencies, objectives, skills, and topics found in the file.
    V2.1: Fixed to skip type column and get actual description.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
        else:
            df = pd.read_excel(file_path, header=None, engine='openpyxl')

        metadata = {
            'competencies': [],
            'objectives': [],
            'skills': [],
            'topics': [],
            'nmc_competencies': [],
            'raw_columns': [],
            'detected_type': None
        }

        # Try to detect the file type and extract data
        # Check all cells for curriculum codes
        for row_idx, row in df.iterrows():
            for col_idx, cell in enumerate(row):
                if pd.isna(cell):
                    continue
                cell_str = str(cell).strip()

                # NMC Competency codes (MI1.1, MI1.2, etc.)
                if len(cell_str) >= 4 and cell_str[:2] == 'MI' and '.' in cell_str:
                    # Get description from next column if available
                    desc = ''
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        desc = str(row.iloc[col_idx + 1]).strip()
                    metadata['nmc_competencies'].append({
                        'id': cell_str,
                        'description': desc
                    })
                    metadata['detected_type'] = 'nmc_competency'

                # Competency codes (C1, C2, etc.)
                elif len(cell_str) == 2 and cell_str[0] == 'C' and cell_str[1].isdigit():
                    desc = ''
                    # Check col+1, but skip if it's just a type label
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        next_val = str(row.iloc[col_idx + 1]).strip().lower()
                        if next_val in ['competency', 'objective', 'skill', 'type']:
                            # Skip type column, use col+2 for description
                            if col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                                desc = str(row.iloc[col_idx + 2]).strip()
                        else:
                            desc = str(row.iloc[col_idx + 1]).strip()
                    elif col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                        desc = str(row.iloc[col_idx + 2]).strip()
                    metadata['competencies'].append({
                        'id': cell_str,
                        'description': desc
                    })
                    if not metadata['detected_type']:
                        metadata['detected_type'] = 'competency'

                # Objective codes (O1, O2, etc.)
                elif len(cell_str) == 2 and cell_str[0] == 'O' and cell_str[1].isdigit():
                    desc = ''
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        next_val = str(row.iloc[col_idx + 1]).strip().lower()
                        if next_val in ['competency', 'objective', 'skill', 'type']:
                            if col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                                desc = str(row.iloc[col_idx + 2]).strip()
                        else:
                            desc = str(row.iloc[col_idx + 1]).strip()
                    elif col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                        desc = str(row.iloc[col_idx + 2]).strip()
                    metadata['objectives'].append({
                        'id': cell_str,
                        'description': desc
                    })
                    if not metadata['detected_type']:
                        metadata['detected_type'] = 'objective'

                # Skill codes (S1, S2, etc.)
                elif len(cell_str) == 2 and cell_str[0] == 'S' and cell_str[1].isdigit():
                    desc = ''
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        next_val = str(row.iloc[col_idx + 1]).strip().lower()
                        if next_val in ['competency', 'objective', 'skill', 'type']:
                            if col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                                desc = str(row.iloc[col_idx + 2]).strip()
                        else:
                            desc = str(row.iloc[col_idx + 1]).strip()
                    elif col_idx + 2 < len(row) and pd.notna(row.iloc[col_idx + 2]):
                        desc = str(row.iloc[col_idx + 2]).strip()
                    metadata['skills'].append({
                        'id': cell_str,
                        'description': desc
                    })
                    if not metadata['detected_type']:
                        metadata['detected_type'] = 'skill'

        # Check for Topic Area format
        if df.shape[1] >= 2:
            # Look for "Topic Area" header
            for row_idx in range(min(5, len(df))):
                for col_idx in range(len(df.columns)):
                    cell = df.iloc[row_idx, col_idx]
                    if pd.notna(cell) and 'topic' in str(cell).lower():
                        # Found topic header, extract topics from subsequent rows
                        for data_row in range(row_idx + 1, len(df)):
                            topic = df.iloc[data_row, col_idx] if col_idx < len(df.columns) else None
                            subtopics = df.iloc[data_row, col_idx + 1] if col_idx + 1 < len(df.columns) else None
                            if pd.notna(topic) and str(topic).strip():
                                metadata['topics'].append({
                                    'topic': str(topic).strip(),
                                    'subtopics': str(subtopics).strip() if pd.notna(subtopics) else ''
                                })
                        if metadata['topics']:
                            metadata['detected_type'] = 'area_topics'
                        break

        return metadata
    except Exception as e:
        return {'error': str(e)}


def extract_question_metadata(file_path):
    """
    Extract metadata from a question file.
    Returns course info, question count, and sample questions.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine='openpyxl')

        metadata = {
            'total_questions': len(df),
            'columns': list(df.columns),
            'sample_questions': []
        }

        # Find question text column
        question_col = None
        for col in df.columns:
            if 'question' in col.lower() and 'text' in col.lower():
                question_col = col
                break
            elif 'question' in col.lower():
                question_col = col

        # Get sample questions
        if question_col:
            for idx, row in df.head(5).iterrows():
                q_text = str(row[question_col])[:200] if pd.notna(row[question_col]) else ''
                q_num = row.get('Question Number', row.get('Q#', idx + 1))
                metadata['sample_questions'].append({
                    'number': str(q_num),
                    'text': q_text + ('...' if len(str(row.get(question_col, ''))) > 200 else '')
                })

        return metadata
    except Exception as e:
        return {'error': str(e)}


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Tool: upload_question_files
    Description: Upload question bank and reference curriculum files
    Inputs: question_file (file), reference_file (file)
    Outputs: {status, question_file, reference_file, question_count, reference_count, question_metadata, reference_metadata}
    """
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

        # Extract metadata
        question_metadata = extract_question_metadata(question_path)
        reference_metadata = extract_reference_metadata(reference_path)

        return jsonify({
            'status': 'success',
            'question_file': question_filename,
            'reference_file': reference_filename,
            'question_count': len(question_df),
            'reference_count': len(reference_df),
            'question_metadata': question_metadata,
            'reference_metadata': reference_metadata
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run-audit', methods=['POST'])
def run_audit():
    """
    Tool: run_mapping_audit
    Description: Map questions to curriculum topics (single-question mode)
    Inputs: {question_file, reference_file, dimension}
    Outputs: {recommendations, coverage, gaps, dimension, total_questions, mapped_questions}
    """
    try:
        data = request.json
        question_file = data.get('question_file')
        reference_file = data.get('reference_file')
        dimension = data.get('dimension')

        if not all([question_file, reference_file, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)

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
    """
    Tool: run_mapping_audit_batched
    Description: Map questions to curriculum topics (batched mode, 60-70% cost savings)
    Inputs: {question_file, reference_file, dimension, batch_size}
    Outputs: {recommendations, coverage, gaps, dimension, total_questions, mapped_questions, batch_mode, batch_size}
    """
    try:
        data = request.json
        question_file = data.get('question_file')
        reference_file = data.get('reference_file')
        dimension = data.get('dimension')
        batch_size = data.get('batch_size', 5)

        if not all([question_file, reference_file, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        batch_size = max(1, min(10, int(batch_size)))

        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)
        reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)

        result = audit_engine.run_audit_batched(
            question_csv=question_path,
            reference_csv=reference_path,
            dimension=dimension,
            batch_size=batch_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/apply-and-save', methods=['POST'])
def apply_and_save():
    """
    Tool: apply_mappings_and_save
    Description: Apply selected mappings, save to library, AND generate downloadable Excel
    Inputs: {question_file, recommendations, selected_indices, dimension, name}
    Outputs: {status, library_id, library_name, output_file, download_url}

    V2 Change: Combined save + download in single operation
    """
    try:
        data = request.json
        question_file = data.get('question_file')
        recommendations = data.get('recommendations')
        selected_indices = data.get('selected_indices')
        dimension = data.get('dimension')
        name = data.get('name', f'Mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        if not all([question_file, recommendations, selected_indices is not None, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)

        # 1. Apply changes and generate Excel
        output_path = audit_engine.apply_and_export(
            question_csv=question_path,
            recommendations=recommendations,
            selected_indices=selected_indices,
            dimension=dimension,
            output_folder=app.config['OUTPUT_FOLDER']
        )

        # 2. Save to library (only selected recommendations)
        selected_recommendations = [recommendations[i] for i in selected_indices if i < len(recommendations)]

        library_result = library_manager.save_mapping(
            name=name,
            recommendations=selected_recommendations,
            dimension=dimension,
            mode='A',
            source_file=question_file
        )

        return jsonify({
            'status': 'success',
            'library_id': library_result['id'],
            'library_name': library_result['name'],
            'output_file': os.path.basename(output_path),
            'download_url': f'/api/download/{os.path.basename(output_path)}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Keep legacy endpoint for backward compatibility
@app.route('/api/apply-changes', methods=['POST'])
def apply_changes():
    """
    Tool: apply_mappings (legacy)
    Description: Apply selected recommendations and export Excel (without auto-save)
    """
    try:
        data = request.json
        question_file = data.get('question_file')
        recommendations = data.get('recommendations')
        selected_indices = data.get('selected_indices')
        dimension = data.get('dimension')

        if not all([question_file, recommendations, selected_indices is not None, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file)

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
            'download_url': f'/api/download/{os.path.basename(output_path)}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Tool: download_file
    Description: Download generated Excel file
    Inputs: filename (path parameter)
    Outputs: Binary file download
    """
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
    """
    Tool: upload_mapped_file
    Description: Upload a file with existing mappings (for Mode B and C)
    Inputs: mapped_file (file), reference_file (file, optional)
    Outputs: {status, mapped_file, question_count, columns, reference_file, reference_count, mapped_metadata, reference_metadata}
    """
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

        # Extract metadata from mapped file
        mapped_metadata = extract_question_metadata(mapped_path)

        response = {
            'status': 'success',
            'mapped_file': mapped_filename,
            'question_count': len(mapped_df),
            'columns': mapped_df.columns.tolist(),
            'mapped_metadata': mapped_metadata
        }

        # Save reference file if provided
        if reference_file and reference_file.filename != '':
            reference_filename = secure_filename(reference_file.filename)
            reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_filename)
            reference_file.save(reference_path)
            reference_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
            response['reference_file'] = reference_filename
            response['reference_count'] = len(reference_df)
            response['reference_metadata'] = extract_reference_metadata(reference_path)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rate-mappings', methods=['POST'])
def rate_mappings():
    """
    Tool: rate_existing_mappings
    Description: Rate existing mappings and suggest alternatives (Mode B)
    Inputs: {mapped_file, reference_file, dimension, batch_size}
    Outputs: {ratings, summary, recommendations, dimension, total_questions}
    """
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

        result = audit_engine.rate_existing_mappings(
            mapped_file=mapped_path,
            reference_csv=reference_path,
            dimension=dimension,
            batch_size=batch_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/apply-corrections-and-save', methods=['POST'])
def apply_corrections_and_save():
    """
    Tool: apply_corrections_and_save
    Description: Apply selected corrections, save to library, AND generate downloadable Excel
    Inputs: {mapped_file, recommendations, selected_indices, dimension, name}
    Outputs: {status, library_id, library_name, output_file, download_url}

    V2 Change: Combined save + download for Mode B
    """
    try:
        data = request.json
        mapped_file = data.get('mapped_file')
        recommendations = data.get('recommendations')
        selected_indices = data.get('selected_indices')
        dimension = data.get('dimension')
        name = data.get('name', f'Corrections_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        if not all([mapped_file, recommendations, selected_indices is not None, dimension]):
            return jsonify({'error': 'Missing required parameters'}), 400

        mapped_path = os.path.join(app.config['UPLOAD_FOLDER'], mapped_file)

        # 1. Apply corrections and generate Excel
        output_path = audit_engine.apply_and_export(
            question_csv=mapped_path,
            recommendations=recommendations,
            selected_indices=selected_indices,
            dimension=dimension,
            output_folder=app.config['OUTPUT_FOLDER']
        )

        # 2. Save to library (only selected corrections)
        selected_recommendations = [recommendations[i] for i in selected_indices if i < len(recommendations)]

        library_result = library_manager.save_mapping(
            name=name,
            recommendations=selected_recommendations,
            dimension=dimension,
            mode='B',
            source_file=mapped_file
        )

        return jsonify({
            'status': 'success',
            'library_id': library_result['id'],
            'library_name': library_result['name'],
            'output_file': os.path.basename(output_path),
            'download_url': f'/api/download/{os.path.basename(output_path)}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MODE C: Generate Insights & Visualizations
# ============================================

@app.route('/api/generate-insights', methods=['POST'])
def generate_insights():
    """
    Tool: generate_insight_charts
    Description: Generate visualization charts from mapping data (Mode C)
    Inputs: {mapped_file, reference_file (optional)}
    Outputs: {status, charts, summary}
    """
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
            # Check multiple possible column names for mappings
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

        # Get reference topics and definitions
        reference_topics = list(coverage.keys())
        reference_definitions = {}
        if reference_file:
            reference_path = os.path.join(app.config['UPLOAD_FOLDER'], reference_file)
            if os.path.exists(reference_path):
                ref_metadata = extract_reference_metadata(reference_path)
                # Build definitions from metadata
                for item in ref_metadata.get('competencies', []):
                    reference_definitions[item['id']] = item['description']
                for item in ref_metadata.get('objectives', []):
                    reference_definitions[item['id']] = item['description']
                for item in ref_metadata.get('skills', []):
                    reference_definitions[item['id']] = item['description']
                for item in ref_metadata.get('nmc_competencies', []):
                    reference_definitions[item['id']] = item['description']
                for item in ref_metadata.get('topics', []):
                    reference_definitions[item['topic']] = item.get('subtopics', '')
                    reference_topics.append(item['topic'])

                # Also check for standard columns
                ref_df = pd.read_csv(reference_path) if reference_path.endswith('.csv') else pd.read_excel(reference_path)
                if 'Topic Area (CBME)' in ref_df.columns:
                    reference_topics = ref_df['Topic Area (CBME)'].dropna().tolist()
                elif 'Topic Area' in ref_df.columns:
                    reference_topics = ref_df['Topic Area'].dropna().tolist()

        # Generate all charts (including coverage_table)
        charts = viz_engine.generate_all_insights(mapping_data, reference_topics, reference_definitions)

        # Separate coverage_table from charts (it's data, not a file path)
        coverage_table = charts.pop('coverage_table', [])

        # Return chart URLs
        chart_urls = {}
        for chart_name, filepath in charts.items():
            filename = os.path.basename(filepath)
            chart_urls[chart_name] = f'/api/insights/{filename}'

        return jsonify({
            'status': 'success',
            'charts': chart_urls,
            'coverage_table': coverage_table,
            'summary': {
                'total_questions': len(recommendations),
                'topics_covered': len(coverage),
                'average_confidence': sum(r['confidence'] for r in recommendations) / len(recommendations) if recommendations else 0,
                'coverage': coverage  # Include coverage data for summary table
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/<filename>', methods=['GET'])
def download_insight(filename):
    """
    Tool: get_insight_chart
    Description: Download insight chart image
    Inputs: filename (path parameter)
    Outputs: PNG image
    """
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
    Tool: list_saved_mappings
    Description: List all saved mapping sets in the library
    Inputs: None
    Outputs: {status, mappings, total}
    """
    try:
        mappings = library_manager.list_mappings()

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
    Tool: save_mapping_to_library
    Description: Save current mapping results to library
    Inputs: {name, recommendations, dimension, mode, source_file}
    Outputs: {status, id, name, message}
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

        result = library_manager.save_mapping(
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


@app.route('/api/library/<mapping_id>', methods=['GET'])
def load_from_library(mapping_id):
    """
    Tool: get_library_mapping
    Description: Load a specific mapping set from library
    Inputs: mapping_id (path parameter)
    Outputs: {status, mapping}
    """
    try:
        data = library_manager.get_mapping(mapping_id)

        if not data:
            return jsonify({'error': 'Mapping not found'}), 404

        return jsonify({
            'status': 'success',
            'mapping': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/<mapping_id>', methods=['DELETE'])
def delete_from_library(mapping_id):
    """
    Tool: delete_library_mapping
    Description: Delete a mapping set from library
    Inputs: mapping_id (path parameter)
    Outputs: {status, message}
    """
    try:
        success = library_manager.delete_mapping(mapping_id)

        if not success:
            return jsonify({'error': 'Mapping not found'}), 404

        return jsonify({
            'status': 'success',
            'message': f'Deleted mapping {mapping_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/library/<mapping_id>/export', methods=['GET'])
def export_from_library(mapping_id):
    """
    Tool: export_library_mapping
    Description: Export a saved mapping to Excel
    Inputs: mapping_id (path parameter)
    Outputs: {status, download_url}
    """
    try:
        output_path = library_manager.export_to_excel(
            mapping_id=mapping_id,
            output_folder=app.config['OUTPUT_FOLDER']
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
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Inpods Audit Engine V2")
    print("="*50)
    print("[*] Backend running on http://localhost:5001")
    print("[*] Open http://localhost:8001 in your browser")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)

"""
Web Chat Interface for the AI Agent

A Flask-based web interface providing a chat UI for the curriculum mapping agent.
"""

import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .config import get_agent_config
from .orchestrator import AgentOrchestrator

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configuration
config = get_agent_config()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = config.upload_folder
app.config['OUTPUT_FOLDER'] = config.output_folder

# Ensure folders exist
os.makedirs(config.upload_folder, exist_ok=True)
os.makedirs(config.output_folder, exist_ok=True)
os.makedirs(config.insights_folder, exist_ok=True)

# Initialize agent
agent = None


def get_agent():
    """Get or create the agent instance"""
    global agent
    if agent is None:
        agent = AgentOrchestrator(config)
    return agent


def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/')
def index():
    """Serve the chat interface"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat message"""
    try:
        data = request.json
        message = data.get('message', '')
        files = data.get('files', [])

        agent = get_agent()
        response = run_async(agent.process_message(message, files))

        return jsonify({
            'success': True,
            'message': response.message,
            'options': response.options,
            'charts': response.charts,
            'download_url': response.download_url,
            'input_type': response.input_type,
            'state': response.state,
            'metadata': response.metadata
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        file_type = request.form.get('type', 'question')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(config.upload_folder, filename)
        file.save(file_path)

        # Process with agent
        agent = get_agent()
        files = [{
            'filename': filename,
            'path': file_path,
            'type': file_type
        }]

        response = run_async(agent.process_message(f"Uploaded {filename}", files))

        return jsonify({
            'success': True,
            'filename': filename,
            'path': file_path,
            'message': response.message,
            'state': response.state
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a generated file"""
    try:
        file_path = os.path.join(config.output_folder, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights/<filename>')
def get_insight(filename):
    """Get an insight chart image"""
    try:
        file_path = os.path.join(config.insights_folder, filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/png')
        return jsonify({'error': 'Chart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_agent():
    """Reset the agent state"""
    global agent
    agent = AgentOrchestrator(config)
    return jsonify({
        'success': True,
        'message': 'Agent reset successfully'
    })


@app.route('/api/state')
def get_state():
    """Get current agent state"""
    agent = get_agent()
    return jsonify(agent.state.to_dict())


def run_server(host=None, port=None, debug=None):
    """Run the web server"""
    host = host or config.host
    port = port or config.port
    debug = debug if debug is not None else config.debug

    print(f"\n{'='*50}")
    print(f"Curriculum Mapping AI Agent")
    print(f"{'='*50}")
    print(f"[*] Web interface: http://localhost:{port}")
    print(f"[*] API endpoint: http://localhost:{port}/api/chat")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()

# Curriculum Mapping System - Integration Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Integration Options](#integration-options)
6. [API Reference](#api-reference)
7. [Frontend Integration](#frontend-integration)
8. [Authentication](#authentication)
9. [Database Integration](#database-integration)
10. [Deployment](#deployment)
11. [Examples](#examples)

---

## Overview

The Inpods Curriculum Mapping System is an AI-powered tool for mapping educational questions to curriculum frameworks. It uses Azure OpenAI (GPT-4) to analyze questions and match them to appropriate competencies, objectives, or topic areas.

### Key Features

- **AI-Powered Mapping**: Automatically maps questions to curriculum elements
- **Batch Processing**: Efficient token usage with 60-70% cost savings
- **Multiple Dimensions**: Supports NMC Competency, Area Topics, Objectives, Skills
- **Rating Mode**: Evaluate and improve existing mappings
- **Visualization**: Generate insight charts and dashboards
- **Library Management**: Save, load, and export mapping sets

### Supported Dimensions

| Dimension | ID Format | Example | Description |
|-----------|-----------|---------|-------------|
| `nmc_competency` | MI1.1 - MI15.x | MI1.1, MI2.3 | NMC Medical Education Competencies |
| `area_topics` | Topic / Subtopic | Bacteriology / Gram Positive | Topic areas with subtopics |
| `competency` | C1 - C9 | C1, C5 | Generic competencies |
| `objective` | O1 - O9 | O1, O6 | Learning objectives |
| `skill` | S1 - S5 | S1, S3 | Skills assessment |

---

## Architecture

### Package Structure

```
inpods-audit_cc/
├── integration/                    # INTEGRATION PACKAGE
│   ├── __init__.py                # Package exports
│   ├── app.py                     # Flask app factory (743 lines)
│   ├── engine.py                  # Core AI engine (700+ lines)
│   ├── visualization.py           # Chart generation (300+ lines)
│   ├── config.py                  # Configuration classes
│   ├── auth.py                    # Authentication middleware
│   ├── database.py                # SQLAlchemy models
│   ├── web_components/
│   │   ├── curriculum-mapper.js   # Embeddable web component
│   │   └── embed.html             # Demo page
│   └── README.md                  # Quick start guide
│
├── backend_v2/                    # ORIGINAL IMPLEMENTATION
│   ├── app.py                     # Flask API
│   ├── audit_engine.py            # Original engine
│   └── visualization_engine.py    # Original charts
│
├── frontend_v2/                   # ORIGINAL FRONTEND
│   └── index.html                 # Web UI
│
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Orchestration
├── requirements.txt               # Dependencies
├── .env.example                   # Config template
├── run_integration.py             # Python runner
└── run_integration.bat            # Windows runner
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR PLATFORM                                │
│  ┌─────────────────┐     ┌─────────────────┐     ┌───────────────┐ │
│  │   Your Frontend │     │  Your Backend   │     │  Your Database │ │
│  └────────┬────────┘     └────────┬────────┘     └───────────────┘ │
│           │                       │                                  │
└───────────┼───────────────────────┼──────────────────────────────────┘
            │                       │
            │    REST API Calls     │
            ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 CURRICULUM MAPPING MICROSERVICE                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      Flask API Layer                         │   │
│  │   /api/upload  /api/run-audit  /api/rate  /api/insights     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────┐  ┌────────┴────────┐  ┌───────────────────┐     │
│  │ Auth Module  │  │   Audit Engine  │  │  Visualization    │     │
│  │ JWT/API Key  │  │   (AI Logic)    │  │  Engine (Charts)  │     │
│  └──────────────┘  └────────┬────────┘  └───────────────────┘     │
│                             │                                       │
│                    ┌────────┴────────┐                             │
│                    │  Azure OpenAI   │                             │
│                    │    (GPT-4)      │                             │
│                    └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. UPLOAD
   User → Upload CSV/Excel → Save to /uploads → Return file metadata

2. MAP (Mode A)
   Files → Parse Questions → Batch (5 per call) → Azure OpenAI
        → Parse JSON Response → Build Recommendations → Return Results

3. RATE (Mode B)
   Pre-mapped File → Extract Existing Mappings → Batch Rate with AI
                  → Compare & Score → Return Ratings + Suggestions

4. INSIGHTS (Mode C)
   Mapped Data → Calculate Coverage → Generate Charts (matplotlib)
             → Save PNGs → Return URLs

5. EXPORT
   Selected Recommendations → Apply to DataFrame → Export Excel → Download
```

---

## Installation

### Prerequisites

- Python 3.10+
- Azure OpenAI API access
- pip package manager

### Quick Install

```bash
# Clone or download the project
cd inpods-audit_cc

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run
python run_integration.py
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| flask | ≥3.0.0 | Web framework |
| flask-cors | ≥4.0.0 | CORS support |
| openai | ≥1.0.0 | Azure OpenAI client |
| pandas | ≥1.5.0 | Data processing |
| openpyxl | ≥3.0.0 | Excel file support |
| matplotlib | ≥3.5.0 | Chart generation |
| python-dotenv | ≥1.0.0 | Configuration |
| PyJWT | ≥2.0.0 | JWT authentication (optional) |
| SQLAlchemy | ≥2.0.0 | Database ORM (optional) |

---

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# REQUIRED: Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Service
HOST=0.0.0.0
PORT=5001
DEBUG=false

# Storage
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_FILE_SIZE_MB=16

# Authentication (optional)
AUTH_ENABLED=false
AUTH_PROVIDER=jwt
AUTH_SECRET_KEY=your-secret-key

# Database (optional)
DATABASE_ENABLED=false
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Configuration Classes (Python)

```python
from integration.config import Config, get_config, from_dict

# Load from .env
config = get_config()

# Or create programmatically
config = from_dict({
    'azure': {
        'api_key': 'your-key',
        'endpoint': 'https://your-resource.openai.azure.com/'
    },
    'auth': {
        'enabled': True,
        'provider': 'jwt',
        'secret_key': 'your-secret'
    }
})
```

---

## Integration Options

### Option 1: Microservice (Recommended)

Deploy as a standalone service that your platform calls via REST API.

**Pros:**
- Minimal changes to existing platform
- Independent scaling
- Easy updates
- Clear separation of concerns

**Setup:**
```bash
# Start the microservice
python run_integration.py --port 5001

# Or with Docker
docker-compose up -d
```

**Call from your platform:**
```python
import requests

# Upload files
files = {
    'question_file': open('questions.csv', 'rb'),
    'reference_file': open('curriculum.csv', 'rb')
}
response = requests.post('http://localhost:5001/api/upload', files=files)

# Run mapping
result = requests.post('http://localhost:5001/api/run-audit-efficient', json={
    'question_file': 'questions.csv',
    'reference_file': 'curriculum.csv',
    'dimension': 'nmc_competency',
    'batch_size': 5
}).json()
```

### Option 2: Direct Library Import

Import the Python modules directly into your existing backend.

**Pros:**
- No additional infrastructure
- Lower latency
- Single deployment

**Setup:**
```python
from integration import AuditEngine, LibraryManager, VisualizationEngine

# Initialize
config = {
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
    'api_version': '2024-02-15-preview',
    'deployment': 'gpt-4'
}

engine = AuditEngine(config)

# Use in your routes
@app.route('/your-platform/map-curriculum', methods=['POST'])
def map_curriculum():
    result = engine.run_audit_batched(
        question_csv=request.files['questions'],
        reference_csv=request.files['reference'],
        dimension=request.form['dimension'],
        batch_size=5
    )
    return jsonify(result)
```

### Option 3: Flask Blueprint

Register the curriculum mapping endpoints on your existing Flask app.

```python
from flask import Flask
from integration.app import register_blueprint
from integration.config import get_config

app = Flask(__name__)
config = get_config()
register_blueprint(app, config)

# Now your app has all /api/... curriculum endpoints
```

### Option 4: Docker Container

```bash
# Build
docker build -t curriculum-mapping:latest .

# Run
docker run -p 5001:5001 --env-file .env curriculum-mapping:latest
```

---

## API Reference

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check |
| `/api/info` | GET | Service capabilities |

### Mode A: Map Unmapped Questions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload question + reference files |
| `/api/run-audit` | POST | Map questions (single mode) |
| `/api/run-audit-efficient` | POST | Map questions (batched - recommended) |
| `/api/apply-changes` | POST | Apply mappings & export Excel |
| `/api/download/{filename}` | GET | Download generated file |

### Mode B: Rate Existing Mappings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-mapped` | POST | Upload pre-mapped file |
| `/api/rate-mappings` | POST | Rate existing mappings |

### Mode C: Generate Insights

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-insights` | POST | Generate visualization charts |
| `/api/insights/{filename}` | GET | Download chart PNG |

### Library Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/library` | GET | List saved mappings |
| `/api/library/save` | POST | Save mapping set |
| `/api/library/{id}` | GET | Get specific mapping |
| `/api/library/{id}` | DELETE | Delete mapping |
| `/api/library/{id}/export` | GET | Export to Excel |

### Detailed Examples

#### Upload Files

```http
POST /api/upload
Content-Type: multipart/form-data

question_file: questions.csv
reference_file: curriculum.csv
```

**Response:**
```json
{
    "status": "success",
    "question_file": "questions.csv",
    "reference_file": "curriculum.csv",
    "question_count": 50,
    "reference_count": 15
}
```

#### Run Batched Mapping

```http
POST /api/run-audit-efficient
Content-Type: application/json

{
    "question_file": "questions.csv",
    "reference_file": "curriculum.csv",
    "dimension": "nmc_competency",
    "batch_size": 5
}
```

**Response:**
```json
{
    "recommendations": [
        {
            "question_num": "Q1",
            "question_text": "Which organism causes typhoid fever?",
            "recommended_mapping": "MI1.1",
            "mapped_id": "MI1.1",
            "confidence": 0.92,
            "justification": "Question tests knowledge of bacterial classification and pathogenesis..."
        }
    ],
    "coverage": {
        "MI1.1": 5,
        "MI2.3": 3,
        "MI3.1": 7
    },
    "gaps": ["MI4.2", "MI5.1"],
    "dimension": "nmc_competency",
    "total_questions": 50,
    "mapped_questions": 50,
    "batch_mode": true,
    "batch_size": 5
}
```

#### Rate Existing Mappings

```http
POST /api/rate-mappings
Content-Type: application/json

{
    "mapped_file": "existing_mappings.xlsx",
    "reference_file": "curriculum.csv",
    "dimension": "nmc_competency",
    "batch_size": 5
}
```

**Response:**
```json
{
    "ratings": [
        {
            "question_num": "Q1",
            "question_text": "...",
            "existing_mapping": {"id": "MI1.1"},
            "rating": "correct",
            "agreement_score": 0.95,
            "rating_justification": "Mapping accurately reflects...",
            "suggested_mapping": "MI1.1",
            "suggestion_confidence": 0.95
        }
    ],
    "summary": {
        "total_rated": 50,
        "correct": 30,
        "partially_correct": 15,
        "incorrect": 5,
        "accuracy_rate": 0.6,
        "average_agreement_score": 0.78
    },
    "recommendations": [...]
}
```

---

## Frontend Integration

### Web Component (Easiest)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Curriculum Mapping</title>
</head>
<body>
    <!-- Include the component script -->
    <script src="/path/to/curriculum-mapper.js"></script>

    <!-- Use the component -->
    <curriculum-mapper
        api-base="http://localhost:5001"
        dimension="nmc_competency"
        theme="light">
    </curriculum-mapper>
</body>
</html>
```

**Attributes:**
| Attribute | Required | Default | Description |
|-----------|----------|---------|-------------|
| `api-base` | Yes | - | Base URL of the API |
| `dimension` | No | `nmc_competency` | Default mapping dimension |
| `theme` | No | `light` | `light` or `dark` |
| `auth-token` | No | - | Bearer token for auth |

### iFrame Embed

```html
<iframe
    src="http://localhost:8001"
    width="100%"
    height="800px"
    frameborder="0"
    allow="clipboard-write">
</iframe>
```

### React Integration

```jsx
import { useEffect, useRef } from 'react';

function CurriculumMapper({ apiBase, dimension }) {
    const containerRef = useRef(null);

    useEffect(() => {
        // Load the web component script
        const script = document.createElement('script');
        script.src = '/curriculum-mapper.js';
        document.head.appendChild(script);

        script.onload = () => {
            const component = document.createElement('curriculum-mapper');
            component.setAttribute('api-base', apiBase);
            component.setAttribute('dimension', dimension);
            containerRef.current.appendChild(component);
        };

        return () => {
            script.remove();
        };
    }, [apiBase, dimension]);

    return <div ref={containerRef} />;
}

// Usage
<CurriculumMapper apiBase="http://localhost:5001" dimension="nmc_competency" />
```

### Vue Integration

```vue
<template>
    <curriculum-mapper
        :api-base="apiBase"
        :dimension="dimension"
        :theme="theme">
    </curriculum-mapper>
</template>

<script>
import '/path/to/curriculum-mapper.js';

export default {
    data() {
        return {
            apiBase: 'http://localhost:5001',
            dimension: 'nmc_competency',
            theme: 'light'
        };
    }
};
</script>
```

---

## Authentication

### Enable Authentication

```env
AUTH_ENABLED=true
AUTH_PROVIDER=jwt
AUTH_SECRET_KEY=your-super-secret-key-min-32-chars
```

### JWT Authentication

**Get Token:**
```http
POST /api/auth/token
Content-Type: application/json

{
    "user_id": "user-123",
    "email": "user@example.com",
    "permissions": ["curriculum_mapping"]
}
```

**Use Token:**
```http
GET /api/library
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### API Key Authentication

```env
AUTH_PROVIDER=api_key
AUTH_API_KEY_HEADER=X-API-Key
```

```http
GET /api/library
X-API-Key: your-api-key
```

### Custom Authentication

```python
from integration.auth import BaseAuthProvider, AuthMiddleware

class MyAuthProvider(BaseAuthProvider):
    def authenticate(self, request):
        # Your custom logic
        token = request.headers.get('X-My-Token')
        user = my_validate_function(token)
        return user  # Return user dict or None

# Use it
auth_config.provider = 'custom'
auth_middleware = AuthMiddleware(auth_config)
auth_middleware.provider = MyAuthProvider()
```

---

## Database Integration

### Enable Database

```env
DATABASE_ENABLED=true
DATABASE_URL=postgresql://user:pass@localhost:5432/curriculum_mapping
```

### Supported Databases

- PostgreSQL: `postgresql://user:pass@host:5432/db`
- MySQL: `mysql+pymysql://user:pass@host:3306/db`
- SQLite: `sqlite:///./curriculum_mapping.db`

### Database Schema

```sql
-- Mapping Sets (sessions)
CREATE TABLE curriculum_mapping_sets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    dimension VARCHAR(50) NOT NULL,
    mode VARCHAR(10) NOT NULL,
    source_file VARCHAR(255),
    question_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual Mappings
CREATE TABLE curriculum_mappings (
    id VARCHAR(36) PRIMARY KEY,
    mapping_set_id VARCHAR(36) REFERENCES curriculum_mapping_sets(id),
    question_number VARCHAR(50),
    question_text TEXT,
    mapped_id VARCHAR(50),
    mapped_topic VARCHAR(255),
    mapped_subtopic VARCHAR(255),
    confidence DECIMAL(3,2),
    justification TEXT,
    rating VARCHAR(20),
    agreement_score DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE curriculum_audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  curriculum-api:
    build: .
    ports:
      - "5001:5001"
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped
```

```bash
docker-compose up -d
```

### Production with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:5001 "integration.app:create_app()"
```

### Production with Nginx

```nginx
# nginx.conf
upstream curriculum_api {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name curriculum.yourplatform.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://curriculum_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: curriculum-mapping
spec:
  replicas: 2
  selector:
    matchLabels:
      app: curriculum-mapping
  template:
    metadata:
      labels:
        app: curriculum-mapping
    spec:
      containers:
      - name: api
        image: curriculum-mapping:latest
        ports:
        - containerPort: 5001
        env:
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: api-key
```

---

## Examples

### Complete Python Example

```python
from integration import AuditEngine, LibraryManager, VisualizationEngine

# 1. Initialize
config = {
    'api_key': 'your-key',
    'azure_endpoint': 'https://your-resource.openai.azure.com/',
    'api_version': '2024-02-15-preview',
    'deployment': 'gpt-4'
}

engine = AuditEngine(config)
library = LibraryManager('outputs/library')
viz = VisualizationEngine('outputs/insights')

# 2. Run mapping
result = engine.run_audit_batched(
    question_csv='questions.csv',
    reference_csv='curriculum.csv',
    dimension='nmc_competency',
    batch_size=5
)

print(f"Mapped {result['mapped_questions']} questions")
print(f"Coverage: {result['coverage']}")
print(f"Gaps: {result['gaps']}")

# 3. Save to library
saved = library.save_mapping(
    name='Microbiology Exam 2026',
    recommendations=result['recommendations'],
    dimension='nmc_competency',
    mode='A',
    source_file='questions.csv'
)
print(f"Saved as: {saved['id']}")

# 4. Generate visualizations
charts = viz.generate_all_insights(result, list(result['coverage'].keys()))
print(f"Charts: {charts}")

# 5. Export to Excel
output_path = engine.apply_and_export(
    question_csv='questions.csv',
    recommendations=result['recommendations'],
    selected_indices=list(range(len(result['recommendations']))),
    dimension='nmc_competency',
    output_folder='outputs'
)
print(f"Exported: {output_path}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:5001/api/health

# Upload files
curl -X POST http://localhost:5001/api/upload \
    -F "question_file=@questions.csv" \
    -F "reference_file=@curriculum.csv"

# Run mapping
curl -X POST http://localhost:5001/api/run-audit-efficient \
    -H "Content-Type: application/json" \
    -d '{
        "question_file": "questions.csv",
        "reference_file": "curriculum.csv",
        "dimension": "nmc_competency",
        "batch_size": 5
    }'

# List library
curl http://localhost:5001/api/library

# With authentication
curl http://localhost:5001/api/library \
    -H "Authorization: Bearer your-jwt-token"
```

### JavaScript/Fetch Example

```javascript
async function runCurriculumMapping() {
    const API_BASE = 'http://localhost:5001';

    // 1. Upload files
    const formData = new FormData();
    formData.append('question_file', document.getElementById('questions').files[0]);
    formData.append('reference_file', document.getElementById('reference').files[0]);

    const uploadRes = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
    });
    const uploadData = await uploadRes.json();

    // 2. Run mapping
    const mapRes = await fetch(`${API_BASE}/api/run-audit-efficient`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_file: uploadData.question_file,
            reference_file: uploadData.reference_file,
            dimension: 'nmc_competency',
            batch_size: 5
        })
    });
    const mapData = await mapRes.json();

    console.log('Recommendations:', mapData.recommendations);
    console.log('Coverage:', mapData.coverage);
    console.log('Gaps:', mapData.gaps);

    // 3. Apply and download
    const highConfidence = mapData.recommendations
        .map((r, i) => r.confidence >= 0.85 ? i : -1)
        .filter(i => i >= 0);

    const applyRes = await fetch(`${API_BASE}/api/apply-changes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_file: uploadData.question_file,
            recommendations: mapData.recommendations,
            selected_indices: highConfidence,
            dimension: 'nmc_competency'
        })
    });
    const applyData = await applyRes.json();

    // Download file
    window.open(`${API_BASE}${applyData.download_url}`);
}
```

---

## Troubleshooting

### Common Issues

**"Failed to connect to Azure OpenAI"**
- Verify API key and endpoint in `.env`
- Check network connectivity
- Ensure deployment name is correct

**"File upload failed"**
- Check file size (max 16MB default)
- Verify file extension (.csv, .xlsx, .xls, .ods)
- Ensure required columns exist

**"Rate limit exceeded"**
- Reduce batch_size
- Add delays between requests
- Check Azure OpenAI quota

**"CORS error"**
- Set `CORS_ORIGINS` in config
- Ensure API is running

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Support

- **Documentation**: This file + `integration/README.md`
- **Examples**: `integration/web_components/embed.html`
- **Issues**: GitHub Issues

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01 | Integration package, auth, database, web components |
| 1.0.0 | 2026-01 | Initial release with basic API |

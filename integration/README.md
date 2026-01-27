# Curriculum Mapping System - Integration Guide

This package provides everything needed to integrate the Inpods Curriculum Mapping System into an existing platform.

## Quick Start

### Option 1: Standalone Microservice (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# 3. Run the service
python -m integration.app
```

The API will be available at `http://localhost:5001`

### Option 2: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f curriculum-api

# Stop
docker-compose down
```

### Option 3: Direct Library Integration

```python
from integration import AuditEngine, LibraryManager

# Configure
config = {
    'api_key': 'your-azure-openai-key',
    'azure_endpoint': 'https://your-resource.openai.azure.com/',
    'api_version': '2024-02-15-preview',
    'deployment': 'gpt-4'
}

# Initialize engine
engine = AuditEngine(config)

# Map questions to curriculum
result = engine.run_audit_batched(
    question_csv='questions.csv',
    reference_csv='curriculum.csv',
    dimension='nmc_competency',
    batch_size=5
)

print(f"Mapped {result['mapped_questions']} questions")
print(f"Coverage: {result['coverage']}")
print(f"Gaps: {result['gaps']}")
```

---

## API Reference

### Health Check

```
GET /api/health
```

Response:
```json
{
    "status": "ok",
    "service": "Curriculum Mapping Service",
    "version": "2.0.0",
    "azure_connected": true
}
```

### Mode A: Map Unmapped Questions

#### Upload Files

```
POST /api/upload
Content-Type: multipart/form-data

question_file: <file>
reference_file: <file>
```

Response:
```json
{
    "status": "success",
    "question_file": "questions.csv",
    "reference_file": "curriculum.csv",
    "question_count": 50,
    "reference_count": 15
}
```

#### Run Mapping (Batched - Recommended)

```
POST /api/run-audit-efficient
Content-Type: application/json

{
    "question_file": "questions.csv",
    "reference_file": "curriculum.csv",
    "dimension": "nmc_competency",
    "batch_size": 5
}
```

Response:
```json
{
    "recommendations": [
        {
            "question_num": "Q1",
            "question_text": "What is the causative agent...",
            "recommended_mapping": "MI1.1",
            "confidence": 0.92,
            "justification": "Question tests knowledge of microbial classification..."
        }
    ],
    "coverage": {"MI1.1": 5, "MI2.3": 3},
    "gaps": ["MI4.2", "MI5.1"],
    "dimension": "nmc_competency",
    "total_questions": 50,
    "mapped_questions": 50
}
```

#### Apply Changes & Download

```
POST /api/apply-changes
Content-Type: application/json

{
    "question_file": "questions.csv",
    "recommendations": [...],
    "selected_indices": [0, 1, 2, 5, 7],
    "dimension": "nmc_competency"
}
```

Response:
```json
{
    "status": "success",
    "output_file": "audit_output_nmc_competency_20260127_120000.xlsx",
    "download_url": "/api/download/audit_output_nmc_competency_20260127_120000.xlsx"
}
```

### Mode B: Rate Existing Mappings

```
POST /api/rate-mappings
Content-Type: application/json

{
    "mapped_file": "existing_mappings.xlsx",
    "reference_file": "curriculum.csv",
    "dimension": "nmc_competency",
    "batch_size": 5
}
```

Response:
```json
{
    "ratings": [...],
    "summary": {
        "total_rated": 50,
        "correct": 30,
        "partially_correct": 15,
        "incorrect": 5,
        "accuracy_rate": 0.6
    },
    "recommendations": [...]
}
```

### Mode C: Generate Insights

```
POST /api/generate-insights
Content-Type: application/json

{
    "mapped_file": "mappings.xlsx"
}
```

Response:
```json
{
    "status": "success",
    "charts": {
        "topic_bar_chart": "/api/insights/topic_bar_chart_20260127_120000.png",
        "topic_pie_chart": "/api/insights/topic_pie_chart_20260127_120000.png",
        "confidence_histogram": "/api/insights/confidence_histogram_20260127_120000.png",
        "gap_analysis": "/api/insights/gap_analysis_20260127_120000.png",
        "summary_dashboard": "/api/insights/summary_dashboard_20260127_120000.png"
    },
    "summary": {
        "total_questions": 50,
        "topics_covered": 12,
        "average_confidence": 0.87
    }
}
```

### Library Management

```
GET /api/library                    # List saved mappings
POST /api/library/save              # Save mapping set
GET /api/library/{id}               # Get specific mapping
DELETE /api/library/{id}            # Delete mapping
GET /api/library/{id}/export        # Export to Excel
```

---

## Frontend Integration

### Option A: Web Component (Easiest)

```html
<!-- Include the script -->
<script src="integration/web_components/curriculum-mapper.js"></script>

<!-- Use the component -->
<curriculum-mapper
    api-base="https://api.yourplatform.com"
    dimension="nmc_competency"
    theme="light">
</curriculum-mapper>
```

### Option B: iFrame Embed

```html
<iframe
    src="https://curriculum-mapping.yourplatform.com/"
    width="100%"
    height="800px"
    frameborder="0">
</iframe>
```

### Option C: Custom Integration

```javascript
// JavaScript API client example
async function mapQuestions(questionFile, referenceFile, dimension) {
    const formData = new FormData();
    formData.append('question_file', questionFile);
    formData.append('reference_file', referenceFile);

    // Upload files
    const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    const uploadData = await uploadRes.json();

    // Run mapping
    const mapRes = await fetch('/api/run-audit-efficient', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_file: uploadData.question_file,
            reference_file: uploadData.reference_file,
            dimension: dimension,
            batch_size: 5
        })
    });

    return await mapRes.json();
}
```

---

## Authentication

Enable authentication by setting in `.env`:

```
AUTH_ENABLED=true
AUTH_PROVIDER=jwt
AUTH_SECRET_KEY=your-secure-secret-key
```

### Using JWT Tokens

```bash
# Get token (for testing)
curl -X POST http://localhost:5001/api/auth/token \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user123", "email": "user@example.com"}'

# Use token in requests
curl http://localhost:5001/api/library \
    -H "Authorization: Bearer <your-token>"
```

### Using API Keys

```
AUTH_PROVIDER=api_key
AUTH_API_KEY_HEADER=X-API-Key
```

```bash
curl http://localhost:5001/api/library \
    -H "X-API-Key: your-api-key"
```

---

## Database Integration

Enable database storage:

```
DATABASE_ENABLED=true
DATABASE_URL=postgresql://user:pass@localhost/curriculum_mapping
```

Tables created:
- `curriculum_mapping_sets` - Mapping sessions
- `curriculum_mappings` - Individual question mappings
- `curriculum_audit_logs` - Security audit trail

---

## Supported Dimensions

| Dimension | ID Format | Description |
|-----------|-----------|-------------|
| `nmc_competency` | MI1.1-MI15.x | NMC Medical Education Competencies |
| `area_topics` | Topic / Subtopic | Topic areas with subtopics |
| `competency` | C1-C9 | Generic competencies |
| `objective` | O1-O9 | Learning objectives |
| `skill` | S1-S5 | Skills assessment |

---

## File Structure

```
integration/
├── __init__.py          # Package exports
├── app.py               # Flask app factory
├── engine.py            # Core AI mapping engine
├── visualization.py     # Chart generation
├── config.py            # Configuration management
├── auth.py              # Authentication middleware
├── database.py          # Database models
├── web_components/
│   ├── curriculum-mapper.js    # Web component
│   └── embed.html              # Demo page
└── README.md            # This file

Dockerfile               # Container image
docker-compose.yml       # Orchestration
.env.example             # Configuration template
requirements.txt         # Python dependencies
```

---

## Troubleshooting

### Connection Issues

```
[ERROR] Failed to connect to Azure OpenAI
```

- Verify `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` are correct
- Check network connectivity to Azure
- Ensure deployment name matches your Azure configuration

### File Upload Errors

- Check file size is under `MAX_FILE_SIZE_MB` (default: 16MB)
- Ensure file extension is `.csv`, `.xlsx`, `.xls`, or `.ods`
- Verify file has required columns: `Question Number`, `Question Text`

### Rate Limiting

If you see 429 errors:
- Reduce `batch_size` parameter
- Increase delay between requests
- Check Azure OpenAI quota limits

---

## Support

For issues and feature requests, please open an issue on GitHub.

# Inpods Curriculum Mapping Audit System

## Overview

A web-based system that uses Azure OpenAI to automatically map medical education exam questions to curriculum topics/competencies. The system analyzes question text and recommends appropriate curriculum mappings with confidence scores and justifications.

---

## What Was Built

### 1. Audit Engine (`backend/audit_engine.py`)

The core processing engine that:
- Connects to Azure OpenAI API
- Loads question banks and reference curriculum data
- Maps each question to curriculum topics using LLM
- Returns recommendations with confidence scores and justifications

**Key Features:**
- **Batching**: Processes multiple questions per API call (default: 5 questions/batch)
- **Stem Filtering**: Automatically skips stem questions (e.g., "1 (Stem)", "2 (Stem)")
- **Multi-dimension Support**: Maps to topics, competencies, objectives, or skills
- **Token Efficiency**: 60-70% reduction in API costs via batching

### 2. Flask Backend (`backend/app.py`)

REST API server providing endpoints for:
- File upload
- Running audits (single or batched)
- Applying selected mappings
- Downloading exported Excel files

### 3. Frontend UI (`frontend/index.html`)

Single-page web application with:
- File upload interface
- Dimension selector (Topics, Competencies, Objectives, Skills)
- Efficient mode toggle with batch size control
- Recommendations table with selection
- Export functionality

### 4. Test Suite (`backend/test_audit_engine.py`)

16 automated tests covering:
- Expected output validation
- Batch processing logic
- Question-by-question output matching
- Stem filtering verification

---

## What Works Now

| Component | Status | Details |
|-----------|--------|---------|
| Azure OpenAI Connection | Working | Connects and authenticates successfully |
| File Upload | Working | Accepts CSV/Excel files |
| Question Processing | Working | 44 questions processed (stems skipped) |
| Batching | Working | 44 questions = 9 API calls (batch_size=5) |
| Topic Mapping | Working | Maps to 7 curriculum topic areas |
| Confidence Scores | Working | Returns 0.0-1.0 scores |
| Justifications | Working | LLM explains each mapping |
| Frontend UI | Working | Full upload → audit → review → export flow |
| Excel Export | Working | Downloads mapped results as .xlsx |
| Test Suite | Working | 16/16 tests passing |

### Data Flow

```
Input Files                    Processing                      Output
─────────────────────────────────────────────────────────────────────────
Questions CSV     ─┐
(46 questions)     │    ┌─────────────────┐    ┌──────────────┐
                   ├───>│  Audit Engine   │───>│ Recommendations │
Reference CSV     ─┘    │  (Azure OpenAI) │    │ (44 mappings)   │
(7 topic areas)         └─────────────────┘    └───────┬──────────┘
                                                       │
                                                       v
                                               ┌──────────────┐
                                               │ Excel Export │
                                               │ (.xlsx file) │
                                               └──────────────┘
```

### Coverage Results (Sample Run)

```
Topic Area                           Questions Mapped
─────────────────────────────────────────────────────
Infectious Diseases & Laboratory     22
Musculoskeletal, Skin & Soft Tissue  8
Immunology                           5
CVS & Blood                          5
General Microbiology                 2
AETCOM & Bioethics                   1
Gastrointestinal & Hepatobiliary     0 (gap)
─────────────────────────────────────────────────────
Total                                44
```

---

## API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 1. Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "Inpods Audit Engine",
  "version": "1.0.0",
  "azure_connected": true
}
```

---

#### 2. Upload Files

```
POST /api/upload
Content-Type: multipart/form-data
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question_file | File | Yes | Question bank CSV/Excel |
| reference_file | File | Yes | Reference curriculum CSV/Excel |

**Response:**
```json
{
  "status": "success",
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "question_count": 46,
  "reference_count": 7
}
```

**Error Response:**
```json
{
  "error": "Both question_file and reference_file required"
}
```

---

#### 3. Run Audit (Single Mode)

```
POST /api/run-audit
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "dimension": "area_topics"
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| question_file | string | Yes | Uploaded filename |
| reference_file | string | Yes | Uploaded filename |
| dimension | string | Yes | `area_topics`, `competency`, `objective`, `skill` |

**Response:**
```json
{
  "dimension": "area_topics",
  "total_questions": 46,
  "mapped_questions": 44,
  "recommendations": [...],
  "coverage": {...},
  "gaps": [...]
}
```

---

#### 4. Run Audit (Efficient/Batched Mode) - RECOMMENDED

```
POST /api/run-audit-efficient
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "dimension": "area_topics",
  "batch_size": 5
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| question_file | string | Yes | - | Uploaded filename |
| reference_file | string | Yes | - | Uploaded filename |
| dimension | string | Yes | - | Mapping dimension |
| batch_size | int | No | 5 | Questions per API call (1-10) |

**Response:**
```json
{
  "dimension": "area_topics",
  "total_questions": 46,
  "mapped_questions": 44,
  "batch_mode": true,
  "batch_size": 5,
  "recommendations": [
    {
      "question_num": "1.A",
      "question_text": "Explain the sequence of events...",
      "current_mapping": null,
      "recommended_mapping": "Immunology / Antigen/Antibody",
      "mapped_topic": "Immunology",
      "mapped_subtopic": "Antigen/Antibody",
      "confidence": 0.95,
      "justification": "The question involves understanding..."
    }
  ],
  "coverage": {
    "Immunology": 5,
    "Infectious Diseases & Laboratory": 22
  },
  "gaps": ["Gastrointestinal & Hepatobiliary"]
}
```

---

#### 5. Apply Changes & Export

```
POST /api/apply-changes
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_file": "questions.csv",
  "recommendations": [...],
  "selected_indices": [0, 1, 2, 5, 10],
  "dimension": "area_topics"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question_file | string | Yes | Original uploaded filename |
| recommendations | array | Yes | Full recommendations array from audit |
| selected_indices | array | Yes | Indices of accepted recommendations |
| dimension | string | Yes | Mapping dimension used |

**Response:**
```json
{
  "status": "success",
  "output_file": "audit_output_area_topics_20260123_121640.xlsx",
  "download_url": "/download/audit_output_area_topics_20260123_121640.xlsx"
}
```

---

#### 6. Download File

```
GET /api/download/{filename}
```

**Response:** Binary Excel file download

**Error Response:**
```json
{
  "error": "File not found"
}
```

---

## File Structure

```
inpods-audit_cc/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── audit_engine.py        # Core audit logic
│   ├── test_audit_engine.py   # Test suite (16 tests)
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Azure credentials (not in repo)
│   ├── .env.example           # Credential template
│   ├── uploads/               # Uploaded files
│   └── outputs/               # Generated Excel files
├── frontend/
│   └── index.html             # Web UI
├── start.bat                  # Windows startup script
├── start.sh                   # Unix startup script
├── DOCUMENTATION.md           # This file
├── README.md                  # Project readme
├── PROJECT_SUMMARY.md         # Project summary
└── QUICKSTART.md              # Quick start guide
```

---

## Running the Application

### Prerequisites
- Python 3.9+
- Azure OpenAI API credentials

### Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Azure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

3. **Start servers:**
   ```bash
   # Option 1: Use start script
   start.bat          # Windows
   ./start.sh         # Unix/Mac

   # Option 2: Manual
   cd backend && python app.py           # Terminal 1 (port 5000)
   cd frontend && python -m http.server 8000  # Terminal 2 (port 8000)
   ```

4. **Open browser:**
   ```
   http://localhost:8000
   ```

---

## Running Tests

```bash
cd backend

# Run all unit tests
python -m pytest test_audit_engine.py -v

# Run live validation (requires Azure credentials)
python test_audit_engine.py --live
```

---

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| AZURE_OPENAI_API_KEY | Yes | Azure OpenAI API key |
| AZURE_OPENAI_ENDPOINT | Yes | Azure endpoint URL |
| AZURE_OPENAI_DEPLOYMENT | Yes | Model deployment name |
| AZURE_OPENAI_API_VERSION | No | API version (default: 2024-02-15-preview) |

---

## Dimensions Supported

| Dimension | Reference Format | Output Fields |
|-----------|------------------|---------------|
| area_topics | Topic Area, Subtopics | mapped_topic, mapped_subtopic |
| competency | C1-C6 codes | mapped_id (C1, C2, etc.) |
| objective | O1-O6 codes | mapped_id (O1, O2, etc.) |
| skill | S1-S5 codes | mapped_id (S1, S2, etc.) |

---

## Known Behaviors

1. **Stem Questions Skipped**: Questions with "(Stem)" in their number are automatically skipped (they are context-setting, not actual questions)

2. **Batch Size Limits**: Batch size is clamped between 1-10 to balance efficiency and response quality

3. **Confidence Threshold**: UI highlights high confidence (≥85%) in green, medium (70-84%) in yellow, low (<70%) in red

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial release with batching, stem filtering, full UI |

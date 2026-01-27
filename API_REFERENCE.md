# Inpods Audit Engine API Reference

**Version:** 2.0.0
**Base URL:** `http://localhost:5000/api`
**Content-Type:** `application/json` (unless specified)

---

## Authentication

No authentication required for local deployment. Azure OpenAI credentials are configured server-side via environment variables.

---

## Endpoints Overview

### Mode A: Map Unmapped Questions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload question and reference files |
| POST | `/run-audit` | Run audit (single-question mode) |
| POST | `/run-audit-efficient` | Run audit (batched mode) |
| POST | `/apply-changes` | Apply mappings and generate Excel |
| GET | `/download/{filename}` | Download generated file |

### Mode B: Rate Existing Mappings

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-mapped` | Upload pre-mapped file with reference |
| POST | `/rate-mappings` | Rate existing mappings |
| POST | `/apply-changes` | Apply corrections and generate Excel |
| GET | `/download/{filename}` | Download generated file |

### Mode C: Generate Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-mapped` | Upload pre-mapped file |
| POST | `/generate-insights` | Generate visualization charts |
| GET | `/insights/{filename}` | Download chart image |

### Common

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## GET /health

Check API server status and Azure OpenAI connection.

### Request

```
GET /api/health
```

### Response

**Status:** `200 OK`

```json
{
  "status": "ok",
  "service": "Inpods Audit Engine",
  "version": "1.0.0",
  "azure_connected": true
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Server status (`ok`) |
| service | string | Service name |
| version | string | API version |
| azure_connected | boolean | Azure OpenAI connection status |

---

## POST /upload

Upload question bank and reference curriculum files (Mode A).

### Request

```
POST /api/upload
Content-Type: multipart/form-data
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question_file | file | Yes | Question bank file (CSV, XLSX, XLS) |
| reference_file | file | Yes | Reference curriculum file (CSV, XLSX, XLS) |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/upload \
  -F "question_file=@questions.csv" \
  -F "reference_file=@reference.csv"
```

### Success Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "question_count": 46,
  "reference_count": 7
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| question_file | string | Saved question filename |
| reference_file | string | Saved reference filename |
| question_count | integer | Number of questions loaded |
| reference_count | integer | Number of reference items loaded |

### Error Responses

**Status:** `400 Bad Request`

```json
{
  "error": "Both question_file and reference_file required"
}
```

```json
{
  "error": "No files selected"
}
```

```json
{
  "error": "Only CSV/Excel files allowed"
}
```

**Status:** `500 Internal Server Error`

```json
{
  "error": "Error message details"
}
```

---

## POST /upload-mapped

Upload a file with existing mappings (Mode B and Mode C).

### Request

```
POST /api/upload-mapped
Content-Type: multipart/form-data
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| mapped_file | file | Yes | Pre-mapped questions file (CSV, XLSX, XLS, ODS) |
| reference_file | file | No | Reference curriculum file (required for Mode B, optional for Mode C) |

### Example Request (cURL)

```bash
# Mode B: With reference file
curl -X POST http://localhost:5000/api/upload-mapped \
  -F "mapped_file=@mapped_questions.xlsx" \
  -F "reference_file=@reference.csv"

# Mode C: Without reference file
curl -X POST http://localhost:5000/api/upload-mapped \
  -F "mapped_file=@mapped_questions.xlsx"
```

### Success Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "mapped_file": "mapped_questions.xlsx",
  "question_count": 44,
  "columns": ["Question Number", "Question", "mapped_topic", "mapped_subtopic", "confidence_score"],
  "reference_file": "reference.csv",
  "reference_count": 7
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| mapped_file | string | Saved mapped filename |
| question_count | integer | Number of questions loaded |
| columns | array | Column names in the file |
| reference_file | string | Saved reference filename (if provided) |
| reference_count | integer | Number of reference items (if provided) |

### Error Responses

**Status:** `400 Bad Request`

```json
{
  "error": "mapped_file required"
}
```

```json
{
  "error": "No file selected"
}
```

---

## POST /run-audit

Run curriculum mapping audit in single-question mode (one API call per question).

> **Note:** Use `/run-audit-efficient` for production to reduce API costs.

### Request

```
POST /api/run-audit
Content-Type: application/json
```

### Request Body

```json
{
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "dimension": "area_topics"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question_file | string | Yes | Filename from upload response |
| reference_file | string | Yes | Filename from upload response |
| dimension | string | Yes | Mapping dimension (see below) |

### Dimension Values

| Value | Description | Output Fields |
|-------|-------------|---------------|
| `area_topics` | Topic Area / Subtopic mapping | mapped_topic, mapped_subtopic |
| `competency` | Competency codes (C1-C6) | mapped_id |
| `objective` | Objective codes (O1-O6) | mapped_id |
| `skill` | Skill codes (S1-S5) | mapped_id |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/run-audit \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "questions.csv",
    "reference_file": "reference.csv",
    "dimension": "area_topics"
  }'
```

### Success Response

**Status:** `200 OK`

```json
{
  "dimension": "area_topics",
  "total_questions": 46,
  "mapped_questions": 44,
  "recommendations": [
    {
      "question_num": "1.A",
      "question_text": "Explain the sequence of events involved in the pathogenesis...",
      "current_mapping": null,
      "recommended_mapping": "Immunology / Antigen/Antibody",
      "mapped_topic": "Immunology",
      "mapped_subtopic": "Antigen/Antibody",
      "confidence": 0.95,
      "justification": "The question involves understanding the concept of antigenic variation..."
    }
  ],
  "coverage": {
    "Immunology": 5,
    "Infectious Diseases & Laboratory": 22,
    "CVS & Blood": 5
  },
  "gaps": [
    "Gastrointestinal & Hepatobiliary"
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| dimension | string | Mapping dimension used |
| total_questions | integer | Total questions in input file |
| mapped_questions | integer | Questions successfully mapped |
| recommendations | array | Array of recommendation objects |
| coverage | object | Count of questions per mapping target |
| gaps | array | Reference items with zero coverage |

### Recommendation Object

| Field | Type | Description |
|-------|------|-------------|
| question_num | string | Question identifier |
| question_text | string | Question text (truncated to 100 chars) |
| current_mapping | string|null | Existing mapping (if any) |
| recommended_mapping | string | Suggested mapping display text |
| mapped_topic | string | Mapped topic (area_topics dimension) |
| mapped_subtopic | string | Mapped subtopic (area_topics dimension) |
| mapped_id | string | Mapped code (competency/objective/skill dimensions) |
| confidence | number | Confidence score (0.0 - 1.0) |
| justification | string | LLM reasoning for the mapping |

---

## POST /run-audit-efficient

Run curriculum mapping audit in batched mode. **Recommended for production use.**

Reduces API costs by 60-70% by processing multiple questions per API call.

### Request

```
POST /api/run-audit-efficient
Content-Type: application/json
```

### Request Body

```json
{
  "question_file": "questions.csv",
  "reference_file": "reference.csv",
  "dimension": "area_topics",
  "batch_size": 5
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| question_file | string | Yes | - | Filename from upload response |
| reference_file | string | Yes | - | Filename from upload response |
| dimension | string | Yes | - | Mapping dimension |
| batch_size | integer | No | 5 | Questions per API call (1-10) |

### Batch Size Guidelines

| Batch Size | API Calls (44 questions) | Use Case |
|------------|--------------------------|----------|
| 3 | 15 calls | Higher accuracy needed |
| 5 | 9 calls | Balanced (recommended) |
| 7 | 7 calls | Faster processing |
| 10 | 5 calls | Maximum efficiency |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/run-audit-efficient \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "questions.csv",
    "reference_file": "reference.csv",
    "dimension": "area_topics",
    "batch_size": 5
  }'
```

### Success Response

**Status:** `200 OK`

```json
{
  "dimension": "area_topics",
  "total_questions": 46,
  "mapped_questions": 44,
  "batch_mode": true,
  "batch_size": 5,
  "recommendations": [...],
  "coverage": {...},
  "gaps": [...]
}
```

### Additional Response Fields

| Field | Type | Description |
|-------|------|-------------|
| batch_mode | boolean | Always `true` for this endpoint |
| batch_size | integer | Batch size used |

---

## POST /rate-mappings

Rate existing mappings and suggest alternatives (Mode B).

### Request

```
POST /api/rate-mappings
Content-Type: application/json
```

### Request Body

```json
{
  "mapped_file": "mapped_questions.xlsx",
  "reference_file": "reference.csv",
  "dimension": "area_topics",
  "batch_size": 5
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| mapped_file | string | Yes | - | Filename from upload-mapped response |
| reference_file | string | Yes | - | Filename from upload-mapped response |
| dimension | string | No | area_topics | Mapping dimension to rate |
| batch_size | integer | No | 5 | Questions per API call (1-10) |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/rate-mappings \
  -H "Content-Type: application/json" \
  -d '{
    "mapped_file": "mapped_questions.xlsx",
    "reference_file": "reference.csv",
    "dimension": "area_topics",
    "batch_size": 5
  }'
```

### Success Response

**Status:** `200 OK`

```json
{
  "dimension": "area_topics",
  "total_questions": 44,
  "rated_questions": 44,
  "ratings": [
    {
      "question_num": "1.A",
      "question_text": "Explain the sequence of events involved in the pathogenesis...",
      "current_mapping": "Immunology / Antigen/Antibody",
      "rating": "Correct",
      "confidence": 0.95,
      "justification": "The current mapping correctly identifies this as an immunology question...",
      "suggested_mapping": null,
      "suggested_topic": null,
      "suggested_subtopic": null
    },
    {
      "question_num": "5.B",
      "question_text": "Which organism causes typhoid fever...",
      "current_mapping": "Immunology / Host Defense",
      "rating": "Incorrect",
      "confidence": 0.92,
      "justification": "This question is about a specific bacterial pathogen...",
      "suggested_mapping": "Infectious Diseases & Laboratory / Bacteria",
      "suggested_topic": "Infectious Diseases & Laboratory",
      "suggested_subtopic": "Bacteria"
    }
  ],
  "summary": {
    "correct": 35,
    "partially_correct": 5,
    "incorrect": 4
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| dimension | string | Mapping dimension rated |
| total_questions | integer | Total questions in input file |
| rated_questions | integer | Questions successfully rated |
| ratings | array | Array of rating objects |
| summary | object | Count by rating category |

### Rating Object

| Field | Type | Description |
|-------|------|-------------|
| question_num | string | Question identifier |
| question_text | string | Question text (truncated) |
| current_mapping | string | Existing mapping in the file |
| rating | string | "Correct", "Partially Correct", or "Incorrect" |
| confidence | number | Confidence in the rating (0.0 - 1.0) |
| justification | string | LLM reasoning for the rating |
| suggested_mapping | string|null | Alternative mapping (if rating is not Correct) |
| suggested_topic | string|null | Suggested topic (area_topics dimension) |
| suggested_subtopic | string|null | Suggested subtopic (area_topics dimension) |
| suggested_id | string|null | Suggested code (competency/objective/skill dimensions) |

### Summary Object

| Field | Type | Description |
|-------|------|-------------|
| correct | integer | Count of correctly mapped questions |
| partially_correct | integer | Count of partially correct mappings |
| incorrect | integer | Count of incorrect mappings |

### Error Responses

**Status:** `400 Bad Request`

```json
{
  "error": "mapped_file required"
}
```

```json
{
  "error": "reference_file required"
}
```

---

## POST /generate-insights

Generate visualization charts from mapping data (Mode C).

### Request

```
POST /api/generate-insights
Content-Type: application/json
```

### Request Body

```json
{
  "mapped_file": "mapped_questions.xlsx",
  "reference_file": "reference.csv"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| mapped_file | string | Yes | Filename from upload-mapped response |
| reference_file | string | No | Reference file for gap analysis |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/generate-insights \
  -H "Content-Type: application/json" \
  -d '{
    "mapped_file": "mapped_questions.xlsx",
    "reference_file": "reference.csv"
  }'
```

### Success Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "charts": {
    "summary": "/insights/summary_dashboard.png",
    "bar_chart": "/insights/topic_distribution.png",
    "pie_chart": "/insights/percentage_distribution.png",
    "histogram": "/insights/confidence_histogram.png",
    "gap_analysis": "/insights/gap_analysis.png"
  },
  "summary": {
    "total_questions": 44,
    "topics_covered": 6,
    "average_confidence": 0.89
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| charts | object | URLs to generated chart images |
| summary | object | Summary statistics |

### Charts Object

| Field | Type | Description |
|-------|------|-------------|
| summary | string | URL to summary dashboard image |
| bar_chart | string | URL to topic distribution bar chart |
| pie_chart | string | URL to percentage pie chart |
| histogram | string | URL to confidence score histogram |
| gap_analysis | string | URL to gap analysis chart |

### Summary Object

| Field | Type | Description |
|-------|------|-------------|
| total_questions | integer | Total questions analyzed |
| topics_covered | integer | Number of unique topics with mappings |
| average_confidence | number | Average confidence score (0.0 - 1.0) |

### Error Responses

**Status:** `400 Bad Request`

```json
{
  "error": "mapped_file required"
}
```

---

## GET /insights/{filename}

Download a generated chart image (Mode C).

### Request

```
GET /api/insights/{filename}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| filename | string | Yes | Chart filename from generate-insights response |

### Example Request

```bash
curl -O http://localhost:5000/api/insights/topic_distribution.png
```

### Success Response

**Status:** `200 OK`
**Content-Type:** `image/png`

Binary PNG image file.

### Error Response

**Status:** `404 Not Found`

```json
{
  "error": "Chart not found"
}
```

---

## POST /apply-changes

Apply selected recommendations/corrections and generate Excel export file.

Works with both Mode A (new mappings) and Mode B (corrected mappings).

### Request

```
POST /api/apply-changes
Content-Type: application/json
```

### Request Body

```json
{
  "question_file": "questions.csv",
  "recommendations": [...],
  "selected_indices": [0, 1, 2, 5, 10, 15],
  "dimension": "area_topics"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question_file | string | Yes | Original uploaded filename |
| recommendations | array | Yes | Full recommendations/ratings array from audit/rate response |
| selected_indices | array | Yes | Array of indices to apply (0-based) |
| dimension | string | Yes | Mapping dimension used |

### Example Request (cURL)

```bash
curl -X POST http://localhost:5000/api/apply-changes \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "questions.csv",
    "recommendations": [...],
    "selected_indices": [0, 1, 2, 3, 4],
    "dimension": "area_topics"
  }'
```

### Success Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "output_file": "audit_output_area_topics_20260123_121640.xlsx",
  "download_url": "/download/audit_output_area_topics_20260123_121640.xlsx"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| output_file | string | Generated filename |
| download_url | string | Relative URL for download |

### Error Responses

**Status:** `400 Bad Request`

```json
{
  "error": "Missing required parameters"
}
```

---

## GET /download/{filename}

Download a generated Excel file.

### Request

```
GET /api/download/{filename}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| filename | string | Yes | Filename from apply-changes response |

### Example Request

```bash
curl -O http://localhost:5000/api/download/audit_output_area_topics_20260123_121640.xlsx
```

### Success Response

**Status:** `200 OK`
**Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

Binary Excel file download.

### Error Response

**Status:** `404 Not Found`

```json
{
  "error": "File not found"
}
```

---

## Error Handling

All endpoints return errors in a consistent format:

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Missing or invalid parameters |
| 404 | Not Found - Resource does not exist |
| 500 | Internal Server Error - Server-side error |

---

## Rate Limits

No rate limits enforced by the API server. Azure OpenAI rate limits apply based on your deployment configuration.

---

## File Size Limits

- Maximum upload size: **16 MB** per file
- Supported formats: CSV, XLSX, XLS, ODS

---

## Example Workflows

### Mode A: Map Unmapped Questions

```bash
# 1. Check server health
curl http://localhost:5000/api/health

# 2. Upload files
curl -X POST http://localhost:5000/api/upload \
  -F "question_file=@questions.csv" \
  -F "reference_file=@reference.csv"

# 3. Run batched audit
curl -X POST http://localhost:5000/api/run-audit-efficient \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "questions.csv",
    "reference_file": "reference.csv",
    "dimension": "area_topics",
    "batch_size": 5
  }'

# 4. Apply selected mappings
curl -X POST http://localhost:5000/api/apply-changes \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "questions.csv",
    "recommendations": [...],
    "selected_indices": [0,1,2,3,4,5],
    "dimension": "area_topics"
  }'

# 5. Download result
curl -O http://localhost:5000/api/download/audit_output_area_topics_20260123_121640.xlsx
```

### Mode B: Rate Existing Mappings

```bash
# 1. Upload mapped file with reference
curl -X POST http://localhost:5000/api/upload-mapped \
  -F "mapped_file=@mapped_questions.xlsx" \
  -F "reference_file=@reference.csv"

# 2. Rate the mappings
curl -X POST http://localhost:5000/api/rate-mappings \
  -H "Content-Type: application/json" \
  -d '{
    "mapped_file": "mapped_questions.xlsx",
    "reference_file": "reference.csv",
    "dimension": "area_topics"
  }'

# 3. Apply corrections for incorrect mappings
curl -X POST http://localhost:5000/api/apply-changes \
  -H "Content-Type: application/json" \
  -d '{
    "question_file": "mapped_questions.xlsx",
    "recommendations": [...],
    "selected_indices": [3, 7, 12],
    "dimension": "area_topics"
  }'

# 4. Download corrected file
curl -O http://localhost:5000/api/download/audit_output_area_topics_20260123_143022.xlsx
```

### Mode C: Generate Insights

```bash
# 1. Upload mapped file
curl -X POST http://localhost:5000/api/upload-mapped \
  -F "mapped_file=@mapped_questions.xlsx" \
  -F "reference_file=@reference.csv"

# 2. Generate insights
curl -X POST http://localhost:5000/api/generate-insights \
  -H "Content-Type: application/json" \
  -d '{
    "mapped_file": "mapped_questions.xlsx",
    "reference_file": "reference.csv"
  }'

# 3. Download charts
curl -O http://localhost:5000/api/insights/summary_dashboard.png
curl -O http://localhost:5000/api/insights/topic_distribution.png
curl -O http://localhost:5000/api/insights/percentage_distribution.png
curl -O http://localhost:5000/api/insights/confidence_histogram.png
curl -O http://localhost:5000/api/insights/gap_analysis.png
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-23 | Added Mode B (rate-mappings), Mode C (generate-insights), ODS support |
| 1.0.0 | 2026-01-23 | Initial API release |

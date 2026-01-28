# Inpods Curriculum Mapping Audit System V2
## Complete Technical Documentation

**Version:** 2.0.0
**Last Updated:** January 2025
**Author:** AI-Assisted Development

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Backend: app.py](#backend-apppy)
4. [Backend: audit_engine.py](#backend-audit_enginepy)
5. [Backend: visualization_engine.py](#backend-visualization_enginepy)
6. [Frontend: index.html](#frontend-indexhtml)
7. [API Reference](#api-reference)
8. [Data Flow](#data-flow)
9. [Token Usage Tracking](#token-usage-tracking)

---

## System Overview

The Inpods Curriculum Mapping Audit System is a web application that uses Azure OpenAI to automatically map educational questions to curriculum frameworks. It supports three operational modes:

- **Mode A:** Map unmapped questions to curriculum topics
- **Mode B:** Analyze and improve existing mappings
- **Mode C:** Generate visualization insights and gap analysis

### Key Features
- AI-powered curriculum mapping using GPT-4
- Batch processing for 60-70% token cost savings
- Token usage tracking per operation
- Coverage table with Code -> Definition -> Questions -> Percentage
- MCQ option handling (combines options with question text)
- Library system for saving/loading mapping sets
- Excel export functionality

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Port 8001)                     │
│                     frontend_v2/index.html                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Mode A    │  │   Mode B    │  │   Mode C    │         │
│  │  Mapping    │  │   Rating    │  │  Insights   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (Port 5001)                      │
│                     backend_v2/app.py                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Flask REST API                    │   │
│  │  /api/upload  /api/run-audit  /api/rate-mappings    │   │
│  │  /api/generate-insights  /api/library/*             │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │              ┌───────┴───────┐                      │   │
│  │              │  AuditEngine  │ ◄── audit_engine.py  │   │
│  │              └───────┬───────┘                      │   │
│  │                      │                              │   │
│  │              ┌───────┴───────┐                      │   │
│  │              │ Azure OpenAI  │                      │   │
│  │              │    GPT-4      │                      │   │
│  │              └───────────────┘                      │   │
│  │                                                     │   │
│  │  ┌───────────────────┐  ┌───────────────────┐      │   │
│  │  │VisualizationEngine│  │  LibraryManager   │      │   │
│  │  └───────────────────┘  └───────────────────┘      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend: app.py

**Location:** `backend_v2/app.py`
**Purpose:** Flask REST API server handling all HTTP requests

### Line-by-Line Documentation

```python
"""
Lines 1-13: Module Docstring
Describes the purpose of the file and V2 changes including:
- Combined save & download functionality
- Full question text preservation
- Tool-ready API design for future agent integration
- Port 5001 (parallel to V1 on 5000)
"""

# Lines 15-21: Import Statements
from flask import Flask, request, jsonify, send_file  # Flask web framework
from flask_cors import CORS                            # Cross-Origin Resource Sharing
import pandas as pd                                    # Data manipulation
import os                                              # File system operations
from werkzeug.utils import secure_filename             # Secure file upload handling
from datetime import datetime                          # Timestamp generation
from dotenv import load_dotenv                         # Environment variable loading

# Lines 23-24: Local Imports
from audit_engine import AuditEngine, LibraryManager   # Core AI engine
from visualization_engine import VisualizationEngine  # Chart generation

# Line 27: Load .env file for configuration
load_dotenv()

# Lines 29-30: Flask App Initialization
app = Flask(__name__)     # Create Flask application instance
CORS(app)                 # Enable CORS for all routes (allows frontend on different port)

# Lines 33-37: Folder Configuration
UPLOAD_FOLDER = 'uploads'           # Where uploaded files are stored
OUTPUT_FOLDER = 'outputs'           # Where generated Excel files go
INSIGHTS_FOLDER = 'outputs/insights' # Where chart images are saved
LIBRARY_FOLDER = 'outputs/library'   # Where saved mappings are stored
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'ods'}  # Allowed file types

# Lines 39-42: Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(INSIGHTS_FOLDER, exist_ok=True)
os.makedirs(LIBRARY_FOLDER, exist_ok=True)

# Lines 44-48: Flask Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['INSIGHTS_FOLDER'] = INSIGHTS_FOLDER
app.config['LIBRARY_FOLDER'] = LIBRARY_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Lines 50-58: Azure OpenAI Configuration
azure_config = {
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),           # API key from .env
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),   # Azure endpoint URL
    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
    'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')  # Model deployment name
}

# Lines 61-76: Validate and Initialize Engines
# Checks if credentials exist, initializes AuditEngine, tests connection
# Exits with error if connection fails

# Lines 79-80: Initialize Other Engines
viz_engine = VisualizationEngine(output_folder=INSIGHTS_FOLDER)
library_manager = LibraryManager(library_folder=LIBRARY_FOLDER)

# Lines 83-85: Helper Function - File Extension Check
def allowed_file(filename):
    """Returns True if file extension is in allowed list"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### Key Endpoints

#### `/api/health` (GET) - Lines 92-105
```python
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Returns service health status
    Response: {status: 'ok', service: 'Inpods Audit Engine V2', version: '2.0.0', azure_connected: bool}
    """
```

#### `/api/upload` (POST) - Lines 261-311
```python
@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Uploads question bank and reference files for Mode A

    Request: multipart/form-data with question_file and reference_file

    Process:
    1. Validate both files are present
    2. Check file extensions are allowed
    3. Save files to UPLOAD_FOLDER with secure filenames
    4. Read files with pandas to validate format
    5. Extract metadata from both files
    6. Return file info and metadata

    Response: {
        status, question_file, reference_file,
        question_count, reference_count,
        question_metadata, reference_metadata
    }
    """
```

#### `/api/run-audit-efficient` (POST) - Lines 346-379
```python
@app.route('/api/run-audit-efficient', methods=['POST'])
def run_audit_efficient():
    """
    Runs batched mapping audit (60-70% cost savings)

    Request JSON: {question_file, reference_file, dimension, batch_size}

    Process:
    1. Validate required parameters
    2. Clamp batch_size between 1-10
    3. Build file paths
    4. Call audit_engine.run_audit_batched()
    5. Return results including token_usage

    Response: {
        recommendations, coverage, gaps, dimension,
        total_questions, mapped_questions, batch_mode,
        batch_size, reference_definitions, token_usage
    }
    """
```

#### `/api/generate-insights` (POST) - Lines 652-761
```python
@app.route('/api/generate-insights', methods=['POST'])
def generate_insights():
    """
    Generates visualization charts from mapping data (Mode C)

    Request JSON: {mapped_file, reference_file (optional)}

    Process:
    1. Load mapped data from file
    2. Build coverage dictionary counting each topic
    3. Extract recommendations with confidence scores
    4. Load reference definitions if provided
    5. Generate all charts via viz_engine
    6. Build chart URLs for frontend
    7. Return coverage_table data separately

    Response: {
        status, charts: {chart_name: url, ...},
        coverage_table: [{code, definition, count, percentage}, ...],
        summary: {total_questions, topics_covered, average_confidence}
    }
    """
```

### Metadata Extraction Functions

#### `extract_reference_metadata()` - Lines 112-217
```python
def extract_reference_metadata(file_path):
    """
    Scans reference file for curriculum codes

    Detection Logic:
    - MI*.* patterns -> NMC Competencies
    - C1-C9 patterns -> Competencies
    - O1-O9 patterns -> Objectives
    - S1-S9 patterns -> Skills
    - "Topic" headers -> Topic Areas

    Returns: {
        competencies: [{id, description}, ...],
        objectives: [{id, description}, ...],
        skills: [{id, description}, ...],
        nmc_competencies: [{id, description}, ...],
        topics: [{topic, subtopics}, ...],
        detected_type: 'nmc_competency'|'competency'|'objective'|'skill'|'area_topics'
    }
    """
```

#### `extract_question_metadata()` - Lines 220-258
```python
def extract_question_metadata(file_path):
    """
    Extracts info from question file

    Returns: {
        total_questions: int,
        columns: [column names],
        sample_questions: [{number, text}, ...] (first 5)
    }
    """
```

---

## Backend: audit_engine.py

**Location:** `backend_v2/audit_engine.py`
**Purpose:** Core AI engine for curriculum mapping operations

### Line-by-Line Documentation

```python
"""
Lines 1-9: Module Docstring
Core Audit Engine V2 with dimension-agnostic curriculum mapping
V2 Changes: Full question text, cleaner tool interfaces, structured outputs
"""

# Lines 11-16: Imports
from openai import AzureOpenAI  # Azure OpenAI SDK
import pandas as pd             # Data manipulation
import json                     # JSON parsing
from datetime import datetime   # Timestamps
import os                       # File operations
import uuid                     # Unique ID generation
```

### Class: AuditEngine

#### `__init__()` - Lines 27-44
```python
def __init__(self, config):
    """
    Initialize with Azure OpenAI configuration

    config = {
        'api_key': str,
        'azure_endpoint': str,
        'api_version': str,
        'deployment': str (model name)
    }

    Stores config and calls _initialize_client()
    """
```

#### `_get_full_question_text()` - Lines 46-69
```python
def _get_full_question_text(self, row):
    """
    CRITICAL: Combines question text with MCQ options

    Process:
    1. Get base question text from 'Question Text' column
    2. Look for option columns: 'option a', 'Option A', 'A', etc.
    3. Format options as "A. <text>\nB. <text>\n..."
    4. Append formatted options to question text

    This ensures MCQ options are mapped WITH the question,
    not as separate items.

    Returns: Complete question string with options
    """
```

#### `_call_llm()` - Lines 330-372
```python
def _call_llm(self, prompt, max_tokens=500):
    """
    Makes Azure OpenAI API call

    Request:
    - System message: "You are a medical education curriculum mapping expert. Always respond with valid JSON."
    - User message: The prompt
    - temperature=0.3 (low for consistency)
    - response_format={"type": "json_object"} (ensures JSON response)

    Returns: tuple(parsed_json_response, token_usage_dict)

    Token usage dict: {
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    }
    """
```

#### `run_audit_batched()` - Lines 462-620
```python
def run_audit_batched(self, question_csv, reference_csv, dimension, batch_size=5):
    """
    MAIN MAPPING FUNCTION - Batched mode for efficiency

    Process:
    1. Load question CSV into DataFrame
    2. Load reference data based on dimension
    3. Initialize token_usage tracker
    4. Prepare questions list (skip stem questions)
    5. Calculate total batches

    For each batch:
        a. Build batch prompt with multiple questions
        b. Call Azure OpenAI API
        c. Track token usage from response.usage
        d. Parse JSON response for mappings array
        e. Match mappings to questions
        f. Build recommendation objects
        g. Update coverage counts

    Error Handling:
    - If batch fails, falls back to one-by-one processing
    - Logs errors but continues with other batches

    Returns: {
        recommendations: [{
            question_num, question_text, current_mapping,
            recommended_mapping, mapped_id/mapped_topic,
            confidence, justification
        }, ...],
        coverage: {topic: count, ...},
        gaps: [topics with zero coverage],
        dimension, total_questions, mapped_questions,
        batch_mode: true, batch_size,
        reference_definitions: {code: definition, ...},
        token_usage: {prompt_tokens, completion_tokens, total_tokens, api_calls}
    }
    """
```

#### `rate_existing_mappings()` - Lines 761-919
```python
def rate_existing_mappings(self, mapped_file, reference_csv, dimension, batch_size=5):
    """
    MODE B: Evaluates existing mappings

    Process:
    1. Load mapped file (CSV, Excel, or ODS)
    2. Load reference data
    3. Build questions list with existing mappings
    4. Process in batches with rating prompt

    Rating Categories:
    - "correct": Mapping is accurate
    - "partially_correct": Related but not optimal
    - "incorrect": Wrong mapping

    For non-correct mappings, provides:
    - suggested_id/suggested_topic: Better alternative
    - suggestion_confidence: How confident in suggestion
    - suggestion_justification: Why suggest change

    Returns: {
        ratings: [all rating results],
        summary: {correct, partially_correct, incorrect counts},
        recommendations: [non-correct with suggestions],
        token_usage: {...}
    }
    """
```

### Class: LibraryManager

#### `save_mapping()` - Lines 944-980
```python
def save_mapping(self, name, recommendations, dimension, mode, source_file=''):
    """
    Saves mapping set to JSON file in library folder

    Creates unique 8-character ID using uuid4
    Stores: id, name, created_at, dimension, mode, source_file,
            question_count, recommendations

    File: {library_folder}/{id}.json
    """
```

#### `export_to_excel()` - Lines 1049-1085
```python
def export_to_excel(self, mapping_id, output_folder):
    """
    Exports saved mapping to Excel file

    Creates DataFrame with columns:
    - Question Number
    - Question Text
    - Mapped Topic
    - Mapped Subtopic
    - Confidence
    - Justification
    """
```

---

## Backend: visualization_engine.py

**Location:** `backend_v2/visualization_engine.py`
**Purpose:** Generates matplotlib charts for insights

### Line-by-Line Documentation

```python
# Lines 1-6: Module Docstring
"""Generates static charts (PNG) for stakeholder reporting"""

# Lines 8-14: Imports
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import os
from datetime import datetime
from collections import Counter
```

### Class: VisualizationEngine

#### `__init__()` - Lines 20-26
```python
def __init__(self, output_folder='outputs/insights'):
    """
    Initialize with output folder and style settings

    - Creates output folder if needed
    - Sets seaborn-v0_8-whitegrid style
    - Defines color palette for charts
    """
```

#### `generate_topic_bar_chart()` - Lines 28-66
```python
def generate_topic_bar_chart(self, coverage_data, title):
    """
    Creates horizontal bar chart of question counts per topic

    Features:
    - Sorted by count descending
    - Color-coded bars
    - Value labels on bars
    - Saves as PNG with timestamp filename

    Returns: filepath to saved PNG
    """
```

#### `generate_percentage_pie_chart()` - Lines 68-108
```python
def generate_percentage_pie_chart(self, coverage_data, title):
    """
    Creates donut chart showing topic distribution

    Features:
    - Percentage labels
    - Legend with counts
    - Center text showing total

    Returns: filepath to saved PNG
    """
```

#### `generate_confidence_histogram()` - Lines 110-172
```python
def generate_confidence_histogram(self, confidence_scores, title):
    """
    Creates histogram of confidence score distribution

    Bins: <50%, 50-60%, 60-70%, 70-80%, 80-85%, 85-90%, 90-95%, 95-100%

    Color coding:
    - Red: <70% (low confidence)
    - Yellow: 70-85% (medium)
    - Green: >85% (high)

    Includes stats annotation: Avg and High Confidence count

    Returns: filepath to saved PNG
    """
```

#### `generate_gap_analysis_chart()` - Lines 174-238
```python
def generate_gap_analysis_chart(self, coverage_data, reference_topics, title):
    """
    Shows all reference topics with their coverage status

    Color coding:
    - Red: 0 questions (GAP)
    - Yellow: 1-2 questions (low)
    - Green: 3+ questions (good)

    Labels show count or "GAP" for zero coverage

    Returns: filepath to saved PNG
    """
```

#### `generate_coverage_table()` - Lines 325-366
```python
def generate_coverage_table(self, coverage_data, reference_data, total_questions):
    """
    Generates coverage table data (not a chart)

    For each curriculum code:
    - code: The curriculum code (e.g., "MI1.1", "C1")
    - definition: Description text (truncated to 200 chars)
    - count: Number of questions mapped
    - percentage: (count / total) * 100

    Sorted by count descending, gaps at end

    Returns: [{code, definition, count, percentage}, ...]
    """
```

#### `generate_all_insights()` - Lines 368-406
```python
def generate_all_insights(self, mapping_data, reference_topics, reference_definitions):
    """
    Master function generating all charts

    Generates:
    1. topic_bar_chart
    2. topic_pie_chart
    3. confidence_histogram
    4. gap_analysis
    5. summary_dashboard
    6. coverage_table (data, not image)

    Returns: {chart_name: filepath, ..., coverage_table: [...]}
    """
```

---

## Frontend: index.html

**Location:** `frontend_v2/index.html`
**Purpose:** Single-page web application UI

### Structure Overview

```
index.html
├── <head>
│   └── <style> (Lines 7-770)
│       ├── Reset and base styles
│       ├── Layout (container, header, sidebar)
│       ├── Mode cards (selection screen)
│       ├── Forms and inputs
│       ├── Tables and recommendations
│       ├── Charts and insights
│       ├── Coverage table styling
│       ├── Token usage display
│       └── Responsive breakpoints
│
├── <body>
│   ├── Header with title and version badge
│   ├── Status notification area
│   ├── Mode Selection Cards (A, B, C)
│   ├── Main Content Area
│   │   ├── Sidebar (Library)
│   │   ├── Mode A UI
│   │   ├── Mode B UI
│   │   ├── Mode C UI
│   │   └── Library View
│   └── Save Modal
│
└── <script> (Lines 1145-2100+)
    ├── Configuration (API_URL, BASE_URL)
    ├── State variables
    ├── Initialization
    ├── Library functions
    ├── Mode A functions
    ├── Mode B functions
    ├── Mode C functions
    └── Helper functions
```

### CSS Documentation (Key Sections)

```css
/* Lines 14-20: Base Body Styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa;    /* Light gray background */
    padding: 30px;
    line-height: 1.7;
    font-size: 20px;        /* Base font size */
    zoom: 1.3;              /* 30% zoom for larger UI */
}

/* Lines 157-174: Mode Selection Cards */
.mode-card {
    background: white;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: all 0.3s ease;
    border: 3px solid transparent;
    text-align: center;
}
/* Hover lifts card up */
.mode-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

/* Lines 683-730: Token Usage Display */
.token-usage {
    display: flex;
    gap: 20px;
    padding: 15px 20px;
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 8px;
    margin-bottom: 20px;
}
.token-stat-value {
    font-size: 20px;
    font-weight: 700;
    color: #00d4aa;  /* Green for prompt/completion */
}
.token-stat.total .token-stat-value {
    color: #ffa600;  /* Orange for total */
}

/* Lines 617-680: Coverage Table */
.coverage-table th {
    background: #1e293b;
    color: white;
    font-weight: 600;
}
.coverage-table .gap-row {
    background: #fee2e2;    /* Red highlight for gaps */
}
.coverage-table .low-row {
    background: #fef3c7;    /* Yellow for low coverage */
}
```

### JavaScript Documentation

#### Configuration - Lines 1145-1147
```javascript
const API_URL = 'http://localhost:5001/api';  // Backend API base
const BASE_URL = 'http://localhost:5001';     // For file downloads
```

#### State Variables - Lines 1149-1160
```javascript
let currentMode = null;           // 'A', 'B', 'C', or null
let currentLibraryId = null;      // Currently viewed library item
let uploadedFilesA = {...};       // Mode A file references
let uploadedFilesB = {...};       // Mode B file references
let uploadedFilesC = {...};       // Mode C file references
let recommendationsA = [];        // Mode A mapping results
let referenceDefinitionsA = {};   // Definitions for display
let ratingsB = [];                // Mode B rating results
let recommendationsB = [];        // Mode B recommendations
let selectedIndicesA = [];        // Selected checkboxes Mode A
let selectedIndicesB = [];        // Selected checkboxes Mode B
```

#### Mode A: runAuditA() - Lines 1560-1610
```javascript
async function runAuditA() {
    /*
    Executes the mapping audit

    Process:
    1. Hide file overview, show loading spinner
    2. Build request with file names, dimension, batch size
    3. POST to /api/run-audit-efficient
    4. On success:
       - Store recommendations and definitions
       - Display recommendations table
       - Display token usage
       - Show success message
    5. On error:
       - Show error message
       - Return to file overview
    */
}
```

#### displayTokenUsageA() - Lines 1635-1640
```javascript
function displayTokenUsageA(tokenUsage) {
    /*
    Updates token usage display elements

    Sets text content for:
    - promptTokensA: formatted prompt token count
    - completionTokensA: formatted completion count
    - totalTokensA: formatted total
    - apiCallsA: number of API calls
    */
    document.getElementById('promptTokensA').textContent =
        tokenUsage.prompt_tokens.toLocaleString();
    // ... etc
}
```

#### displayRecommendationsA() - Lines 1603-1633
```javascript
function displayRecommendationsA(recs, definitions = {}) {
    /*
    Renders recommendations table

    For each recommendation:
    1. Create table row
    2. Determine confidence class (high/medium/low)
    3. Get definition from definitions dict
    4. Build HTML with:
       - Checkbox for selection
       - Question number
       - Full question text (scrollable)
       - Mapping code (bold)
       - Definition (italic)
       - Confidence badge (color-coded)
       - Justification
    5. Append row to table body
    */
}
```

#### displayInsightsC() - Lines 2040-2110
```javascript
function displayInsightsC(data) {
    /*
    Renders Mode C insights

    1. Summary Stats:
       - Total questions
       - Topics covered
       - Average confidence
       - Charts generated

    2. Charts Grid:
       - Loads each chart image from URL
       - summary_dashboard is full-width
       - Others are 2-column grid

    3. Coverage Table:
       - For each item in coverage_table:
         - Determine row class (gap-row, low-row, or none)
         - Calculate percentage bar width
         - Render code, definition, count, percentage with bar
    */
}
```

---

## API Reference

### Mode A Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload question and reference files |
| `/api/run-audit` | POST | Run single-question mapping |
| `/api/run-audit-efficient` | POST | Run batched mapping (recommended) |
| `/api/apply-and-save` | POST | Apply mappings, save to library, download Excel |

### Mode B Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-mapped` | POST | Upload pre-mapped file |
| `/api/rate-mappings` | POST | Analyze existing mappings |
| `/api/apply-corrections-and-save` | POST | Apply corrections, save, download |

### Mode C Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-insights` | POST | Generate all visualization charts |
| `/api/insights/<filename>` | GET | Download chart image |

### Library Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/library` | GET | List all saved mappings |
| `/api/library/<id>` | GET | Get specific mapping |
| `/api/library/<id>` | DELETE | Delete mapping |
| `/api/library/<id>/export` | GET | Export to Excel |

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/download/<filename>` | GET | Download output file |

---

## Data Flow

### Mode A: Mapping Unmapped Questions

```
1. User selects Mode A
2. User uploads question_file + reference_file
   └─> POST /api/upload
       └─> Files saved to uploads/
       └─> Metadata extracted and returned

3. User clicks "Run Audit"
   └─> POST /api/run-audit-efficient
       └─> audit_engine.run_audit_batched()
           └─> For each batch:
               └─> Build prompt with questions + reference
               └─> POST to Azure OpenAI
               └─> Parse JSON response
               └─> Track token usage
           └─> Return recommendations + token_usage

4. User reviews recommendations (with definitions)
5. User selects recommendations to apply
6. User clicks "Save & Download"
   └─> POST /api/apply-and-save
       └─> Apply to original file
       └─> Save to library as JSON
       └─> Generate Excel file
       └─> Return download URL
```

### Mode B: Rating Existing Mappings

```
1. User selects Mode B
2. User uploads mapped_file + reference_file
   └─> POST /api/upload-mapped

3. Immediately runs rating
   └─> POST /api/rate-mappings
       └─> audit_engine.rate_existing_mappings()
           └─> For each batch:
               └─> Build rating prompt with current mappings
               └─> POST to Azure OpenAI
               └─> Get ratings + suggestions
               └─> Track token usage
           └─> Return ratings + summary + token_usage

4. User reviews ratings
5. User selects corrections to apply
6. User clicks "Save & Download Corrections"
```

### Mode C: Generate Insights

```
1. User selects Mode C
2. User uploads mapped_file (+ optional reference)
   └─> POST /api/upload-mapped

3. User clicks "Generate Insights"
   └─> POST /api/generate-insights
       └─> Parse coverage from mapped file
       └─> viz_engine.generate_all_insights()
           └─> Generate 5 PNG charts
           └─> Generate coverage_table data
       └─> Return chart URLs + coverage_table

4. Frontend displays:
   - Summary stats
   - Chart images
   - Coverage table with definitions
```

---

## Token Usage Tracking

### Backend Implementation

Token usage is captured from Azure OpenAI API responses:

```python
# In run_audit_batched():
response = self.client.chat.completions.create(...)

# response.usage contains:
# - prompt_tokens: Tokens in the input
# - completion_tokens: Tokens in the output
# - total_tokens: Sum of both

if response.usage:
    total_token_usage['prompt_tokens'] += response.usage.prompt_tokens
    total_token_usage['completion_tokens'] += response.usage.completion_tokens
    total_token_usage['total_tokens'] += response.usage.total_tokens
total_token_usage['api_calls'] += 1
```

### Frontend Display

```html
<div class="token-usage">
    <span class="token-usage-title">API Token Usage</span>
    <div class="token-stat">
        <span class="token-stat-value" id="promptTokensA">0</span>
        <span class="token-stat-label">Prompt</span>
    </div>
    <!-- ... more stats ... -->
</div>
```

```javascript
function displayTokenUsageA(tokenUsage) {
    document.getElementById('promptTokensA').textContent =
        tokenUsage.prompt_tokens.toLocaleString();
    document.getElementById('completionTokensA').textContent =
        tokenUsage.completion_tokens.toLocaleString();
    document.getElementById('totalTokensA').textContent =
        tokenUsage.total_tokens.toLocaleString();
    document.getElementById('apiCallsA').textContent =
        tokenUsage.api_calls || 0;
}
```

---

## File Structure

```
inpods-audit_cc/
├── backend_v2/
│   ├── app.py                 # Flask API server (924 lines)
│   ├── audit_engine.py        # Core AI engine (1086 lines)
│   ├── visualization_engine.py # Chart generation (407 lines)
│   ├── .env                   # Environment variables (not in git)
│   ├── .env.example           # Template for .env
│   ├── uploads/               # Uploaded files
│   └── outputs/
│       ├── insights/          # Generated chart PNGs
│       └── library/           # Saved mapping JSONs
│
├── frontend_v2/
│   └── index.html             # Complete frontend (~2100 lines)
│
├── run_v2.bat                 # Windows startup script
└── TECHNICAL_DOCUMENTATION_V2.md  # This file
```

---

## Environment Variables

```env
# Required
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Optional (have defaults)
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

---

## Running the Application

### Windows
```batch
# Start both servers
run_v2.bat

# Or manually:
cd backend_v2 && python app.py    # Port 5001
cd frontend_v2 && python -m http.server 8001
```

### Access
- Frontend: http://localhost:8001
- Backend API: http://localhost:5001
- Health Check: http://localhost:5001/api/health

---

*End of Technical Documentation*

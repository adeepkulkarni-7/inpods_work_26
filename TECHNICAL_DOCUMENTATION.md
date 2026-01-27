# Inpods Curriculum Mapping System - Technical Documentation

A comprehensive guide for understanding, running, and maintaining the curriculum mapping audit system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Folder Structure](#folder-structure)
3. [How to Run the System](#how-to-run-the-system)
4. [System Flow Diagram](#system-flow-diagram)
5. [Backend Explained](#backend-explained)
6. [Frontend Explained](#frontend-explained)
7. [The 3 Tools](#the-3-tools)
8. [Supported Dimensions](#supported-dimensions)
9. [File-by-File Explanation](#file-by-file-explanation)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

### What Does This System Do?

This system helps medical educators map exam questions to curriculum standards using AI (Azure OpenAI GPT-4). It answers questions like:
- "Which curriculum topic does this question test?"
- "Is this question correctly mapped to its learning objective?"
- "Which topics have too few or too many questions?"

### Key Components

```
┌─────────────────┐     HTTP Requests      ┌─────────────────┐
│                 │ ──────────────────────>│                 │
│    FRONTEND     │                        │     BACKEND     │
│  (HTML + JS)    │ <──────────────────────│  (Python Flask) │
│                 │     JSON Responses     │                 │
└─────────────────┘                        └────────┬────────┘
                                                    │
                                                    │ API Calls
                                                    v
                                           ┌─────────────────┐
                                           │   Azure OpenAI  │
                                           │    (GPT-4)      │
                                           └─────────────────┘
```

---

## Folder Structure

```
inpods-audit_cc/
│
├── backend_v2/                    # Main backend server
│   ├── app.py                     # Flask web server (API endpoints)
│   ├── audit_engine.py            # Core AI mapping logic
│   ├── visualization_engine.py    # Chart generation (matplotlib)
│   ├── .env                       # Azure OpenAI credentials (SECRET!)
│   ├── requirements.txt           # Python dependencies
│   ├── uploads/                   # Temporary uploaded files
│   ├── outputs/                   # Generated Excel files
│   └── library/                   # Saved mapping sets (JSON)
│
├── frontend/                      # Web interface
│   └── index.html                 # Single-page application (HTML + CSS + JS)
│
├── objectives/                    # Standalone objectives-only system
│   ├── backend/                   # Separate Flask server for objectives
│   └── frontend/                  # Separate UI for objectives
│
├── reference_docs/                # Reference files
│   └── NMC_Microbiology_Reference_15.xlsx
│
├── AI_PROMPTS.md                  # All AI prompts documented
├── TECHNICAL_DOCUMENTATION.md     # This file
└── NMC_Microbiology_Reference_15 (1).xlsx  # NMC 15 competencies
```

---

## How to Run the System

### Prerequisites

1. **Python 3.8+** installed
2. **Azure OpenAI API access** (API key, endpoint, deployment name)

### Step 1: Install Dependencies

Open a terminal/command prompt and run:

```bash
cd C:\Users\adeep\Downloads\inpods-audit_cc\backend_v2
pip install -r requirements.txt
```

### Step 2: Configure Azure OpenAI Credentials

Edit the `.env` file in `backend_v2/`:

```
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Step 3: Start the Backend Server

```bash
cd C:\Users\adeep\Downloads\inpods-audit_cc\backend_v2
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5001
 * Debugger is active!
```

### Step 4: Open the Frontend

Open this file in your web browser:
```
C:\Users\adeep\Downloads\inpods-audit_cc\frontend\index.html
```

Or double-click the file in Windows Explorer.

### Step 5: Use the System

1. Select a tool (Map Questions, Rate Mappings, or Generate Insights)
2. Upload your files
3. Select the dimension (Area Topics, Competency, Objective, Skill, or NMC Competency)
4. Click the action button
5. Review results and export

---

## System Flow Diagram

### Tool 1: Map Unmapped Questions

```
User uploads question file + reference file
           │
           v
    ┌──────────────┐
    │   Frontend   │  Sends files via HTTP POST to /api/upload
    └──────┬───────┘
           │
           v
    ┌──────────────┐
    │   Backend    │  Saves files to uploads/ folder
    │   (app.py)   │
    └──────┬───────┘
           │
           v
    ┌──────────────┐
    │ audit_engine │  Reads files, builds prompts
    └──────┬───────┘
           │
           v
    ┌──────────────┐
    │ Azure OpenAI │  Processes questions in batches of 5
    │   (GPT-4)    │  Returns JSON with mappings
    └──────┬───────┘
           │
           v
    ┌──────────────┐
    │   Backend    │  Parses response, builds recommendations list
    └──────┬───────┘
           │
           v
    ┌──────────────┐
    │   Frontend   │  Displays results in table
    │              │  User selects which to accept
    └──────┬───────┘
           │
           v
    User clicks "Save & Download"
           │
           v
    ┌──────────────┐
    │   Backend    │  Saves to library (JSON)
    │              │  Generates Excel file
    └──────────────┘
```

---

## Backend Explained

### app.py - The Web Server

This file creates a web server that listens for requests from the frontend.

**Line-by-line key sections:**

```python
# Lines 1-20: Imports
from flask import Flask, request, jsonify, send_file  # Web framework
from flask_cors import CORS  # Allows frontend to talk to backend
import pandas as pd  # For reading Excel/CSV files
from dotenv import load_dotenv  # Loads .env file

# Lines 21-30: Load configuration
load_dotenv()  # Reads .env file
app = Flask(__name__)  # Creates the web application
CORS(app)  # Enables cross-origin requests (frontend can call backend)

# Lines 31-50: Configure folders
app.config['UPLOAD_FOLDER'] = 'uploads'  # Where uploaded files go
app.config['OUTPUT_FOLDER'] = 'outputs'  # Where generated files go
app.config['LIBRARY_FOLDER'] = 'library'  # Where saved mappings go

# Lines 51-80: Initialize the AI engine
config = {
    'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
    'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
    'api_version': os.getenv('AZURE_OPENAI_API_VERSION'),
    'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT')
}
audit_engine = AuditEngine(config)  # Creates the AI engine instance
```

**API Endpoints (Routes):**

| Endpoint | Method | What It Does |
|----------|--------|--------------|
| `/api/upload` | POST | Receives uploaded files, saves to disk |
| `/api/run-audit-efficient` | POST | Runs Tool 1 (mapping) with batching |
| `/api/rate-mappings` | POST | Runs Tool 2 (rating existing mappings) |
| `/api/generate-insights` | POST | Runs Tool 3 (charts and statistics) |
| `/api/apply-and-save` | POST | Saves results to library + generates Excel |
| `/api/library` | GET | Lists all saved mapping sets |
| `/api/library/<id>` | GET/DELETE | Get or delete a specific mapping set |
| `/api/download/<filename>` | GET | Download a generated file |

---

### audit_engine.py - The AI Brain

This file contains all the logic for talking to Azure OpenAI.

**Key Classes:**

#### AuditEngine Class

```python
class AuditEngine:
    """Main class that handles all AI operations"""

    def __init__(self, config):
        """
        Initializes connection to Azure OpenAI

        config = {
            'api_key': 'your-key',
            'azure_endpoint': 'https://...',
            'api_version': '2024-02-15-preview',
            'deployment': 'gpt-4'
        }
        """
        self.client = AzureOpenAI(...)  # Creates API connection
```

**Key Methods Explained:**

#### 1. `_load_reference_data(reference_file, dimension)`

```python
def _load_reference_data(self, reference_csv, dimension):
    """
    Reads the reference file and extracts the curriculum items.

    For area_topics: Returns {topic_name: subtopics_text}
    For competency/objective/skill/nmc_competency: Returns {ID: {type, description}}

    Example output for nmc_competency:
    {
        'MI1.1': {'type': 'General Microbiology', 'description': 'Describe taxonomy...'},
        'MI1.2': {'type': 'General Microbiology', 'description': 'Describe morphology...'},
        ...
    }
    """
```

#### 2. `_build_mapping_prompt(question_text, reference_data, dimension)`

```python
def _build_mapping_prompt(self, question_text, reference_data, dimension):
    """
    Creates the prompt that gets sent to GPT-4.

    The prompt includes:
    1. Role: "You are a curriculum mapping expert"
    2. The question text
    3. List of available curriculum items
    4. Expected JSON response format
    5. Rules (confidence score 0-1, choose most relevant, etc.)
    """
```

#### 3. `run_audit_batched(question_csv, reference_csv, dimension, batch_size=5)`

```python
def run_audit_batched(self, question_csv, reference_csv, dimension, batch_size=5):
    """
    TOOL 1: Maps questions to curriculum items.

    Process:
    1. Load questions from CSV/Excel
    2. Load reference data
    3. Group questions into batches of 5
    4. For each batch:
       - Build a prompt with all 5 questions
       - Send to GPT-4
       - Parse the JSON response
       - Extract mapping for each question
    5. Return all recommendations

    Why batching? Saves 60-70% on API costs because:
    - The reference list is only sent once per batch
    - Less HTTP overhead
    """
```

#### 4. `rate_existing_mappings(mapped_file, reference_csv, dimension, batch_size=5)`

```python
def rate_existing_mappings(self, mapped_file, reference_csv, dimension, batch_size=5):
    """
    TOOL 2: Evaluates existing mappings.

    Process:
    1. Load file with existing mappings
    2. For each question + its current mapping:
       - Ask GPT-4: "Is this mapping correct?"
       - Get rating: correct / partially_correct / incorrect
       - Get suggested alternative if not correct
    3. Return ratings and recommendations
    """
```

---

### visualization_engine.py - Chart Generator

Creates PNG chart images using matplotlib.

**Key Methods:**

```python
class VisualizationEngine:

    def generate_topic_bar_chart(self, coverage_data):
        """Creates horizontal bar chart showing questions per topic"""

    def generate_percentage_pie_chart(self, coverage_data):
        """Creates donut chart showing distribution"""

    def generate_confidence_histogram(self, confidence_scores):
        """Creates histogram of confidence scores (color-coded)"""

    def generate_gap_analysis_chart(self, coverage_data, reference_topics):
        """Creates chart highlighting gaps (topics with 0 questions)"""

    def generate_summary_dashboard(self, coverage_data, confidence_scores, reference_topics):
        """Creates 2x2 grid with all charts + summary statistics"""
```

---

## Frontend Explained

### index.html - The User Interface

This single file contains HTML (structure), CSS (styling), and JavaScript (behavior).

**Structure Overview:**

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 400+ lines of CSS for styling */
    </style>
</head>
<body>
    <!-- Header -->
    <h1>Inpods Curriculum Mapping</h1>

    <!-- Sidebar: Library of saved mappings -->
    <div class="sidebar">...</div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Tool Selection Cards -->
        <div class="mode-selection">
            <div class="mode-card" onclick="selectMode('A')">Tool 1: Map Questions</div>
            <div class="mode-card" onclick="selectMode('B')">Tool 2: Rate Mappings</div>
            <div class="mode-card" onclick="selectMode('C')">Tool 3: Generate Insights</div>
        </div>

        <!-- Tool A Panel -->
        <div id="panelA">
            <!-- File upload forms -->
            <!-- Dimension dropdown -->
            <!-- Results table -->
        </div>

        <!-- Tool B Panel -->
        <div id="panelB">...</div>

        <!-- Tool C Panel -->
        <div id="panelC">...</div>
    </div>

    <script>
        /* 800+ lines of JavaScript for functionality */
    </script>
</body>
</html>
```

**Key JavaScript Variables:**

```javascript
const API_URL = 'http://localhost:5001/api';  // Backend server address

// Reference dictionaries for showing definitions
const OBJECTIVES_REF = {
    'O1': 'Explain how microorganisms cause human infection',
    'O2': 'Understand commensal, opportunistic and pathogenic organisms',
    // ...
};

const COMPETENCIES_REF = { /* C1-C6 definitions */ };
const SKILLS_REF = { /* S1-S5 definitions */ };
const NMC_COMPETENCIES_REF = {
    'MI1.1': 'Describe the taxonomy and classification of microorganisms',
    'MI1.2': 'Describe the morphology, microbial growth and physiology',
    // ... all 15 NMC competencies
};
```

**Key JavaScript Functions:**

```javascript
// Switches between Tool 1, 2, 3
function selectMode(mode) {
    currentMode = mode;
    // Hide all panels, show selected one
    document.getElementById('panelA').classList.add('hidden');
    document.getElementById('panelB').classList.add('hidden');
    document.getElementById('panelC').classList.add('hidden');
    document.getElementById(`panel${mode}`).classList.remove('hidden');
}

// Tool 1: Upload files and run mapping
async function uploadAndRunAuditA() {
    // 1. Get files from form
    const questionFile = document.getElementById('questionFileA').files[0];
    const referenceFile = document.getElementById('referenceFileA').files[0];
    const dimension = document.getElementById('dimensionA').value;

    // 2. Upload files to backend
    const formData = new FormData();
    formData.append('question_file', questionFile);
    formData.append('reference_file', referenceFile);

    const uploadResponse = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
    });

    // 3. Run the audit
    const auditResponse = await fetch(`${API_URL}/run-audit-efficient`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_file: uploadData.question_file,
            reference_file: uploadData.reference_file,
            dimension: dimension,
            batch_size: 5
        })
    });

    // 4. Display results
    const data = await auditResponse.json();
    displayResultsA(data.recommendations);
}

// Display results in a table
function displayResultsA(recommendations) {
    let html = '<table class="recommendations-table">';
    html += '<tr><th>Select</th><th>Question</th><th>Mapping</th><th>Confidence</th></tr>';

    for (const rec of recommendations) {
        html += `<tr>
            <td><input type="checkbox" checked></td>
            <td>${rec.question_text}</td>
            <td>${rec.recommended_mapping}<br><small>${getMappingDefinition(rec.mapped_id)}</small></td>
            <td>${Math.round(rec.confidence * 100)}%</td>
        </tr>`;
    }

    html += '</table>';
    document.getElementById('resultsTableA').innerHTML = html;
}

// Get human-readable definition for any ID
function getMappingDefinition(mappingId) {
    if (OBJECTIVES_REF[mappingId]) return OBJECTIVES_REF[mappingId];
    if (COMPETENCIES_REF[mappingId]) return COMPETENCIES_REF[mappingId];
    if (SKILLS_REF[mappingId]) return SKILLS_REF[mappingId];
    if (NMC_COMPETENCIES_REF[mappingId]) return NMC_COMPETENCIES_REF[mappingId];
    return '';
}
```

---

## The 3 Tools

### Tool 1: Map Unmapped Questions

**Purpose:** Take questions that don't have curriculum mappings and assign them.

**Input:**
- Question file (CSV/Excel with "Question Number" and "Question Text" columns)
- Reference file (curriculum standards)
- Dimension (what to map to)

**Output:**
- List of recommendations (question → suggested mapping + confidence + justification)

**How it works:**
1. Questions are grouped into batches of 5
2. Each batch is sent to GPT-4 with the reference list
3. GPT-4 returns JSON with mappings for all 5 questions
4. User reviews and selects which to accept
5. Accepted mappings are saved to library and exported to Excel

---

### Tool 2: Rate Existing Mappings

**Purpose:** Check if existing mappings are correct.

**Input:**
- File with questions AND existing mappings
- Reference file
- Dimension

**Output:**
- Rating for each mapping (correct / partially_correct / incorrect)
- Suggested alternatives for incorrect mappings

**How it works:**
1. Questions + their current mappings are sent to GPT-4
2. GPT-4 evaluates each: "Is this mapping appropriate?"
3. Returns rating + suggestion if not correct
4. User can accept suggestions for incorrect mappings

---

### Tool 3: Generate Insights

**Purpose:** Visualize coverage and identify gaps.

**Input:**
- File with mapped questions

**Output:**
- Coverage summary table
- Bar chart (questions per topic)
- Pie chart (distribution)
- Confidence histogram
- Gap analysis chart
- Summary dashboard

**How it works:**
1. Reads the mapped file
2. Counts questions per topic/competency
3. Calculates confidence statistics
4. Generates PNG charts using matplotlib
5. Displays in browser

---

## Supported Dimensions

### 1. Area Topics
- **Format:** Topic name strings (e.g., "Immunology", "Bacteriology")
- **Reference file:** NMC OER Mapping CSV with Topic Area and Subtopics columns
- **Use case:** Mapping to broad curriculum areas

### 2. Competency (C1-C6)
- **Format:** C1, C2, C3, C4, C5, C6
- **Reference file:** Reference sheet with ID and Description columns
- **Use case:** Mapping to learning competencies

### 3. Objective (O1-O6)
- **Format:** O1, O2, O3, O4, O5, O6
- **Reference file:** Reference sheet with ID and Description columns
- **Use case:** Mapping to learning objectives

### 4. Skill (S1-S5)
- **Format:** S1, S2, S3, S4, S5
- **Reference file:** Reference sheet with ID and Description columns
- **Use case:** Mapping to practical skills

### 5. NMC Competency (MI1.1-MI3.5)
- **Format:** MI1.1, MI1.2, ... MI3.5 (15 total)
- **Reference file:** NMC_Microbiology_Reference_15.xlsx
- **Categories:**
  - MI1.x: General Microbiology (6 items)
  - MI2.x: Immunology (4 items)
  - MI3.x: Systemic Microbiology (5 items)
- **Use case:** Mapping to National Medical Council competencies

---

## File-by-File Explanation

### backend_v2/app.py

| Lines | What It Does |
|-------|--------------|
| 1-20 | Import required libraries |
| 21-50 | Configure Flask app and folders |
| 51-80 | Initialize Azure OpenAI connection |
| 81-120 | `/api/upload` - Handle file uploads |
| 121-180 | `/api/run-audit` - Single question mapping |
| 181-225 | `/api/run-audit-efficient` - Batch mapping |
| 226-280 | `/api/apply-and-save` - Save results |
| 281-350 | `/api/rate-mappings` - Tool 2 endpoint |
| 351-450 | `/api/library` endpoints - CRUD operations |
| 451-550 | `/api/generate-insights` - Tool 3 endpoint |
| 551-600 | `/api/download` - File downloads |
| 601-620 | Main entry point (starts server) |

### backend_v2/audit_engine.py

| Lines | What It Does |
|-------|--------------|
| 1-60 | AuditEngine class initialization |
| 61-80 | `test_connection()` - Verify Azure connection |
| 79-145 | `_load_reference_data()` - Parse reference files |
| 146-202 | `_build_mapping_prompt()` - Single question prompt |
| 203-290 | `_build_batch_prompt()` - Batch prompt |
| 291-326 | `_call_llm()` - Send request to Azure OpenAI |
| 327-413 | `run_audit()` - Single question mapping |
| 414-563 | `run_audit_batched()` - Batch mapping (Tool 1) |
| 564-611 | `apply_and_export()` - Generate Excel output |
| 612-702 | `_build_batch_rating_prompt()` - Rating prompt |
| 703-862 | `rate_existing_mappings()` - Tool 2 main function |
| 863-1028 | LibraryManager class - Save/load mapping sets |

### backend_v2/visualization_engine.py

| Lines | What It Does |
|-------|--------------|
| 1-30 | Setup matplotlib, define colors |
| 31-70 | `generate_topic_bar_chart()` |
| 71-110 | `generate_percentage_pie_chart()` |
| 111-175 | `generate_confidence_histogram()` |
| 176-240 | `generate_gap_analysis_chart()` |
| 241-325 | `generate_summary_dashboard()` |
| 326-355 | `generate_all_insights()` |

### frontend/index.html

| Lines | What It Does |
|-------|--------------|
| 1-10 | HTML document setup |
| 11-400 | CSS styles (colors, layout, tables, buttons) |
| 401-600 | Tool selection cards HTML |
| 601-700 | Tool A (Map Questions) form HTML |
| 701-800 | Tool B (Rate Mappings) form HTML |
| 801-860 | Tool C (Generate Insights) form HTML |
| 861-920 | JavaScript: API URL and reference dictionaries |
| 921-1000 | JavaScript: Mode selection and status display |
| 1001-1200 | JavaScript: Tool A functions |
| 1201-1400 | JavaScript: Tool B functions |
| 1401-1600 | JavaScript: Tool C functions |
| 1601-1700 | JavaScript: Library management functions |

---

## Troubleshooting

### "Network Error" when clicking any button

**Cause:** Backend server is not running.

**Fix:**
```bash
cd C:\Users\adeep\Downloads\inpods-audit_cc\backend_v2
python app.py
```

### "500 Internal Server Error"

**Cause:** Usually a problem with file format or missing columns.

**Fix:**
- Check that your question file has "Question Number" and "Question Text" columns
- Check that your reference file matches the expected format for the dimension

### Charts are empty or show errors

**Cause:** Division by zero (no mapped questions found).

**Fix:** Make sure your file has mapping columns (mapped_topic, mapped_objective, etc.)

### "API Key Invalid" error

**Cause:** Azure OpenAI credentials not configured.

**Fix:** Edit `backend_v2/.env` with your correct credentials.

### Download button doesn't work

**Cause:** Browser blocking the download or wrong URL.

**Fix:**
- Check browser's download permissions
- Make sure backend is running on port 5001

---

## Quick Reference Card

### Start the System
```bash
cd C:\Users\adeep\Downloads\inpods-audit_cc\backend_v2
python app.py
# Then open frontend/index.html in browser
```

### File Requirements

**Question File:**
- Columns: "Question Number", "Question Text"
- Format: CSV or Excel

**Reference File:**
- For Area Topics: "Topic Area", "Subtopics Covered"
- For C/O/S: "ID", "Description"
- For NMC: "ID", "Category", "Description"
- Format: CSV or Excel

### Ports
- Backend: http://localhost:5001
- Frontend: Opens directly from file

---

*Document created: January 2026*
*System Version: 2.0*

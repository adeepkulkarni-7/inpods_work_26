# Inpods Curriculum Mapping Audit System V2

AI-powered system for mapping exam questions to curriculum dimensions using Azure OpenAI.

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.9+** installed
2. **Azure OpenAI API access** with a deployed model (GPT-4o-mini recommended)
3. A modern web browser (Chrome, Firefox, Edge)

---

## Setup Instructions (First Time)

### Step 1: Download and Extract

```
Download ZIP from GitHub → Extract to any folder
```

### Step 2: Install Python Dependencies

Open a terminal/command prompt in the project folder:

```bash
cd backend_v2
pip install -r requirements.txt
```

**If you get NumPy errors:**
```bash
pip install "numpy<2"
```

### Step 3: Configure Azure OpenAI Credentials

1. Copy the example environment file:
   ```bash
   cd backend_v2
   cp .env.example .env
   ```

2. Edit `.env` with your Azure credentials:
   ```
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

---

## Running the Application

You need **TWO terminal windows** open:

### Terminal 1: Start Backend Server

```bash
cd backend_v2
python app.py
```

You should see:
```
[*] Initializing Inpods Audit Engine V2...
[OK] Connection Status: Connected
[OK] Azure OpenAI connected successfully
==================================================
[*] Backend running on http://localhost:5001
==================================================
```

### Terminal 2: Start Frontend Server

```bash
cd inpods-audit_cc
python -m http.server 8002
```

You should see:
```
Serving HTTP on :: port 8002 (http://[::]:8002/) ...
```

---

## Accessing the Applications

Open your browser to these URLs:

| Application | URL | Description |
|-------------|-----|-------------|
| **Launcher** | http://localhost:8002/ | Main menu with links to all apps |
| **Mode A - Mapping** | http://localhost:8002/app_mapping/ | Map unmapped questions |
| **Mode B - Validation** | http://localhost:8002/app_rating/ | Validate existing mappings |
| **Mode C - Insights** | http://localhost:8002/app_insights/ | Generate charts |
| **Chat Agent** | http://localhost:8002/agent_v2/ | Conversational interface |

---

## Testing Each Application

### Test Files Location

Sample test files are in the root folder:
- `test_10_questions_unmapped.csv` - 10 unmapped questions
- `test_reference_simple.csv` - Simple reference with competencies

Or use the files in `backend_v2/uploads/`:
- `media_questions_unmapped.csv` - Unmapped questions
- `media_questions_mapped.csv` - Pre-mapped questions
- `media_reference.csv` - Reference file

---

### Test 1: Mode A - Question Mapping

**URL:** http://localhost:8002/app_mapping/

**Purpose:** Map unmapped questions to curriculum dimensions

**Steps:**
1. Open http://localhost:8002/app_mapping/
2. Click "Choose File" under **Question Bank** → Select `test_10_questions_unmapped.csv`
3. Click "Choose File" under **Reference Sheet** → Select `test_reference_simple.csv`
4. Check **Competency** dimension
5. Check **Enable Efficient Mode** (faster processing)
6. Click **Upload & Preview**
7. Review the file overview that appears
8. Click **Run Audit**
9. Wait for mapping to complete (watch progress bar)
10. Review recommendations with confidence scores
11. Click checkboxes to select mappings (or "Select All")
12. Click **Save & Download**
13. Excel file downloads with mappings applied

**Expected Output:**
- Recommendations table with columns: Question, Recommended Mapping, Confidence
- Confidence scores between 0-100%
- Downloaded Excel with `mapped_competency` column filled

---

### Test 2: Mode B - Mapping Validation

**URL:** http://localhost:8002/app_rating/

**Purpose:** Validate accuracy of existing mappings

**Steps:**
1. Open http://localhost:8002/app_rating/
2. Click "Choose File" under **Mapped Questions** → Select the Excel from Test 1 (or `media_questions_mapped.csv`)
3. Click "Choose File" under **Reference Sheet** → Select `test_reference_simple.csv`
4. Check **Competency** dimension
5. Click **Upload & Analyze**
6. Wait for validation to complete
7. Review results:
   - Green rows = Correct mappings
   - Yellow rows = Partially correct
   - Red rows = Incorrect (with suggested fix)
8. Click checkboxes on incorrect items
9. Click **Save & Download Corrections**
10. Excel downloads with corrections applied

**Expected Output:**
- Summary showing: X Correct, Y Partial, Z Incorrect
- Color-coded table with ratings
- Downloaded Excel with corrections

---

### Test 3: Mode C - Insights & Charts

**URL:** http://localhost:8002/app_insights/

**Purpose:** Generate visual analytics from mapped data

**Steps:**
1. Open http://localhost:8002/app_insights/
2. Click "Choose File" under **Mapped Questions** → Select the Excel from Test 1 or 2
3. Optionally upload Reference Sheet for gap analysis
4. Click **Generate Insights**
5. Wait for charts to generate
6. View:
   - Executive Summary dashboard
   - Confidence distribution chart
   - Coverage charts per dimension
   - Gap analysis (if reference provided)
7. Click **Start Over** to try again

**Expected Output:**
- Multiple PNG charts displayed
- Coverage percentages per dimension
- Visual confidence distribution

---

### Test 4: Chat Agent (All-in-One)

**URL:** http://localhost:8002/agent_v2/

**Purpose:** Guided conversational workflow through all modes

**Steps:**
1. Open http://localhost:8002/agent_v2/
2. Agent greets you and asks for question file
3. Click the upload area → Select `test_10_questions_unmapped.csv`
4. Agent asks for reference file
5. Click the upload area → Select `test_reference_simple.csv`
6. Agent shows file overview (question count, detected dimensions)
7. Click **Map to Competency** button
8. Wait for mapping to complete
9. Agent shows results (X mapped, Y% avg confidence)
10. Choose next action:
    - **Save & Download** → Downloads Excel
    - **Validate Mappings** → Runs Mode B on new mappings
    - **Generate Charts** → Creates visualizations
11. Click **Start Over** to reset

**Expected Output:**
- Conversational flow through entire workflow
- Same results as individual apps
- Seamless chaining between modes

---

## Folder Structure

```
inpods-audit_cc/
├── backend_v2/                 # Flask API server (Python)
│   ├── app.py                  # Main server - run this
│   ├── audit_engine.py         # Mapping/rating logic
│   ├── visualization_engine.py # Chart generation
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Your Azure credentials (create this)
│   ├── .env.example            # Template for credentials
│   ├── uploads/                # Uploaded files stored here
│   └── outputs/                # Generated Excel & charts
│
├── app_mapping/                # Mode A standalone app
├── app_rating/                 # Mode B standalone app
├── app_insights/               # Mode C standalone app
├── agent_v2/                   # Conversational agent
├── shared/                     # Shared CSS/JS components
├── frontend_v2/                # Combined app (all modes)
│
├── index.html                  # Launcher page
├── README.md                   # This file
├── PIPELINE_DOCUMENTATION.md   # Technical documentation
│
└── test_*.csv                  # Sample test files
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection Failed" on startup | Check your `.env` file has correct Azure credentials |
| Backend won't start | Make sure port 5001 is free. Kill other Python processes |
| Frontend shows "Failed to fetch" | Backend isn't running. Start it first (Terminal 1) |
| Charts show 0% | Mapping columns might be wrong. Try remapping with latest version |
| NumPy errors | Run `pip install "numpy<2"` |
| Port already in use | Change port: `python -m http.server 8003` |

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/upload` | POST | Upload question + reference files |
| `/api/upload-mapped` | POST | Upload pre-mapped file |
| `/api/run-audit-efficient` | POST | Map questions (batched) |
| `/api/rate-mappings` | POST | Validate existing mappings |
| `/api/generate-insights` | POST | Generate charts |
| `/api/apply-and-save` | POST | Save mappings + download |
| `/api/download/<file>` | GET | Download generated file |

---

## Quick Reference Card

```
START SERVERS:
  Terminal 1: cd backend_v2 && python app.py
  Terminal 2: cd inpods-audit_cc && python -m http.server 8002

OPEN APPS:
  Launcher:   http://localhost:8002/
  Mapping:    http://localhost:8002/app_mapping/
  Validation: http://localhost:8002/app_rating/
  Insights:   http://localhost:8002/app_insights/
  Agent:      http://localhost:8002/agent_v2/

STOP SERVERS:
  Press Ctrl+C in each terminal
```

---

## License

Internal use only - Inpods.ai

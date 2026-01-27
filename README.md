# Inpods Curriculum Mapping Audit System

A web-based system that uses Azure OpenAI to map medical education exam questions to curriculum topics, rate existing mappings, and generate visual insights.

---

## Quick Start

### 1. Install Dependencies (first time only)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Azure Credentials (first time only)

```bash
cd backend
cp .env.example .env
# Edit .env with your Azure OpenAI credentials:
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Run the Application

**Option A: Use start script (Windows)**
```bash
cd inpods-audit_cc
start.bat
```

**Option B: Manual start**
```bash
# Terminal 1: Start backend (port 5000)
cd backend
python app.py

# Terminal 2: Start frontend (port 8000)
cd frontend
python -m http.server 8000
```

### 4. Open Browser

Go to: **http://localhost:8000**

---

## Three Modes

| Mode | Purpose | Input Files | Output |
|------|---------|-------------|--------|
| **A** | Map Unmapped Questions | Questions CSV + Reference CSV | Excel with mappings |
| **B** | Rate Existing Mappings | Pre-mapped file + Reference CSV | Ratings + corrected Excel |
| **C** | Generate Insights | Pre-mapped file | Visual charts (PNG) |

---

### Mode A: Map Unmapped Questions

**Use when:** You have questions without curriculum mappings and need AI to recommend them.

**Steps:**
1. Click "Mode A" card
2. Upload Question Bank CSV (unmapped)
3. Upload Reference Sheet CSV
4. Select dimension (Area Topics / Competency / Objective / Skill)
5. Enable "Efficient Mode" for faster processing
6. Click "Upload & Run Audit"
7. Review recommendations with confidence scores
8. Select mappings to accept
9. Click "Apply Selected Mappings" to download Excel

**Test files:**
- Questions: `RamaiaMicroExamCSV_CLEANED (1).csv`
- Reference: `NMC_OER_Mapping (3).csv`

---

### Mode B: Rate Existing Mappings

**Use when:** You have questions already mapped and want AI to evaluate/correct them.

**Steps:**
1. Click "Mode B" card
2. Upload Mapped Questions file (.csv, .xlsx, .ods)
3. Upload Reference Sheet CSV
4. Select dimension
5. Click "Upload & Rate Mappings"
6. Review ratings (Correct / Partially Correct / Incorrect)
7. Select incorrect mappings to update
8. Click "Apply Selected Updates" to download corrected Excel

**Test files:**
- Mapped file: `Microbiology_OER_Audit_Results.xlsx.ods`
- Reference: `NMC_OER_Mapping (3).csv`

---

### Mode C: Generate Insights

**Use when:** You want visual reports of mapping distribution and coverage for stakeholders.

**Steps:**
1. Click "Mode C" card
2. Upload Mapped Questions file
3. Optionally upload Reference Sheet (for gap analysis)
4. Click "Generate Insights"
5. View generated charts:
   - Summary Dashboard
   - Topic Distribution Bar Chart
   - Percentage Pie Chart
   - Confidence Histogram
   - Gap Analysis Chart

**Test files:**
- Mapped file: `Microbiology_OER_Audit_Results.xlsx.ods`
- Reference: `NMC_OER_Mapping (3).csv`

---

## Project Structure

```
inpods-audit_cc/
├── backend/
│   ├── app.py                  # Flask API server (main entry point)
│   ├── audit_engine.py         # Core mapping & rating logic
│   ├── visualization_engine.py # Chart generation (matplotlib)
│   ├── test_audit_engine.py    # Test suite (16 tests)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Azure credentials (create this)
│   ├── .env.example            # Template for credentials
│   ├── uploads/                # Uploaded files stored here
│   └── outputs/                # Generated Excel & charts
│       └── insights/           # Generated PNG charts
├── frontend/
│   └── index.html              # Web UI (single file, no framework)
├── start.bat                   # Windows startup script
├── start.sh                    # Unix/Mac startup script
├── README.md                   # This file
├── API_REFERENCE.md            # Full API documentation
├── DOCUMENTATION.md            # Detailed system documentation
│
│ # Test/Sample Data Files:
├── RamaiaMicroExamCSV_CLEANED (1).csv      # 46 unmapped questions
├── NMC_OER_Mapping (3).csv                 # 7 topic areas reference
├── reference_sheet_microbiology (1).csv    # C/O/S codes reference
└── Microbiology_OER_Audit_Results.xlsx.ods # 44 pre-mapped questions
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Batching** | Processes 5 questions per API call (60-70% cost savings) |
| **Stem Filtering** | Automatically skips stem questions (e.g., "1 (Stem)") |
| **Multi-dimension** | Supports Topics, Competencies, Objectives, Skills |
| **Confidence Scores** | 0-1 score for each mapping recommendation |
| **Justifications** | AI explains why each mapping was chosen |
| **Visual Insights** | PNG charts for non-technical stakeholders |
| **Rating System** | Evaluate existing mappings for accuracy |

---

## API Endpoints

| Endpoint | Method | Mode | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | All | Health check |
| `/api/upload` | POST | A | Upload unmapped files |
| `/api/upload-mapped` | POST | B, C | Upload pre-mapped files |
| `/api/run-audit` | POST | A | Run audit (single mode) |
| `/api/run-audit-efficient` | POST | A | Run audit (batched) |
| `/api/rate-mappings` | POST | B | Rate existing mappings |
| `/api/generate-insights` | POST | C | Generate charts |
| `/api/apply-changes` | POST | A, B | Apply & export Excel |
| `/api/download/{file}` | GET | A, B | Download Excel file |
| `/api/insights/{file}` | GET | C | Download chart image |

See `API_REFERENCE.md` for complete documentation.

---

## Running Tests

```bash
cd backend

# Run all unit tests (16 tests)
python -m pytest test_audit_engine.py -v

# Run live validation (requires Azure credentials)
python test_audit_engine.py --live
```

---

## Environment Variables

Create `backend/.env` with:

```
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Requirements

- Python 3.9+
- Azure OpenAI API access
- Modern web browser (Chrome, Firefox, Edge)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection Failed" | Check .env credentials are correct |
| NumPy error | Run `pip install "numpy<2"` |
| Port 5000 in use | Kill other Python processes or change port |
| Charts not loading | Check `outputs/insights/` folder exists |
| Empty recommendations | Verify CSV has correct column names |

---

## License

Internal use only - Inpods.ai

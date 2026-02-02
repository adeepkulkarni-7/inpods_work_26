# Inpods Audit Engine - Complete Pipeline Documentation

## System Overview

The Inpods Audit Engine is a curriculum mapping system that maps exam questions to curriculum dimensions (competencies, objectives, skills, Blooms taxonomy, etc.) using Azure OpenAI.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INPODS AUDIT SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│   │  Individual  │     │   Agent V2   │     │  Backend V2  │           │
│   │    Apps      │     │  (Chat UI)   │     │  (Flask API) │           │
│   │              │     │              │     │              │           │
│   │ • app_mapping│     │ State Machine│     │ • Audit      │           │
│   │ • app_rating │◄───►│ Conversation │◄───►│   Engine     │           │
│   │ • app_insights     │ Flow         │     │ • Viz Engine │           │
│   │              │     │              │     │ • Library    │           │
│   └──────────────┘     └──────────────┘     └──────────────┘           │
│         ▲                    ▲                    ▲                     │
│         │                    │                    │                     │
│         └────────────────────┴────────────────────┘                     │
│                              │                                          │
│                    ┌─────────▼─────────┐                               │
│                    │   Azure OpenAI    │                               │
│                    │   GPT-4o-mini     │                               │
│                    └───────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Backend V2 (`backend_v2/`)

**Main Server:** `app.py` (Flask, port 5001)

| File | Purpose |
|------|---------|
| `app.py` | REST API endpoints, request routing |
| `audit_engine.py` | Core mapping/rating logic, LLM calls |
| `visualization_engine.py` | Chart generation (matplotlib) |
| `library_manager.py` | Save/load mapping results |

### 2. Individual Apps (`app_mapping/`, `app_rating/`, `app_insights/`)

Three standalone single-page applications:

| App | Purpose | Port |
|-----|---------|------|
| `app_mapping/` | Mode A - Map unmapped questions | 8002 |
| `app_rating/` | Mode B - Validate existing mappings | 8002 |
| `app_insights/` | Mode C - Generate visualizations | 8002 |

### 3. Conversational Agent (`agent_v2/`)

Chat-based interface that guides users through the entire workflow.

| File | Purpose |
|------|---------|
| `agent.js` | State machine, conversation flow |
| `api-client.js` | Backend API wrapper |
| `agent.css` | Chat UI styles |

### 4. Shared Components (`shared/`)

| File | Purpose |
|------|---------|
| `common.css` | Global styles |
| `task-manager.js` | Async task tracking |
| `utils.js` | API URL, helper functions |

---

## Data Flow Pipelines

### Pipeline A: Question Mapping (Unmapped → Mapped)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. UPLOAD       │     │ 2. ANALYZE      │     │ 3. MAP          │
│                 │     │                 │     │                 │
│ questions.csv   │────►│ Detect columns  │────►│ LLM batches     │
│ reference.csv   │     │ Count questions │     │ (5 at a time)   │
│                 │     │ Extract dims    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 4. REVIEW       │     │ 5. SAVE         │     │ 6. EXPORT       │
│                 │     │                 │     │                 │
│ Recommendations │────►│ Library entry   │────►│ Excel download  │
│ Confidence %    │     │ CSV copy        │     │ + CSV for chain │
│ Select items    │     │ (for chaining)  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**API Endpoints:**
1. `POST /api/upload` - Upload files, get metadata
2. `POST /api/run-audit-efficient` - Run batched mapping
3. `POST /api/apply-and-save` - Save & export (creates CSV for chaining)

**Column Output:**
```
Question Number | Question Text | mapped_competency | confidence_score | justification
```

---

### Pipeline B: Mapping Validation (Mapped → Validated)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. UPLOAD       │     │ 2. DETECT       │     │ 3. RATE         │
│                 │     │                 │     │                 │
│ mapped.csv      │────►│ Find mapped_*   │────►│ LLM validates   │
│ reference.csv   │     │ columns         │     │ each mapping    │
│                 │     │ Auto-detect dims│     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 4. RESULTS      │     │ 5. CORRECT      │     │ 6. EXPORT       │
│                 │     │                 │     │                 │
│ Correct: 38     │────►│ Select wrong    │────►│ Corrected Excel │
│ Partial: 5      │     │ Apply fixes     │     │ + CSV for chain │
│ Incorrect: 3    │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**API Endpoints:**
1. `POST /api/upload-mapped` - Upload mapped file
2. `POST /api/rate-mappings` - Validate each mapping
3. `POST /api/apply-corrections-and-save` - Save corrections

**Rating Categories:**
- `correct` - Mapping is accurate
- `partially_correct` - Close but could be better
- `incorrect` - Wrong mapping, needs correction

---

### Pipeline C: Insights Generation (Mapped → Visualizations)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. UPLOAD       │     │ 2. ANALYZE      │     │ 3. GENERATE     │
│                 │     │                 │     │                 │
│ mapped.csv      │────►│ Count coverage  │────►│ Create charts   │
│ reference.csv   │     │ Find gaps       │     │ Per dimension   │
│ (optional)      │     │ Calc confidence │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DISPLAY                                                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Confidence   │  │ Coverage     │  │ Gap Analysis │           │
│  │ Distribution │  │ Heatmap      │  │ Table        │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Questions    │  │ Executive    │                             │
│  │ per Topic    │  │ Summary      │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

**API Endpoints:**
1. `POST /api/upload-mapped` - Upload mapped file
2. `POST /api/generate-insights` - Generate all charts

**Charts Generated:**
- `confidence_distribution.png` - Histogram of confidence scores
- `{dimension}_coverage.png` - Bar chart per dimension
- `coverage_heatmap.png` - Heatmap of all dimensions
- `executive_summary.png` - Overview dashboard

---

## Agent State Machine

```
                    ┌──────────────┐
                    │     IDLE     │
                    └──────┬───────┘
                           │ User starts
                           ▼
              ┌────────────────────────┐
              │  AWAIT_QUESTION_FILE   │
              └───────────┬────────────┘
                          │ File uploaded
                          ▼
              ┌────────────────────────┐
              │  AWAIT_REFERENCE_FILE  │
              └───────────┬────────────┘
                          │ File uploaded
                          ▼
                    ┌──────────────┐
                    │  ANALYZING   │
                    └──────┬───────┘
                           │ Analysis done
                           ▼
                   ┌───────────────┐
                   │ SHOW_OVERVIEW │
                   └───────┬───────┘
                           │ User confirms
                           ▼
                   ┌───────────────┐
                   │ AWAIT_ACTION  │◄─────────────┐
                   └───────┬───────┘              │
                           │ Action selected      │
                           ▼                      │
                   ┌───────────────┐              │
                   │  PROCESSING   │              │
                   └───────┬───────┘              │
                           │ Complete             │
                           ▼                      │
                   ┌───────────────┐              │
                   │ SHOW_RESULTS  │──────────────┘
                   └───────┬───────┘   (continue)
                           │ Save/Complete
                           ▼
                    ┌──────────────┐
                    │   COMPLETE   │
                    └──────────────┘
```

**Agent Actions:**
- `map_competency` - Map to single dimension
- `map_multiple` - Map to multiple dimensions
- `validate` - Validate existing mappings
- `validate_new` - Validate freshly mapped results
- `insights` - Generate charts
- `save` - Save & download Excel
- `visualize` - Generate charts (after mapping)
- `start_over` - Reset and start fresh

---

## Chaining Operations (Agent Flow)

The agent supports chaining operations by saving intermediate CSV files:

```
Mode A (Map)
    │
    ├──► Save & Download ──► mapped_*.csv created
    │                              │
    │                              ├──► Mode B (Validate)
    │                              │         │
    │                              │         └──► Save Corrections ──► corrected_*.csv
    │                              │                                         │
    │                              │                                         └──► Mode C (Charts)
    │                              │
    │                              └──► Mode C (Charts directly)
    │
    └──► Validate Mappings (validate_new)
              │
              └──► Saves first, then validates
```

**Key Implementation:**
- `apply-and-save` endpoint now saves BOTH Excel (download) AND CSV (for chaining)
- `saved_file` returned in response contains CSV filename
- Agent stores `savedMappedFile` for subsequent operations

---

## Dimension Types

| Dimension | Column Name | Example Values |
|-----------|-------------|----------------|
| `competency` | `mapped_competency` | C1, C2, C3, C4, C5, C6 |
| `objective` | `mapped_objective` | O1.1, O2.3, O3.5 |
| `skill` | `mapped_skill` | S1, S2, S3, S4, S5 |
| `nmc_competency` | `mapped_nmc_competency` | MI1, MI2, MI3 |
| `area_topics` | `mapped_topic`, `mapped_subtopic` | Microbiology/Bacteria |
| `blooms` | `mapped_blooms` | KL1-KL6 (Remember-Create) |
| `complexity` | `mapped_complexity` | Easy, Medium, Hard |

---

## File Structure

```
inpods-audit_cc/
├── backend_v2/                 # Flask API server
│   ├── app.py                  # Main API routes
│   ├── audit_engine.py         # Mapping/rating logic
│   ├── visualization_engine.py # Chart generation
│   ├── library_manager.py      # Save/load results
│   ├── uploads/                # Uploaded files
│   ├── outputs/                # Generated Excel/charts
│   └── library/                # Saved mapping results
│
├── app_mapping/                # Mode A standalone app
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── app_rating/                 # Mode B standalone app
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── app_insights/               # Mode C standalone app
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── agent_v2/                   # Conversational agent
│   ├── index.html              # Demo page
│   ├── agent.js                # State machine logic
│   ├── agent.css               # Chat UI styles
│   ├── api-client.js           # API wrapper
│   └── tests/                  # Test suite
│       ├── agent.test.js       # 17 test cases
│       └── test-runner.html    # Browser runner
│
├── shared/                     # Shared components
│   ├── common.css              # Global styles
│   ├── task-manager.js         # Async tracking
│   └── utils.js                # Helpers
│
├── frontend_v2/                # Combined app (reference)
│   └── index.html
│
└── index.html                  # Launcher page
```

---

## API Reference

### Upload Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/upload` | POST | `question_file`, `reference_file` | File metadata |
| `/api/upload-mapped` | POST | `mapped_file`, `reference_file` | Mapped metadata |

### Processing Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/run-audit-efficient` | POST | `question_file`, `reference_file`, `dimensions`, `batch_size` | Recommendations |
| `/api/rate-mappings` | POST | `mapped_file`, `reference_file`, `dimensions`, `batch_size` | Ratings + corrections |
| `/api/generate-insights` | POST | `mapped_file`, `reference_file`, `dimensions` | Chart URLs |

### Save Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/apply-and-save` | POST | `question_file`, `recommendations`, `selected_indices`, `dimensions`, `name` | `download_url`, `saved_file` |
| `/api/apply-corrections-and-save` | POST | `mapped_file`, `recommendations`, `selected_indices`, `dimensions`, `name` | `download_url`, `saved_file` |

### Utility Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/download/<filename>` | GET | filename | Binary file |
| `/api/health` | GET | - | Status |
| `/api/library` | GET | - | Saved items list |

---

## Running the System

### Start Backend
```bash
cd backend_v2
python app.py
# Running on http://localhost:5001
```

### Start Frontend Server
```bash
cd inpods-audit_cc
python -m http.server 8002
# Serving on http://localhost:8002
```

### Access Points
- **Launcher:** http://localhost:8002/
- **Mode A (Mapping):** http://localhost:8002/app_mapping/
- **Mode B (Rating):** http://localhost:8002/app_rating/
- **Mode C (Insights):** http://localhost:8002/app_insights/
- **Agent Chat:** http://localhost:8002/agent_v2/
- **Combined App:** http://localhost:8002/frontend_v2/

### Run Tests
```bash
cd agent_v2
node tests/agent.test.js
# Or open http://localhost:8002/agent_v2/tests/test-runner.html
```

---

## Troubleshooting

### Charts Show 0%
- **Cause:** Mapped file has `mapped_id` column instead of `mapped_competency`
- **Fix:** System now handles `mapped_id` as fallback and properly renames columns

### Validation After Mapping Fails
- **Cause:** No mapped CSV file exists for validation endpoint
- **Fix:** `validate_new` action saves mappings first, then validates

### LLM Timeout
- **Cause:** Large batches or network issues
- **Fix:** Reduce `batch_size` parameter (default: 5)

### Missing Dimensions
- **Cause:** Reference file doesn't have required columns
- **Fix:** Ensure reference has dimension-specific columns (competency_id, objective_id, etc.)

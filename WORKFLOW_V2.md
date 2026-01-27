# Inpods Curriculum Mapping - V2 Workflow Documentation

## Overview

V2 of the Inpods Curriculum Mapping Audit System runs parallel to V1 with improvements for better usability, full question text preservation, combined save/download functionality, and architecture prepared for future AI agent integration.

**Status:** Fully functional and tested (as of 2026-01-23)

---

## V2 Changes Summary

| Feature | V1 Behavior | V2 Behavior |
|---------|-------------|-------------|
| Question text | Truncated to 100 chars | **Full text preserved** |
| Save/Download | Separate actions | **Combined: saves to library AND downloads** |
| Start Over | Varied behavior | **Resets form within same mode** |
| Library | Sidebar list | **Enhanced with mode badges (A/B)** |
| API design | Standard REST | **Tool-ready with clear contracts** |
| Ports | 5000/8000 | **5001/8001** |

---

## Quick Start

### Prerequisites
- Python 3.8+
- Azure OpenAI API credentials

### Setup

1. **Copy credentials:**
   ```bash
   copy backend\.env backend_v2\.env
   ```

2. **Install dependencies (if needed):**
   ```bash
   cd backend_v2
   pip install -r requirements.txt
   ```

3. **Start V2:**
   ```bash
   # Option A: Use start script (Windows)
   start_v2.bat

   # Option B: Manual start
   # Terminal 1:
   cd backend_v2
   python app.py

   # Terminal 2:
   cd frontend_v2
   python -m http.server 8001
   ```

4. **Open browser:**
   ```
   http://localhost:8001
   ```

### Running Both Versions

V1 and V2 can run simultaneously:
- **V1:** http://localhost:8000 (backend: 5000)
- **V2:** http://localhost:8001 (backend: 5001)

---

## Supported Dimensions

Currently supported:
- **Area Topics** (Topic / Subtopic) - Primary mapping dimension
- **Competency** (C1-C6)
- **Objective** (O1-O6)
- **Skill** (S1-S5)

Planned additions:
- **Course Outcomes (CO)** - CO definitions mapping
- **KLS (Knowledge, Learning, Skills)** - KLS framework mapping
- **Skills Objectives** - Detailed skills objective mapping

---

## User Workflows

### Mode A: Map Unmapped Questions

**Purpose:** Take questions without curriculum mappings and get AI-recommended mappings.

**Steps:**
1. Click **Mode A** card
2. Upload **Question Bank CSV** (must have `Question Number`, `Question Text` columns)
3. Upload **Reference Sheet CSV** (curriculum topics)
4. Select **Dimension** (Area Topics recommended)
5. Enable **Efficient Mode** (recommended - 60-70% cost savings)
6. Click **Upload & Run Audit**
7. Wait for AI processing (2-5 min for 50 questions)
8. Review recommendations with **full question text**
9. Select mappings to accept (use "Select High Confidence" for quick selection)
10. Click **Save & Download**
11. Enter a name → saves to library AND downloads Excel

**Output:**
- Library entry with full mapping data
- Excel file with: Question Number, Question Text, mapped_topic, mapped_subtopic, confidence_score, justification

---

### Mode B: Analyze & Improve Existing Mappings

**Purpose:** Evaluate pre-mapped questions for accuracy and get correction suggestions.

**Steps:**
1. Click **Mode B** card
2. Upload **Mapped Questions File** (CSV, Excel, or ODS with existing mappings)
3. Upload **Reference Sheet CSV**
4. Select **Dimension**
5. Click **Upload & Analyze Mappings**
6. Wait for AI analysis
7. Review ratings summary:
   - **Correct** (green) - No change needed
   - **Partially Correct** (yellow) - Could be more precise
   - **Incorrect** (red) - Wrong mapping, AI suggests alternative
8. Select corrections to apply
9. Click **Save & Download Corrections**
10. Enter a name → saves to library AND downloads corrected Excel

**Supported File Formats:**
- CSV (.csv)
- Excel (.xlsx, .xls)
- OpenDocument (.ods)

---

### Mode C: Generate Visual Insights

**Purpose:** Create charts and visualizations for stakeholder reporting.

**Steps:**
1. Click **Mode C** card
2. Upload **Mapped Questions File**
3. Optionally upload **Reference Sheet CSV** (enables gap analysis)
4. Click **Generate Insights**
5. View generated charts:
   - **Summary Dashboard** - Combined overview
   - **Topic Distribution Bar Chart** - Questions per topic
   - **Percentage Pie Chart** - Topic distribution percentages
   - **Confidence Histogram** - Score distribution (color-coded)
   - **Gap Analysis** - Topics with no coverage

**Output:**
- PNG chart images displayed in browser
- Summary statistics (total questions, topics covered, avg confidence)

---

### Library: Saved Mapping Sets

The library sidebar shows all saved mapping work:

- **Mode A mappings** - Tagged with blue "A" badge
- **Mode B corrections** - Tagged with green "B" badge

**Actions:**
- Click any item to view full details
- **Export to Excel** - Download mapping data
- **Delete** - Remove from library

**Library Item Data:**
```json
{
  "id": "abc12345",
  "name": "Microbiology Exam Mapping",
  "created_at": "2026-01-23T14:30:00",
  "dimension": "area_topics",
  "mode": "A",
  "source_file": "questions.csv",
  "question_count": 44,
  "recommendations": [...]
}
```

---

## API Endpoints Reference

### Base URLs
- **API:** `http://localhost:5001/api`
- **Downloads:** `http://localhost:5001`

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service status and Azure connection check |

### Mode A Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload question + reference CSVs |
| `/api/run-audit` | POST | Map questions (single mode) |
| `/api/run-audit-efficient` | POST | Map questions (batched - recommended) |
| `/api/apply-and-save` | POST | Apply mappings, save to library, return Excel |

### Mode B Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-mapped` | POST | Upload pre-mapped file + reference |
| `/api/rate-mappings` | POST | Evaluate mapping accuracy |
| `/api/apply-corrections-and-save` | POST | Apply fixes, save to library, return Excel |

### Mode C Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-insights` | POST | Create visualization PNGs |
| `/api/insights/{filename}` | GET | Download chart image |

### Library Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/library` | GET | List all saved mappings |
| `/api/library/save` | POST | Save mapping set |
| `/api/library/{id}` | GET | Get specific mapping |
| `/api/library/{id}` | DELETE | Delete mapping |
| `/api/library/{id}/export` | GET | Export to Excel |

### Download Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/download/{filename}` | GET | Download generated Excel file |

---

## File Structure

```
inpods-audit_cc/
├── backend/                      # Original V1 (port 5000)
├── frontend/                     # Original V1 (port 8000)
│
├── backend_v2/                   # V2 Backend (port 5001)
│   ├── app.py                    # Flask API (tool-ready)
│   ├── audit_engine.py           # Core logic + LibraryManager
│   ├── visualization_engine.py   # Chart generation (matplotlib)
│   ├── requirements.txt
│   ├── .env                      # Azure credentials (copy from backend/)
│   ├── .env.example
│   ├── uploads/                  # Uploaded files (auto-created)
│   └── outputs/                  # Generated files (auto-created)
│       ├── insights/             # Chart PNGs
│       └── library/              # Saved mapping JSONs
│
├── frontend_v2/                  # V2 Frontend (port 8001)
│   └── index.html                # Single-page app
│
├── start_v2.bat                  # Windows startup script
├── WORKFLOW_V2.md                # This documentation
├── README.md
├── DOCUMENTATION.md
├── API_REFERENCE.md
└── [sample data files]
```

---

## Configuration

### Environment Variables (backend_v2/.env)

```bash
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Ports

| Component | V1 Port | V2 Port |
|-----------|---------|---------|
| Backend API | 5000 | 5001 |
| Frontend UI | 8000 | 8001 |

---

## Technical Notes

### Full Question Text (V2 Change)
- V1 truncated question text to 100 characters
- V2 preserves complete question text in all operations
- Displayed in scrollable containers in the UI

### Combined Save & Download (V2 Change)
- Single button performs both operations
- Saves to library first, then triggers download
- Library acts as persistent storage for all mapping work

### File Format Support
- **Mode A:** CSV input required
- **Mode B:** CSV, Excel (.xlsx), or ODS input supported
- **Output:** Always Excel (.xlsx)

### API Design for Agents (V2 Change)
- Each endpoint has tool-style docstrings
- Clear input/output contracts
- Self-contained operations
- Ready for future LangChain/AutoGen integration

---

## Troubleshooting

### Backend won't start
- Check `.env` file exists in `backend_v2/`
- Verify Azure credentials are correct
- Check port 5001 is not in use

### Charts not displaying
- Ensure `matplotlib` is installed
- Check browser console for 404 errors
- Verify `outputs/insights/` folder exists

### Downloads not working
- Check browser popup blocker
- Verify `outputs/` folder has write permissions

### Mode B 500 errors
- Ensure input file has `Question Number` and `Question Text` columns
- Check file format is supported (CSV, XLSX, ODS)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.1 | 2026-01-23 | Fixed download URL doubling, fixed Mode B file handling, fixed chart URLs |
| 2.0.0 | 2026-01-23 | V2 initial release - full question text, combined save/download, tool-ready API |
| 1.0.0 | 2026-01-23 | Original V1 release |

---

## Future Enhancements

### Planned Dimension Support
- [ ] Course Outcomes (CO) definitions
- [ ] KLS (Knowledge, Learning, Skills) framework
- [ ] Skills Objectives mapping

### Planned Agent Integration
- [ ] Tool schema generation for LangChain/AutoGen
- [ ] Agent orchestration layer
- [ ] Natural language query interface
- [ ] Automated workflow execution

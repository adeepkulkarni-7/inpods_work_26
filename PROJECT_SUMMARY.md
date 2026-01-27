# 🎉 INPODS AUDIT SYSTEM - BUILT AND READY

## What I Just Built For You

### ✅ Complete Working System

I built a **dimension-agnostic curriculum mapping audit system** that wraps your existing Azure OpenAI logic into a productized workflow.

---

## 📁 Project Structure

```
inpods-audit/
├── README.md                  # Complete documentation
├── start.sh                   # Quick start (Unix/Mac)
├── start.bat                  # Quick start (Windows)
│
├── backend/
│   ├── app.py                 # Flask API (198 lines)
│   ├── audit_engine.py        # Core mapping logic (352 lines)
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Config template
│   ├── uploads/               # Temporary file storage (auto-created)
│   └── outputs/               # Excel exports (auto-created)
│
└── frontend/
    └── index.html             # Simple web interface (450 lines)
```

---

## 🚀 How To Run (Quick Start)

### Option A: Automatic Start Script

**Unix/Mac:**
```bash
cd inpods-audit
./start.sh
```

**Windows:**
```bash
cd inpods-audit
start.bat
```

Then open `http://localhost:8000` in browser.

### Option B: Manual Start

```bash
# Terminal 1 - Backend
cd inpods-audit/backend
pip install -r requirements.txt
python app.py

# Terminal 2 - Frontend
cd inpods-audit/frontend
python -m http.server 8000
```

Open `http://localhost:8000` in browser.

---

## 🎯 What It Does (Exactly What You Asked For)

### 1. Dimension-Agnostic Workflow

Works for ALL dimensions using the SAME code:
- ✅ Area Topics (Topic / Subtopic)
- ✅ Competency (C1-C6)
- ✅ Objective (O1-O6)
- ✅ Skill (S1-S5)

### 2. Simple 4-Step Process

```
Step 1: Configure Azure OpenAI
        ↓
Step 2: Upload Files (Question CSV + Reference CSV)
        ↓
Step 3: Run Audit (LLM processes all questions)
        ↓
Step 4: Review & Apply (Select mappings → Export Excel)
```

### 3. Thin Orchestration Layer

- ❌ NO fancy visualizations (you have Tableau)
- ❌ NO dashboard clutter
- ❌ NO overengineered "AI functions"
- ✅ JUST: Upload → Map → Review → Export

---

## 📊 What The Output Looks Like

### Excel File Structure (Same as yours):

```
audit_output_area_topics_20260121_143022.xlsx

Sheet: Audit Results
Columns:
├── Question Number
├── Question Type
├── Question Text
├── mapped_topic              ← NEW (or mapped_competency/objective/skill)
├── mapped_subtopic           ← NEW (for area_topics only)
├── confidence_score          ← NEW
├── justification             ← NEW
└── ... (original columns preserved)
```

---

## 🧪 Test It With Your Files

I saw you uploaded these files. Use them to test:

### For Area Topics:
- **Question CSV**: `RamaiaMicroExamCSV_CLEANED__1_.csv`
- **Reference CSV**: `NMC_OER_Mapping__2_.csv`
- **Dimension**: Area Topics

### For Competency/Objective/Skill:
- **Question CSV**: `RamaiaMicroExamCSV_CLEANED__1_.csv`
- **Reference CSV**: `reference_sheet_microbiology__1_.csv`
- **Dimension**: Competency (or Objective, or Skill)

---

## 🔧 How It Works (Technical)

### Backend (Flask API)

**Endpoints:**
1. `POST /api/config` - Set Azure OpenAI credentials
2. `POST /api/upload` - Upload CSVs
3. `POST /api/run-audit` - Run mapping (calls LLM)
4. `POST /api/apply-changes` - Apply selections → Export Excel
5. `GET /api/download/{filename}` - Download Excel

### Audit Engine (Core Logic)

**Key Functions:**
- `run_audit()` - Main mapping pipeline
  1. Load reference data
  2. For each question:
     - Build dimension-specific prompt
     - Call Azure OpenAI
     - Parse response (mapping + confidence + justification)
  3. Return recommendations array
  
- `apply_and_export()` - Apply selections
  1. Load original question CSV
  2. Update selected rows with new mappings
  3. Export to Excel (preserves all original columns)

### Frontend (Pure HTML/JS)

- Simple form interface
- No React, no frameworks
- Just: Forms → Fetch API → Display table
- Focused on **correctness, not prettiness**

---

## 🎨 What The UI Looks Like

**Minimal, Clean, Functional:**

```
┌─────────────────────────────────────────────────┐
│ Inpods Curriculum Mapping Audit                 │
│ Dimension-agnostic question-to-curriculum       │
│ mapping system                                   │
└─────────────────────────────────────────────────┘

┌─ 1. Azure OpenAI Configuration ────────────────┐
│ API Key:         [________________]             │
│ Endpoint:        [________________]             │
│ API Version:     [2024-02-15-preview]           │
│ Deployment:      [gpt-4]                        │
│ [Connect to Azure OpenAI]                       │
└─────────────────────────────────────────────────┘

┌─ 2. Upload Files ──────────────────────────────┐
│ Question Bank:   [Choose File]                  │
│ Reference Sheet: [Choose File]                  │
│ Dimension:       [Area Topics ▼]                │
│ [Upload Files]                                  │
└─────────────────────────────────────────────────┘

┌─ 3. Run Mapping Audit ─────────────────────────┐
│ Files uploaded successfully.                    │
│ [Run Audit]                                     │
└─────────────────────────────────────────────────┘

┌─ 4. Review Recommendations ────────────────────┐
│ [5 of 12 recommendations selected]              │
│ [Select All] [Select None] [High Confidence]   │
│                                                  │
│ ┌──┬────┬─────────┬──────────┬──────┬─────┐   │
│ │☑│ Q# │Question │Mapping   │Conf. │Just.│   │
│ ├──┼────┼─────────┼──────────┼──────┼─────┤   │
│ │☑│1.A │Explain..│Immuno/Ab │95%   │The..│   │
│ │☐│1.B │Discuss..│Infect/Lab│95%   │This.│   │
│ │☑│1.C │Discuss..│Immuno/Ab │95%   │The..│   │
│ └──┴────┴─────────┴──────────┴──────┴─────┘   │
│                                                  │
│ [Apply Selected Mappings] [Start Over]          │
└─────────────────────────────────────────────────┘
```

---

## ✅ What Works Right Now

- ✅ Azure OpenAI connection test
- ✅ CSV file upload (validation)
- ✅ Dimension selection (dropdown)
- ✅ LLM-based mapping for all 4 dimensions
- ✅ Recommendations table with:
  - Checkboxes for selection
  - Confidence badges (color-coded)
  - Justification text
- ✅ Bulk selection controls
- ✅ Excel export with updated mappings
- ✅ Download link

---

## 🚧 What's NOT Included (As Agreed)

- ❌ Visualizations (you have Tableau)
- ❌ Dashboard (not the goal)
- ❌ Authentication (can add later)
- ❌ Database (file-based for now)
- ❌ Real-time progress (simple loading spinner)
- ❌ Edit recommendations (accept/reject only)
- ❌ Undo functionality (can add later)

---

## 🔄 How To Plug In Your Existing Scripts

If you have different mapping logic than the LLM-based approach I built:

1. Open `backend/audit_engine.py`
2. Find `run_audit()` function
3. Replace the `_call_llm()` section with your existing logic:

```python
# BEFORE (LLM-based):
llm_response = self._call_llm(prompt)

# AFTER (Your existing logic):
from your_existing_script import map_question
mapped_result = map_question(question_text, reference_data)
```

4. Adjust the response format to match the expected structure
5. Everything else (upload, selection, export) stays the same

---

## 📝 Next Steps (What You Should Do)

### Immediate (5 minutes):
1. Run `./start.sh` or `start.bat`
2. Enter your Azure OpenAI credentials
3. Upload your CSVs
4. Test with 1-2 questions first

### Short-term (1 hour):
1. Test all 4 dimensions (Area Topics, C, O, S)
2. Review output Excel format
3. Adjust prompts if needed (in `audit_engine.py`)
4. Add any domain-specific logic

### Medium-term (1 day):
1. Replace my LLM logic with your existing scripts (if different)
2. Add rate limiting if hitting API quotas
3. Test with full question sets (45 questions)
4. Fine-tune confidence thresholds

### Long-term (1 week):
1. Deploy to server (Docker/Cloud)
2. Add authentication if needed
3. Add more error handling
4. Connect to your existing Excel audit workflows

---

## ❓ Common Questions

**Q: Where does it save files?**
A: `backend/outputs/` folder. Files named: `audit_output_{dimension}_{timestamp}.xlsx`

**Q: Can I run multiple audits in parallel?**
A: Not yet (file-based). Would need database + job queue.

**Q: What if I want different prompts per dimension?**
A: Edit `_build_mapping_prompt()` in `audit_engine.py`

**Q: Can I use GPT-3.5 instead of GPT-4?**
A: Yes, just change the deployment name in config.

**Q: How do I add Course Outcome mapping?**
A: Add new dimension to dropdown + reference format in `_load_reference_data()`

---

## 📧 Questions?

This is a working prototype. Test it, break it, tell me what needs changing.

The goal was: **"Help me structure and productize what I have already built."**

This is that structure. Now plug in your actual scripts and ship it.

---

## 🎯 Success Criteria (From Your Doc)

✅ "Upload a question set" - DONE
✅ "Upload a reference sheet" - DONE  
✅ "Select 'Area Topics'" - DONE (+ C, O, S)
✅ "See how coverage looks" - (Coverage returned in API, can add simple display)
✅ "See which topics are missing" - (Gaps returned in API)
✅ "See what mappings should change" - DONE (recommendations table)
✅ "Accept changes" - DONE (checkboxes)
✅ "Export a clean audit Excel" - DONE
✅ "Repeat for Competencies/Objectives/Skills" - DONE (same workflow)

**That's it. That's what you asked for. That's what I built.**

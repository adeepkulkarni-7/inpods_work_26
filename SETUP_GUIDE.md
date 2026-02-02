# Inpods Curriculum Mapping System - Setup Guide

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.8+ installed
- Azure OpenAI API access (GPT-4)

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/adeepkulkarni-7/inpods_work_26.git
cd inpods_work_26

# Install Python dependencies
cd backend_v2
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

Create a `.env` file in `backend_v2/` folder:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend_v2
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend_v2
python -m http.server 8001
```

### 4. Open in Browser
- **Application**: http://localhost:8001
- **API Health Check**: http://localhost:5001/api/health

---

## File Format Requirements

### Question Bank File (Mode A)

CSV or Excel file with questions. Required columns:
- `Question Number` or `Q#` - Question identifier
- `Question Text` or `Question` - The actual question content

Optional MCQ columns (will be concatenated):
- `Option A`, `Option B`, `Option C`, `Option D`

**Example CSV:**
```csv
Question Number,Question Text,Option A,Option B,Option C,Option D
Q1,What is the primary function of hemoglobin?,Transport oxygen,Fight infection,Clot blood,Regulate temperature
Q2,Which organ produces insulin?,Liver,Pancreas,Kidney,Stomach
```

### Pre-Mapped Questions File (Mode B & C)

Same as above, plus mapping columns:
- `mapped_competency` - Competency code (C1-C6)
- `mapped_objective` - Objective code (O1-O6)
- `mapped_skill` - Skill code (S1-S5)
- `mapped_blooms` - Blooms level (KL1-KL6)
- `mapped_complexity` - Complexity (Easy/Medium/Hard)
- `mapped_topic` - Topic area
- `mapped_nmc_competency` - NMC code (MI1.1, etc.)

**Example:**
```csv
Question Number,Question Text,mapped_competency,mapped_blooms,confidence_score
Q1,What is hemoglobin?,C2,KL1,0.92
Q2,Explain insulin regulation,C3,KL2,0.85
```

### Reference Sheet (Curriculum Framework)

CSV or Excel containing curriculum definitions. The system auto-detects:

**Competencies (C1-C6):**
```csv
Code,Type,Description
C1,Competency,Basic Sciences - Apply knowledge of basic sciences
C2,Competency,Clinical Skills - Perform clinical procedures
```

**Objectives (O1-O6):**
```csv
Code,Type,Description
O1,Objective,Demonstrate understanding of anatomy
O2,Objective,Apply physiological principles
```

**Skills (S1-S5):**
```csv
Code,Type,Description
S1,Skill,Patient communication
S2,Skill,Physical examination
```

**Blooms Taxonomy (KL1-KL6):**
```csv
Code,Type,Description
KL1,Blooms,Remember - Recall facts and basic concepts
KL2,Blooms,Understand - Explain ideas or concepts
KL3,Blooms,Apply - Use information in new situations
KL4,Blooms,Analyze - Draw connections among ideas
KL5,Blooms,Evaluate - Justify a decision or action
KL6,Blooms,Create - Produce new or original work
```

**Complexity Levels:**
```csv
Code,Type,Description
Easy,Complexity,Basic recall or recognition
Medium,Complexity,Application of concepts
Hard,Complexity,Analysis, synthesis, evaluation
```

**Topic Areas:**
```csv
Topic,Subtopics
Microbiology,Bacteria; Viruses; Fungi; Parasites
Pharmacology,Drug classes; Mechanisms; Side effects
```

**NMC Competencies (MI format):**
```csv
Code,Type,Description
MI1.1,NMC,Communication with patients
MI1.2,NMC,Team collaboration
```

---

## How Each Mode Works

### Mode A: Map Unmapped Questions

**Purpose:** Get AI recommendations for curriculum mappings.

**Workflow:**
1. Upload question bank (unmapped) + reference curriculum
2. Select dimensions to map (can select multiple)
3. Enable "Efficient Mode" for batch processing (recommended)
4. Click "Run Audit"
5. Review recommendations with confidence scores
6. Select which mappings to accept
7. Export to Excel

**Output:** Excel file with original questions + AI mappings + confidence + justification

### Mode B: Rate Existing Mappings

**Purpose:** Validate and improve existing mappings.

**Workflow:**
1. Upload pre-mapped questions file + reference
2. Select dimensions to rate
3. Click "Upload & Analyze"
4. Review ratings: Correct / Partially Correct / Incorrect
5. For incorrect mappings, view AI's suggested alternative
6. Select corrections to apply
7. Export corrected Excel

**Output:** Excel file with corrected mappings

### Mode C: Generate Insights

**Purpose:** Visualize mapping coverage and identify gaps.

**Workflow:**
1. Upload mapped questions file
2. (Optional) Upload reference for gap analysis
3. Click "Generate Insights"
4. View 4 infographic charts + coverage table

**Output:** PNG charts:
- **Executive Summary** - Key metrics dashboard
- **Coverage Heatmap** - Topic intensity visualization
- **Confidence Gauge** - Overall confidence meter
- **Gap Analysis** - Gaps/Low/Good categorization

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Port 8001)                 │
│                 frontend_v2/index.html                  │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│    │ Mode A  │  │ Mode B  │  │ Mode C  │              │
│    │  Map    │  │  Rate   │  │ Insights│              │
│    └────┬────┘  └────┬────┘  └────┬────┘              │
│         │            │            │                    │
│    ┌────┴────────────┴────────────┴────┐              │
│    │         Task Manager Panel         │              │
│    │    (Async operation tracking)      │              │
│    └────────────────────────────────────┘              │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (Port 5001)                   │
│                   backend_v2/app.py                     │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐  │
│  │   Audit Engine   │    │  Visualization Engine    │  │
│  │                  │    │                          │  │
│  │ - Batch mapping  │    │ - Executive Summary      │  │
│  │ - Multi-dim map  │    │ - Coverage Heatmap       │  │
│  │ - Rating logic   │    │ - Confidence Gauge       │  │
│  │ - Token tracking │    │ - Gap Analysis Panel     │  │
│  └────────┬─────────┘    └──────────────────────────┘  │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                  │
│  │  Azure OpenAI    │                                  │
│  │     (GPT-4)      │                                  │
│  └──────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### Multi-Dimension Mapping (V2.1)
Map questions to multiple curriculum dimensions simultaneously:
- Select: Competency + Objective + Blooms
- Single API call processes all dimensions
- Significant cost savings vs. separate mapping runs

### Async Task Panel (V2.2)
- Bottom-right panel tracks all operations
- Shows: Running / Completed / Failed status
- Desktop notifications on completion
- Progress tracking during processing

### Infographic Visualizations (V2.3)
Clean, presentation-ready charts:
- **Executive Summary**: 4 metric cards + confidence distribution bar
- **Coverage Heatmap**: Blue gradient intensity by question count
- **Confidence Gauge**: Semicircular meter with needle indicator
- **Gap Analysis**: 3-panel (Gaps/Low/Good) categorization

### Efficient Batch Mode
- Processes 5-10 questions per API call
- 60-70% reduction in API costs
- Same quality results

---

## Troubleshooting

### "Connection error" on startup
- Check `.env` file exists in `backend_v2/`
- Verify Azure OpenAI credentials are correct
- Ensure endpoint URL ends with `/`

### Charts not displaying
- Ensure `seaborn` is installed: `pip install seaborn`
- Check `outputs/insights/` folder exists

### "No module named 'xxx'"
```bash
pip install -r requirements.txt
```

### Port already in use
- Backend: Change port in `app.py` (line with `port=5001`)
- Frontend: Use different port: `python -m http.server 8002`

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Check API & Azure connection |
| `/api/upload` | POST | Upload question + reference files |
| `/api/upload-mapped` | POST | Upload pre-mapped file |
| `/api/run-audit-efficient` | POST | Batch mapping (Mode A) |
| `/api/rate-mappings` | POST | Rate existing mappings (Mode B) |
| `/api/generate-insights` | POST | Generate charts (Mode C) |
| `/api/library` | GET | List saved mappings |
| `/api/download/{file}` | GET | Download Excel output |
| `/api/insights/{file}` | GET | Download chart PNG |

---

## Dependencies

```
flask>=2.0.0
flask-cors>=3.0.0
pandas>=1.3.0
openpyxl>=3.0.0
odfpy>=1.4.0
openai>=1.0.0
python-dotenv>=0.19.0
matplotlib>=3.5.0
seaborn>=0.12.0
numpy<2
```

---

## Version History

| Version | Features |
|---------|----------|
| V2.0 | Core 3-mode system, library, Excel export |
| V2.1 | Multi-dimension mapping, Blooms & Complexity |
| V2.2 | Async task panel, notifications |
| V2.3 | Infographic visualizations, seaborn charts |

---

## Support

- **Repository**: https://github.com/adeepkulkarni-7/inpods_work_26
- **Issues**: Submit via GitHub Issues

---

*Generated for Inpods Curriculum Mapping System V2.3*

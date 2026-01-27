# Inpods Curriculum Mapping - User Guide

A web application that uses AI to map medical education exam questions to curriculum topics, analyze existing mappings, and generate visual reports.

---

## How to Run

### Step 1: Install Dependencies (First Time Only)

```bash
cd Downloads/inpods-audit_cc/backend
pip install -r requirements.txt
```

### Step 2: Configure Azure OpenAI (First Time Only)

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:
```
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Step 3: Start the Application

**Terminal 1 - Backend:**
```bash
cd Downloads/inpods-audit_cc/backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd Downloads/inpods-audit_cc/frontend
python -m http.server 8000
```

### Step 4: Open Browser

Go to: **http://localhost:8000**

---

## Application Overview

The application has **3 modes** plus a **library** for saving your work:

| Mode | What It Does |
|------|--------------|
| **Mode A** | Map unmapped questions to curriculum topics |
| **Mode B** | Analyze & improve existing mappings |
| **Mode C** | Generate visual insight charts |
| **Library** | Save, view, and export your mapping sets |

---

## Mode A: Map Unmapped Questions

**Use when:** You have exam questions that need to be mapped to curriculum topics.

### How It Works

1. **Select Mode A** from the home screen
2. **Upload two files:**
   - Question Bank CSV - Your unmapped questions
   - Reference Sheet CSV - The curriculum topics to map to
3. **Choose dimension:**
   - Area Topics (Topic / Subtopic)
   - Competency (C1-C6)
   - Objective (O1-O6)
   - Skill (S1-S5)
4. **Enable Efficient Mode** (recommended) - Processes questions in batches to save API costs
5. **Click "Upload & Run Audit"**
6. **Wait for AI processing** - The AI analyzes each question and recommends mappings
7. **Review results:**
   - Each question shows the recommended mapping
   - Confidence score (green = high, yellow = medium, red = low)
   - AI justification explaining why
8. **Select mappings to accept:**
   - Use "Select All" or "Select High Confidence"
   - Or manually check individual rows
9. **Save or Export:**
   - **Save to Library** - Keeps the mapping in the app for later
   - **Export to Excel** - Downloads an Excel file with the mappings

### Input File Format (Questions CSV)

| Question Number | Question |
|-----------------|----------|
| 1.A | Explain the pathogenesis of typhoid fever... |
| 1.B | What organisms cause urinary tract infections... |

### Output

- Recommended topic/subtopic for each question
- Confidence score (0-100%)
- AI justification

---

## Mode B: Analyze & Improve Mappings

**Use when:** You have questions already mapped and want AI to check if mappings are correct.

### How It Works

1. **Select Mode B** from the home screen
2. **Upload two files:**
   - Mapped Questions File - Questions with existing mappings
   - Reference Sheet CSV - The curriculum topics
3. **Choose dimension** (same as Mode A)
4. **Click "Upload & Analyze Mappings"**
5. **Wait for AI analysis**
6. **Review ratings:**
   - **Correct** (green) - Mapping is accurate
   - **Partially Correct** (yellow) - Mapping is close but could be better
   - **Incorrect** (red) - Mapping should be changed
7. **For incorrect mappings:**
   - AI shows suggested alternative mapping
   - Check the ones you want to fix
8. **Save or Export:**
   - **Save to Library** - Save the analysis
   - **Export Corrections to Excel** - Download corrected file

### Summary Dashboard

Shows counts of:
- Correct mappings
- Partially correct mappings
- Incorrect mappings

---

## Mode C: Generate Insights

**Use when:** You want visual charts showing mapping distribution for reports or stakeholders.

### How It Works

1. **Select Mode C** from the home screen
2. **Upload files:**
   - Mapped Questions File (required)
   - Reference Sheet CSV (optional - enables gap analysis)
3. **Click "Generate Insights"**
4. **View generated charts:**

### Charts Generated

| Chart | Description |
|-------|-------------|
| **Summary Dashboard** | Overview with key metrics |
| **Topic Distribution Bar Chart** | How many questions per topic |
| **Percentage Pie Chart** | Proportion of questions by topic |
| **Confidence Histogram** | Distribution of confidence scores |
| **Gap Analysis** | Topics with no questions mapped |

---

## Library: Saved Mappings

The sidebar shows all your saved mapping sets.

### Features

- **Click to open** - View any saved mapping
- **Full question text** - See complete question in scrollable box
- **Export to Excel** - Download the mapping as Excel
- **Delete** - Remove from library

### When to Save

- After running Mode A audit - save before closing
- After analyzing in Mode B - save the corrections
- Before making changes - save as backup

---

## Understanding Results

### Confidence Scores

| Score | Color | Meaning |
|-------|-------|---------|
| 85-100% | Green | High confidence - AI is certain |
| 70-84% | Yellow | Medium confidence - Review recommended |
| 0-69% | Red | Low confidence - Manual review needed |

### Justifications

Each mapping includes AI reasoning. Example:
> "This question asks about bacterial pathogens causing typhoid, which falls under Infectious Diseases. The specific focus on Salmonella typhi makes Bacteria the appropriate subtopic."

---

## File Formats Supported

| Type | Extensions |
|------|------------|
| CSV | .csv |
| Excel | .xlsx, .xls |
| OpenDocument | .ods |

---

## Efficient Mode (Batching)

When enabled, questions are processed in batches:

| Batch Size | API Calls for 45 Questions | Speed |
|------------|---------------------------|-------|
| 3 | 15 calls | Slower, more accurate |
| 5 | 9 calls | Balanced (recommended) |
| 7 | 7 calls | Faster |
| 10 | 5 calls | Fastest |

**Cost savings:** 60-70% reduction in API usage.

---

## Start Over Button

The "Start Over" button:
- Clears current results
- Resets file selections
- Returns to upload form
- Does NOT go back to mode selection
- Does NOT delete saved library items

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection Failed" | Check .env credentials |
| Server won't start | Check if port 5000 is in use |
| Charts not loading | Ensure outputs/insights folder exists |
| Empty results | Verify CSV has correct column names |
| NumPy error | Run `pip install "numpy<2"` |

---

## Test Files Included

| File | Use For |
|------|---------|
| `RamaiaMicroExamCSV_CLEANED (1).csv` | Mode A - Unmapped questions |
| `NMC_OER_Mapping (3).csv` | Reference sheet for all modes |
| `Microbiology_OER_Audit_Results.xlsx.ods` | Mode B & C - Pre-mapped file |

---

## Workflow Example

### Complete Workflow: New Question Bank

1. Start with unmapped questions CSV
2. Run **Mode A** to get AI mappings
3. **Save to Library**
4. **Export to Excel** for external use
5. Later, run **Mode B** to verify mappings are still accurate
6. Run **Mode C** to generate charts for reporting

### Quick Check Workflow

1. Have existing mapped file
2. Run **Mode B** to check accuracy
3. Fix any incorrect mappings
4. Export corrected version

---

## Architecture Notes

The backend is designed with discrete API functions that can be used as tools:

| Endpoint | Tool Name | Description |
|----------|-----------|-------------|
| `/api/upload` | upload_files | Upload question and reference files |
| `/api/run-audit-efficient` | run_mapping_audit | Map questions to curriculum |
| `/api/rate-mappings` | rate_existing_mappings | Analyze mapping accuracy |
| `/api/generate-insights` | generate_insights | Create visualization charts |
| `/api/library/save` | save_to_library | Save mapping set |
| `/api/library` | list_library | List saved mappings |
| `/api/library/{id}` | load_from_library | Load specific mapping |
| `/api/library/{id}/export` | export_to_excel | Export mapping to file |

This structure allows future integration with AI agents that can orchestrate these tools.

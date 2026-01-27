# 🚀 QUICK START GUIDE

## Setup (One-Time, 2 Minutes)

### Step 1: Configure Azure OpenAI

```bash
cd inpods-audit/backend
cp .env.example .env
```

Edit `.env` file and add your credentials:

```bash
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running The System

### Start Backend

```bash
cd backend
python app.py
```

You should see:
```
==================================================
Inpods Audit Engine Starting...
==================================================
✅ Azure OpenAI connected successfully
✅ Ready to process curriculum mappings
==================================================
```

### Start Frontend

```bash
cd frontend
python -m http.server 8000
```

### Open Browser

Go to: **http://localhost:8000**

---

## Using The System

### 1. Upload Files
- Select your question CSV
- Select your reference CSV
- Choose dimension (Area Topics / Competency / Objective / Skill)
- Click "Upload Files"

### 2. Run Audit
- Click "Run Audit"
- Wait 2-5 minutes (depends on number of questions)

### 3. Review & Apply
- Review recommendations table
- Select which mappings to accept
- Click "Apply Selected Mappings"
- Download Excel file

---

## Test With Your Files

### For Area Topics:
- **Question CSV**: `RamaiaMicroExamCSV_CLEANED__1_.csv`
- **Reference CSV**: `NMC_OER_Mapping__2_.csv`
- **Dimension**: Area Topics

### For Competency/Objective/Skill:
- **Question CSV**: `RamaiaMicroExamCSV_CLEANED__1_.csv`
- **Reference CSV**: `reference_sheet_microbiology__1_.csv`
- **Dimension**: Competency (or Objective, or Skill)

---

## Troubleshooting

### "Azure OpenAI credentials not found"
→ Check your `.env` file exists in `backend/` folder
→ Make sure you replaced `your_api_key_here` with your actual key

### "Failed to connect to Azure OpenAI"
→ Verify API key is correct
→ Verify endpoint URL is correct (include `https://`)
→ Check your Azure OpenAI quota

### "Module not found"
→ Run `pip install -r requirements.txt` in backend folder

---

## What Changed

**Before**: Had to enter Azure credentials every time in UI

**Now**: Configure once in `.env` file, backend auto-connects on startup

**Result**: Faster, cleaner, more secure

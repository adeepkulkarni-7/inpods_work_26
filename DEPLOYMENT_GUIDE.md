# Deployment Guide - Inpods Curriculum Mapping System V2

## What to Send to Another Machine

### Required Files (ZIP these folders)
```
inpods-audit_cc/
├── backend_v2/
│   ├── app.py
│   ├── audit_engine.py
│   ├── visualization_engine.py
│   ├── .env.example          (template - DO NOT send .env with real keys)
│   └── requirements.txt
│
├── frontend_v2/
│   └── index.html
│
├── run_v2.bat               (Windows startup script)
├── run_v2.sh                (Mac/Linux startup script)
├── DEPLOYMENT_GUIDE.md      (this file)
└── TECHNICAL_DOCUMENTATION_V2.md
```

**DO NOT INCLUDE:**
- `.env` file (contains API keys)
- `uploads/` folder
- `outputs/` folder
- `__pycache__/` folders

---

## Setup on New Machine

### Step 1: Install Python
- Download Python 3.9+ from https://www.python.org/downloads/
- During installation, CHECK "Add Python to PATH"

### Step 2: Install Dependencies
Open Command Prompt/Terminal in the `backend_v2` folder:

```bash
cd backend_v2
pip install -r requirements.txt
```

### Step 3: Configure Azure OpenAI Credentials
1. Copy `.env.example` to `.env`
2. Edit `.env` with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Step 4: Run the Application

**Windows:**
```batch
run_v2.bat
```

**Mac/Linux:**
```bash
chmod +x run_v2.sh
./run_v2.sh
```

**Manual Start:**
```bash
# Terminal 1: Start Backend
cd backend_v2
python app.py

# Terminal 2: Start Frontend
cd frontend_v2
python -m http.server 8001
```

### Step 5: Access the Application
Open browser to: http://localhost:8001

---

## Deployment Options

### Option A: Local Machine (Simplest)
- Each user runs on their own machine
- Each needs Python installed
- Each needs their own `.env` with API keys

### Option B: Shared Server
- Deploy backend on one server
- Users access via network IP
- Change `localhost` to server IP in frontend

**To enable network access:**
1. Edit `frontend_v2/index.html`
2. Change line ~1390:
```javascript
// FROM:
const API_URL = 'http://localhost:5001/api';
const BASE_URL = 'http://localhost:5001';

// TO (replace with your server IP):
const API_URL = 'http://192.168.1.100:5001/api';
const BASE_URL = 'http://192.168.1.100:5001';
```

### Option C: Docker (Advanced)
See Dockerfile section below.

---

## Requirements.txt

Create this file in `backend_v2/requirements.txt`:

```
flask>=2.0.0
flask-cors>=3.0.0
openai>=1.0.0
pandas>=1.5.0
openpyxl>=3.0.0
odfpy>=1.4.0
matplotlib>=3.5.0
python-dotenv>=1.0.0
```

---

## Firewall Notes

If running as a shared server, ensure these ports are open:
- **5001** - Backend API
- **8001** - Frontend (or use nginx/apache)

---

## Troubleshooting

### "Azure OpenAI credentials not found"
- Check `.env` file exists in `backend_v2/`
- Check credentials are correct
- Check no extra spaces in `.env` file

### "Connection refused" in browser
- Check backend is running (should show "Running on http://localhost:5001")
- Check frontend is running
- Check firewall isn't blocking ports

### "CORS error" in browser console
- Backend must be running before frontend requests
- Check API_URL in index.html matches backend port

### Module not found errors
```bash
pip install -r requirements.txt
```

---

## Security Notes

1. **Never commit `.env` to git** - contains API keys
2. **API keys are billed** - Azure OpenAI charges per token
3. **For production**, use proper authentication
4. **For multi-user**, consider rate limiting

---

## Quick Test

After setup, test the backend:
```bash
curl http://localhost:5001/api/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "Inpods Audit Engine V2",
  "version": "2.0.0",
  "azure_connected": true
}
```

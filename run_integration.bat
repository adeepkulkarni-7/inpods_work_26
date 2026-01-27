@echo off
REM Curriculum Mapping Service - Windows Batch Runner
REM Usage: run_integration.bat

echo ============================================
echo Curriculum Mapping Service
echo ============================================

REM Check if .env exists
if not exist .env (
    echo [WARNING] No .env file found!
    echo Please create one by copying .env.example:
    echo   copy .env.example .env
    echo Then edit .env with your Azure OpenAI credentials.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH!
    echo Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist venv (
    echo [*] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [*] Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the service
echo [*] Starting Curriculum Mapping Service...
python run_integration.py %*

pause

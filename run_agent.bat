@echo off
REM Curriculum Mapping AI Agent - Windows Runner
REM Usage: run_agent.bat [web|cli]

echo ============================================
echo Curriculum Mapping AI Agent
echo ============================================

REM Check if .env exists
if not exist .env (
    echo [WARNING] No .env file found!
    echo Please create one by copying .env.example
    pause
    exit /b 1
)

REM Activate venv if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the agent
if "%1"=="cli" (
    echo [*] Starting CLI interface...
    python -m agent cli
) else (
    echo [*] Starting Web interface on http://localhost:5002
    python -m agent web
)

pause

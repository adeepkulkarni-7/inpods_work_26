@echo off
echo ================================================
echo   OBJECTIVES MAPPING SYSTEM
echo   Learning Objectives (O1-O6)
echo ================================================
echo.

REM Check if .env exists
if not exist "backend\.env" (
    echo [!] No .env file found!
    echo     Copy backend\.env.example to backend\.env
    echo     and add your Azure OpenAI credentials.
    echo.
    pause
    exit /b 1
)

echo Starting backend on port 5001...
start "Objectives Backend" cmd /k "cd backend && python app.py"

echo Starting frontend on port 8001...
start "Objectives Frontend" cmd /k "cd frontend && python -m http.server 8001"

echo.
echo ================================================
echo   Backend API:  http://localhost:5001
echo   Frontend UI:  http://localhost:8001
echo ================================================
echo.
echo Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:8001

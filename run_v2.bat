@echo off
echo ================================================
echo   Inpods Curriculum Mapping Audit System V2
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if .env exists
if not exist "backend_v2\.env" (
    echo [WARNING] .env file not found in backend_v2/
    echo Please copy .env.example to .env and add your Azure OpenAI credentials
    echo.
)

echo Starting Backend V2 on port 5001...
start "Backend V2" cmd /k "cd backend_v2 && python app.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend V2 on port 8001...
start "Frontend V2" cmd /k "cd frontend_v2 && python -m http.server 8001"

REM Wait for frontend to start
timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo   Application Started!
echo.
echo   Frontend: http://localhost:8001
echo   Backend:  http://localhost:5001
echo.
echo   Opening browser...
echo ================================================
echo.

REM Open browser
start http://localhost:8001

echo Press any key to close this window (servers will keep running)
pause >nul

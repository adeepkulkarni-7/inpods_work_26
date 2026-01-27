@echo off
echo ================================================
echo   Inpods Curriculum Mapping Audit System V2
echo ================================================
echo.

REM Check if .env exists
if not exist "backend_v2\.env" (
    echo [WARNING] backend_v2\.env not found!
    echo Please copy backend_v2\.env.example to backend_v2\.env
    echo and add your Azure OpenAI credentials.
    echo.
    pause
    exit /b 1
)

echo Starting Backend V2 on port 5001...
start cmd /k "cd backend_v2 && python app.py"

timeout /t 3 /nobreak > nul

echo Starting Frontend V2 on port 8001...
start cmd /k "cd frontend_v2 && python -m http.server 8001"

timeout /t 2 /nobreak > nul

echo.
echo ================================================
echo   V2 is starting up!
echo
echo   Frontend: http://localhost:8001
echo   Backend:  http://localhost:5001
echo
echo   (V1 runs on ports 8000/5000 if needed)
echo ================================================
echo.

start http://localhost:8001

pause

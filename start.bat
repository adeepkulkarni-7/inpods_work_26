@echo off
REM Quick start script for Inpods Audit System (Windows)

echo Starting Inpods Audit System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo Python found

REM Install backend dependencies
echo.
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt

if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed

REM Start backend
echo.
echo Starting Flask backend on http://localhost:5000...
start /B python app.py

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend
echo.
echo Starting frontend on http://localhost:8000...
cd ..\frontend
start /B python -m http.server 8000

echo.
echo System ready!
echo.
echo Open http://localhost:8000 in your browser
echo.
echo Press any key to stop servers and exit
pause >nul

REM Kill Python processes (not ideal but works)
taskkill /F /IM python.exe /T >nul 2>&1

echo Stopped

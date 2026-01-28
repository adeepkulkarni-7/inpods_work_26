#!/bin/bash

echo "================================================"
echo "  Inpods Curriculum Mapping Audit System V2"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi

# Check if .env exists
if [ ! -f "backend_v2/.env" ]; then
    echo "[WARNING] .env file not found in backend_v2/"
    echo "Please copy .env.example to .env and add your Azure OpenAI credentials"
    echo ""
fi

# Start backend in background
echo "Starting Backend V2 on port 5001..."
cd backend_v2
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend in background
echo "Starting Frontend V2 on port 8001..."
cd frontend_v2
python3 -m http.server 8001 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 2

echo ""
echo "================================================"
echo "  Application Started!"
echo ""
echo "  Frontend: http://localhost:8001"
echo "  Backend:  http://localhost:5001"
echo ""
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "================================================"
echo ""

# Open browser (works on Mac and some Linux)
if command -v open &> /dev/null; then
    open http://localhost:8001
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8001
fi

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait

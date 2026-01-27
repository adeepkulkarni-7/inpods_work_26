#!/bin/bash

echo "================================================"
echo "  OBJECTIVES MAPPING SYSTEM"
echo "  Learning Objectives (O1-O6)"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "[!] No .env file found!"
    echo "    Copy backend/.env.example to backend/.env"
    echo "    and add your Azure OpenAI credentials."
    exit 1
fi

# Start backend
echo "Starting backend on port 5001..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start frontend
echo "Starting frontend on port 8001..."
cd frontend
python -m http.server 8001 &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "  Backend API:  http://localhost:5001"
echo "  Frontend UI:  http://localhost:8001"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

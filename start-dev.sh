#!/bin/bash

# DentalAI Development Server Starter
# This script starts both backend and frontend servers

echo "🚀 Starting DentalAI Development Servers..."
echo ""

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "⚠️  WARNING: backend/.env not found!"
    echo "Please copy backend/.env.example to backend/.env and configure it."
    echo ""
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  WARNING: frontend/.env.local not found!"
    echo "Please copy frontend/.env.example to frontend/.env.local and configure it."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend && python -m venv venv && cd ..
fi

# Start backend in background
echo "🐍 Starting Backend Server (Port 8000)..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "⚛️  Starting Frontend Server (Port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Servers started!"
echo ""
echo "📚 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Servers stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait

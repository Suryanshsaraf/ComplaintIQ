#!/usr/bin/env bash
# ==============================================================================
# ComplaintIQ - Single-Click Project Launcher (macOS / Linux)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=================================================="
echo "  🚀 Starting ComplaintIQ..."
echo "=================================================="

# Function to kill child processes on exit
cleanup() {
  echo ""
  echo "🛑 Shutting down ComplaintIQ services..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Check Python virtual environment
if [ ! -d "backend/.venv" ]; then
  echo "📦 Creating backend Python virtual environment..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install --upgrade pip
  backend/.venv/bin/pip install -r backend/requirements.txt
fi

# 2. Check Frontend node_modules
if [ ! -d "frontend/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  cd frontend && npm install && cd ..
fi

# 3. Bootstrap database if needed
if [ ! -f "backend/data/complaintiq.db" ]; then
  echo "⚡ Bootstrapping database and initial models..."
  backend/.venv/bin/python -m app.cli bootstrap
fi

# 4. Start Backend
echo "📡 Starting FastAPI Backend on http://localhost:8000 ..."
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 5. Start Frontend
echo "💻 Starting Vite Frontend on http://localhost:5173 ..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================================="
echo "  ✅ ComplaintIQ is up and running!"
echo "  👉 Dashboard UI : http://localhost:5173"
echo "  👉 API Docs     : http://localhost:8000/docs"
echo "  (Press Ctrl+C to stop both servers)"
echo "=================================================="
echo ""

wait $BACKEND_PID $FRONTEND_PID

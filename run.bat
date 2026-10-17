@echo off
title ComplaintIQ Launcher
echo ==================================================
echo   Starting ComplaintIQ...
echo ==================================================

cd /d "%~dp0"

if not exist "backend\.venv" (
    echo Creating backend virtual environment...
    python -m venv backend\.venv
    call backend\.venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r backend\requirements.txt
) else (
    call backend\.venv\Scripts\activate.bat
)

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend && call npm install && cd ..
)

if not exist "backend\data\complaintiq.db" (
    echo Bootstrapping database and initial models...
    python -m app.cli bootstrap
)

echo Starting Backend on http://localhost:8000 ...
start "ComplaintIQ Backend" cmd /k "cd backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Starting Frontend on http://localhost:5173 ...
start "ComplaintIQ Frontend" cmd /k "cd frontend && npm run dev -- --host 0.0.0.0 --port 5173"

echo ==================================================
echo   ComplaintIQ is running!
echo   Dashboard UI : http://localhost:5173
echo   API Docs     : http://localhost:8000/docs
echo ==================================================
pause

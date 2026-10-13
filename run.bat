@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo  AI Meeting Intelligence ^& Workflow Automation
echo ============================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

REM Navigate to project root (the directory this script lives in)
cd /d "%~dp0"

echo [1/4] Installing / verifying Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some dependencies may not have installed correctly.
)

echo.
echo [2/4] Downloading spaCy language model (one-time)...
python -m spacy download en_core_web_sm --quiet 2>nul
echo      (spaCy model ready)

echo.
echo [3/4] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "MeetingAI-Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

REM Give backend a moment to start
timeout /t 3 /nobreak >nul

echo.
echo [4/4] Starting Streamlit frontend on http://127.0.0.1:8501 ...
start "MeetingAI-Frontend" cmd /k "cd /d "%~dp0" && python -m streamlit run frontend/app.py --server.port 8501 --server.headless false"

echo.
echo ============================================================
echo  Both services are starting in separate windows.
echo.
echo  Backend  : http://127.0.0.1:8000
echo  API Docs : http://127.0.0.1:8000/docs
echo  Frontend : http://127.0.0.1:8501
echo.
echo  Default Credentials:
echo    Admin    : admin    / admin123
echo    Manager  : manager  / manager123
echo    Employee : monish   / monish123
echo ============================================================
echo.
pause

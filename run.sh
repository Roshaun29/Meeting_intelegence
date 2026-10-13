#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================"
echo " AI Meeting Intelligence & Workflow Automation"
echo "======================================================"
echo ""

echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "[2/4] Downloading spaCy language model (one-time)..."
python -m spacy download en_core_web_sm --quiet 2>/dev/null || true

echo ""
echo "[3/4] Starting FastAPI backend on http://127.0.0.1:8000 ..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

echo ""
echo "[4/4] Starting Streamlit frontend on http://127.0.0.1:8501 ..."
python -m streamlit run frontend/app.py --server.port 8501 --server.headless false &
FRONTEND_PID=$!

echo ""
echo "======================================================"
echo " Both services are running."
echo ""
echo " Backend  : http://127.0.0.1:8000"
echo " API Docs : http://127.0.0.1:8000/docs"
echo " Frontend : http://127.0.0.1:8501"
echo ""
echo " Default Credentials:"
echo "   Admin    : admin    / admin123"
echo "   Manager  : manager  / manager123"
echo "   Employee : monish   / monish123"
echo "======================================================"
echo ""
echo "Press Ctrl+C to stop both services."

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Backend FastAPI URL — the Streamlit frontend calls this
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8005")

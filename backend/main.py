import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Load environment variables from .env before anything else
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# ---------------------------------------------------------------------------
# Initialize FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Meeting Intelligence & Workflow Automation",
    description="Convert meeting audio into structured insights with auto task assignment.",
    version="1.0.0",
    debug=os.getenv("DEBUG", "false").lower() == "true",
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"GLOBAL ERROR: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": "An unexpected server error occurred.",
        },
    )


# ---------------------------------------------------------------------------
# CORS – allow Streamlit frontend and common dev origins
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup event: create DB tables and seed default users
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # Ensure data directories exist
    os.makedirs("data/audio", exist_ok=True)
    os.makedirs("data/transcripts", exist_ok=True)

    # Create all database tables
    try:
        from backend.database import init_db
        init_db()
    except Exception as e:
        print(f"[ERROR] DB init error: {e}")
        traceback.print_exc()

    # Seed default users if they don't exist
    try:
        from backend.database import SessionLocal
        from backend.models.user import User, UserRole
        from backend.core.security import hash_password

        db = SessionLocal()
        default_users = [
            {"name": "Admin", "email": "admin@test.com", "password": "admin123", "role": UserRole.ADMIN},
            {"name": "Manager", "email": "manager@test.com", "password": "manager123", "role": UserRole.MANAGER},
            {"name": "Monish", "email": "monish@test.com", "password": "monish123", "role": UserRole.EMPLOYEE},
        ]
        for u in default_users:
            if not db.query(User).filter(User.email == u["email"]).first():
                db.add(User(
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                ))
        db.commit()
        db.close()
        print("[OK] Default users seeded.")
    except Exception as e:
        print(f"[WARN] Seed error (non-fatal): {e}")
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------
from backend.routes import auth, transcription, nlp, tasks, meetings, notifications, alerts, escalation, calendar  # noqa: E402

app.include_router(auth.router)
app.include_router(transcription.router)
app.include_router(nlp.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(notifications.router)
app.include_router(alerts.router)
app.include_router(escalation.router)
app.include_router(calendar.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "running", "version": "1.0.0"}


@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Welcome to AI Meeting Intelligence API — visit /docs for the API explorer."}

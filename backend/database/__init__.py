import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Load .env from project root (two levels up from this file)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meeting_ai.db")

# For SQLite we must pass check_same_thread=False; safe for other dialects to ignore
_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Yield a SQLAlchemy session and ensure it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper: create all tables (called from main.py startup)
# ---------------------------------------------------------------------------
def init_db() -> None:
    """Import all models so they are registered on Base, then create tables."""
    # Models must be imported before create_all so SQLAlchemy knows about them.
    # noqa – these imports are side-effect imports; keep them here.
    import backend.models.user          # noqa: F401
    import backend.models.meeting       # noqa: F401
    import backend.models.task          # noqa: F401
    import backend.models.nlp_result    # noqa: F401
    import backend.models.notification  # noqa: F401
    from backend.database.models import CalendarEvent  # noqa: F401

    Base.metadata.create_all(bind=engine)
    # Lightweight, non-destructive SQLite upgrades for databases created by
    # earlier releases. New installations get these fields through create_all.
    if DATABASE_URL.startswith("sqlite"):
        existing = {row[1] for row in engine.connect().execute(text("PRAGMA table_info(meetings)"))}
        with engine.begin() as connection:
            if "processing_error" not in existing:
                connection.execute(text("ALTER TABLE meetings ADD COLUMN processing_error TEXT"))
            if "updated_at" not in existing:
                connection.execute(text("ALTER TABLE meetings ADD COLUMN updated_at DATETIME"))
        task_columns = {row[1] for row in engine.connect().execute(text("PRAGMA table_info(tasks)"))}
        with engine.begin() as connection:
            if "priority" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'"))
            if "source_excerpt" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN source_excerpt TEXT"))
            if "updated_at" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN updated_at DATETIME"))
    print("[OK] Database tables created / verified.")

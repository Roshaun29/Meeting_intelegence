from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from functools import lru_cache

from backend.database import get_db
from backend.models.meeting import Meeting, MeetingStatus
from backend.models.user import User
from backend.services.auth_service import get_current_user
# Retained as a module symbol for integrations that patch the legacy extractor;
# tasks are now deliberately created only after human review.
from utils.voice_task_extractor import extract_voice_tasks  # noqa: F401

ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "m4a", "webm"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024

router = APIRouter(prefix="/transcribe", tags=["Transcription"])


@lru_cache(maxsize=1)
def _get_whisper_model():
    """Lazy-load the Whisper model on first use so server starts fast."""
    try:
        import whisper
        print("[INFO] Loading Whisper base model (first request)...")
        return whisper.load_model("base")
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="openai-whisper is not installed. Run: pip install openai-whisper"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to load Whisper model: {exc}"
        )


@router.post("/")
async def transcribe_and_assign(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if not title or not title.strip():
            raise HTTPException(status_code=400, detail="Meeting title is required")

        file_name = (file.filename or "").strip()
        suffix = Path(file_name).suffix.lower().lstrip(".") if file_name else ""
        if not suffix or suffix not in ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Unsupported audio format. Please upload WAV, MP3, M4A, or WebM audio.",
            )

        project_root = Path(__file__).resolve().parent.parent.parent
        audio_dir = project_root / "data" / "audio"
        transcript_dir = project_root / "data" / "transcripts"

        audio_dir.mkdir(parents=True, exist_ok=True)
        transcript_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uuid.uuid4().hex}{Path(file_name).suffix.lower()}"
        filepath = audio_dir / filename

        with open(str(filepath), "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        if not filepath.exists() or filepath.stat().st_size == 0:
            filepath.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="The uploaded recording is empty.")
        if filepath.stat().st_size > MAX_UPLOAD_BYTES:
            filepath.unlink(missing_ok=True)
            raise HTTPException(status_code=413, detail="Recording exceeds the 200 MB upload limit.")

        meeting = Meeting(
            title=title.strip(), audio_path=str(filepath), uploaded_by=current_user.id,
            status=MeetingStatus.TRANSCRIBING, created_at=datetime.now(),
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        try:
            model = _get_whisper_model()
            result = model.transcribe(str(filepath))
        except HTTPException as exc:
            meeting.status = MeetingStatus.FAILED
            meeting.processing_error = exc.detail
            db.commit()
            raise
        except Exception as exc:
            meeting.status = MeetingStatus.FAILED
            meeting.processing_error = "Transcription could not be completed. Please retry with a valid recording."
            db.commit()
            raise HTTPException(status_code=503, detail=meeting.processing_error) from exc
        transcript_text = (result.get("text") or "").strip()
        if not transcript_text:
            meeting.status = MeetingStatus.FAILED
            meeting.processing_error = "Transcription produced no text."
            db.commit()
            raise HTTPException(status_code=400, detail="Transcription produced no text from the uploaded audio.")

        transcript_filename = f"{timestamp}.txt"
        transcript_path = transcript_dir / transcript_filename
        with open(str(transcript_path), "w", encoding="utf-8") as f:
            f.write(transcript_text)

        meeting.transcript = transcript_text
        meeting.status = MeetingStatus.COMPLETED
        meeting.processing_error = None
        db.commit()
        db.refresh(meeting)

        return {
            "status": "completed",
            "meeting_id": meeting.id,
            "transcript": transcript_text,
            "tasks_created": [],
            "total_tasks": 0,
            "review_required": True,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to process the recording.")

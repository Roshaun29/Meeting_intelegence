from functools import lru_cache
from pathlib import Path

import whisper
from fastapi import HTTPException, status

from backend.services.file_storage import ALLOWED_AUDIO_EXTENSIONS


@lru_cache(maxsize=1)
def get_whisper_model():
    try:
        return whisper.load_model("base")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load Whisper model",
        ) from exc


def clean_transcript_text(text: str) -> str:
    return " ".join(text.split())


def transcribe_audio_file(audio_file_path: str) -> tuple[str, str]:
    path = Path(audio_file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting audio file not found",
        )

    if path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file type for transcription",
        )

    try:
        model = get_whisper_model()
        result = model.transcribe(str(path))
        raw_text = (result.get("text") or "").strip()
        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Whisper returned an empty transcript",
            )
        cleaned_text = clean_transcript_text(raw_text)
        return raw_text, cleaned_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio with Whisper",
        ) from exc

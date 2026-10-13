from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


UPLOAD_DIR = Path("storage/uploads")
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}


def save_uploaded_audio(file: UploadFile) -> str:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only mp3, wav, and m4a files are allowed",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / unique_name

    try:
        contents = file.file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
        destination.write_bytes(contents)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        ) from exc
    finally:
        file.file.close()

    return str(destination.as_posix())

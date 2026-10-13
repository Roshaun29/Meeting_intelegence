from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.meeting import Meeting
from backend.models.user import User, UserRole
from backend.routes.auth import get_current_user
from backend.schemas.meeting import TranscriptResponse
from backend.services.preprocessing_service import preprocess_transcript_text


router = APIRouter(prefix="/meetings", tags=["Preprocessing"])


@router.post("/{meeting_id}/preprocess", response_model=TranscriptResponse)
def preprocess_meeting_transcript(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.TASK_GIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only task_giver users can clean transcripts",
        )

    meeting = (
        db.query(Meeting)
        .options(joinedload(Meeting.transcript))
        .filter(Meeting.id == meeting_id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    if not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generate a transcript before preprocessing",
        )

    meeting.transcript.cleaned_text = preprocess_transcript_text(meeting.transcript.raw_text)
    db.commit()
    db.refresh(meeting.transcript)
    return meeting.transcript

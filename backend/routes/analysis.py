from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.analysis_result import AnalysisResult
from backend.models.meeting import Meeting, MeetingStatus
from backend.models.user import User, UserRole
from backend.routes.auth import get_current_user
from backend.schemas.meeting import AnalysisResultResponse
from backend.services.summarization_service import build_meeting_notes, generate_summary


router = APIRouter(prefix="/meetings", tags=["Analysis"])


@router.post("/{meeting_id}/summarize", response_model=AnalysisResultResponse)
def summarize_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.TASK_GIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only task_giver users can generate summaries",
        )

    meeting = (
        db.query(Meeting)
        .options(joinedload(Meeting.transcript), joinedload(Meeting.analysis_result))
        .filter(Meeting.id == meeting_id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generate a transcript before summarizing the meeting",
        )

    source_text = (meeting.transcript.cleaned_text or meeting.transcript.raw_text or "").strip()
    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty and cannot be summarized",
        )

    summary = generate_summary(source_text)
    notes = build_meeting_notes(
        title=meeting.title,
        participants=meeting.participants_text,
        summary=summary,
        text=source_text,
    )

    if meeting.analysis_result:
        meeting.analysis_result.summary = summary
        meeting.analysis_result.notes = notes
        result = meeting.analysis_result
    else:
        result = AnalysisResult(meeting_id=meeting.id, summary=summary, notes=notes)
        db.add(result)

    meeting.status = MeetingStatus.ANALYZED
    db.commit()
    db.refresh(result)
    return result

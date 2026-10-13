from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.meeting import Meeting
from backend.models.user import User, UserRole
from backend.services.auth_service import get_current_user
from backend.models.task import Task
import json

router = APIRouter(prefix="/meetings", tags=["Meetings"])

def can_view(meeting: Meeting, user: User, db: Session) -> bool:
    if user.role in (UserRole.ADMIN, UserRole.MANAGER) or meeting.uploaded_by == user.id:
        return True
    return db.query(Task.id).filter(Task.meeting_id == meeting.id, Task.assigned_to_user_id == user.id).first() is not None


@router.get("/")
def get_all_meetings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "audio_path": m.audio_path,
            "created_by": m.created_by,
            "created_at": m.created_at,
            "transcript_snippet": m.transcript[:200] + "..." if m.transcript else "No transcript"
        }
        for m in meetings if can_view(m, current_user, db)
    ]

@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not can_view(m, current_user, db):
        raise HTTPException(status_code=403, detail="You do not have access to this meeting")
    
    nlp = m.nlp_results
    return {
        "id": m.id,
        "title": m.title,
        "audio_path": m.audio_path,
        "transcript": m.transcript,
        "created_at": m.created_at,
        "nlp_results": {
            "summary": nlp.summary if nlp else None,
            "action_items": json.loads(nlp.action_items) if nlp and nlp.action_items else [],
            "decisions": json.loads(nlp.decisions) if nlp and nlp.decisions else [],
            "risks": json.loads(nlp.risks) if nlp and nlp.risks else [],
            "sentiment": nlp.sentiment if nlp else None,
            "productivity_score": nlp.productivity_score if nlp else None,
            "deadlines": json.loads(nlp.deadlines) if nlp and nlp.deadlines else [],
            "assignments": json.loads(nlp.assignments) if nlp and nlp.assignments else []
        } if nlp else None
    }

@router.get("/{meeting_id}/tasks")
def get_meeting_tasks(meeting_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not can_view(meeting, current_user, db):
        raise HTTPException(status_code=403, detail="You do not have access to this meeting")
    tasks = db.query(Task).filter(Task.meeting_id == meeting_id).all()
    if current_user.role == UserRole.EMPLOYEE:
        tasks = [task for task in tasks if task.assigned_to_user_id == current_user.id]
    return [
        {
            "id": t.id,
            "description": t.description,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "deadline": t.deadline
        }
        for t in tasks
    ]

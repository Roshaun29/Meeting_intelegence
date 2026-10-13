from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.meeting import Meeting
from backend.models.note import Note
from backend.models.task import Task
from backend.models.user import User, UserRole
from backend.routes.auth import get_current_user
from backend.schemas.meeting import NoteCreateRequest, NoteResponse


router = APIRouter(tags=["Notes"])


@router.post("/notes", response_model=NoteResponse)
def create_note(
    payload: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).filter(Meeting.id == payload.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role == UserRole.TASK_ASSIGNEE:
        has_task_access = (
            db.query(Task)
            .filter(Task.meeting_id == payload.meeting_id, Task.assigned_to_user_id == current_user.id)
            .first()
        )
        if not has_task_access:
            raise HTTPException(status_code=403, detail="You do not have access to add notes for this meeting")

    note = Note(meeting_id=payload.meeting_id, user_id=current_user.id, content=payload.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteResponse(
        id=note.id,
        meeting_id=note.meeting_id,
        user_id=note.user_id,
        content=note.content,
        created_at=note.created_at,
        meeting_title=meeting.title,
        author_name=current_user.name,
    )


@router.get("/notes", response_model=list[NoteResponse])
def list_notes(
    meeting_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Note).options(joinedload(Note.meeting), joinedload(Note.user))

    if current_user.role == UserRole.TASK_GIVER:
        if meeting_id is not None:
            query = query.filter(Note.meeting_id == meeting_id)
        notes = query.order_by(Note.created_at.desc()).all()
    else:
        allowed_meeting_ids = {
            task.meeting_id
            for task in db.query(Task).filter(Task.assigned_to_user_id == current_user.id).all()
        }
        if not allowed_meeting_ids:
            query = query.filter(Note.user_id == current_user.id)
        else:
            query = query.filter((Note.user_id == current_user.id) | (Note.meeting_id.in_(allowed_meeting_ids)))
        if meeting_id is not None:
            query = query.filter(Note.meeting_id == meeting_id)
        notes = query.order_by(Note.created_at.desc()).all()

    return [
        NoteResponse(
            id=note.id,
            meeting_id=note.meeting_id,
            user_id=note.user_id,
            content=note.content,
            created_at=note.created_at,
            meeting_title=note.meeting.title if note.meeting else None,
            author_name=note.user.name if note.user else None,
        )
        for note in notes
    ]

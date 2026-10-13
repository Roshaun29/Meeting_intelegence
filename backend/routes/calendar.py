"""Persisted internal calendar API (external providers are intentionally optional)."""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import CalendarEvent, User, UserRole
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class EventInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = "UTC"
    description: str | None = Field(default=None, max_length=5000)
    meeting_id: int | None = None


def can_manage(event: CalendarEvent, user: User) -> bool:
    return user.role in (UserRole.ADMIN, UserRole.MANAGER) or event.created_by_user_id == user.id


def serialize(event: CalendarEvent) -> dict:
    return {"id": event.id, "title": event.title, "starts_at": event.starts_at,
            "ends_at": event.ends_at, "timezone": event.timezone, "description": event.description,
            "meeting_id": event.meeting_id, "task_id": event.task_id,
            "created_by_user_id": event.created_by_user_id}


@router.get("/")
def list_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    events = db.query(CalendarEvent).order_by(CalendarEvent.starts_at.asc()).all()
    if current_user.role == UserRole.EMPLOYEE:
        events = [e for e in events if e.created_by_user_id == current_user.id]
    return [serialize(event) for event in events]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ZoneInfo(payload.timezone)
    except Exception as exc:
        raise HTTPException(400, "Invalid timezone") from exc
    if payload.ends_at and payload.ends_at <= payload.starts_at:
        raise HTTPException(400, "Event end must be after its start")
    event = CalendarEvent(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(event); db.commit(); db.refresh(event)
    return serialize(event)


@router.put("/{event_id}")
def update_event(event_id: int, payload: EventInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(404, "Calendar event not found")
    if not can_manage(event, current_user):
        raise HTTPException(403, "You cannot edit this event")
    if payload.ends_at and payload.ends_at <= payload.starts_at:
        raise HTTPException(400, "Event end must be after its start")
    for key, value in payload.model_dump().items(): setattr(event, key, value)
    db.commit(); db.refresh(event)
    return serialize(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(404, "Calendar event not found")
    if not can_manage(event, current_user):
        raise HTTPException(403, "You cannot delete this event")
    db.delete(event); db.commit()

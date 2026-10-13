from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.meeting import Meeting
from backend.models.task import Task, TaskPriority
from backend.models.user import User, UserRole
from backend.routes.auth import get_current_user
from backend.schemas.meeting import (
    TaskAssigneeOption,
    TaskExtractionResponse,
    TaskResponse,
    TaskSaveRequest,
    TaskStatusUpdateRequest,
)
from backend.services.notification_service import (
    create_task_assignment_notification,
    create_task_completed_notification,
)
from backend.services.reminder_service import classify_reminder
from backend.services.task_extraction_service import extract_tasks_from_text


router = APIRouter(prefix="/tasks", tags=["Tasks"])


def require_manager_or_admin(current_user: User) -> None:
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers or admins can manage tasks",
        )


def serialize_task(task: Task) -> TaskResponse:
    reminder_status, due_date = classify_reminder(
        task.deadline,
        task.status.value if hasattr(task.status, "value") else task.status,
    )
    assigned_to_name = task.assignee.username if getattr(task, "assignee", None) else None
    meeting_title = task.meeting.title if getattr(task, "meeting", None) else None
    return TaskResponse(
        id=task.id,
        meeting_id=task.meeting_id,
        description=task.description,
        title=task.title,
        assigned_to=task.assigned_to,
        assigned_by=task.assigned_by,
        deadline=task.deadline,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        created_at=task.created_at,
        meeting_title=meeting_title,
        assigned_to_name=assigned_to_name,
        reminder_status=reminder_status,
        due_date_iso=due_date.isoformat() if due_date else None,
        assigned_by_voice=task.assigned_by_voice,
        confirmed=bool(task.confirmed),
        source=task.source,
        priority=task.priority.value if hasattr(task.priority, "value") else task.priority,
    )


@router.get("/assignees", response_model=list[TaskAssigneeOption])
def list_task_assignees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).filter(User.role.in_([UserRole.EMPLOYEE, UserRole.MANAGER])).order_by(User.username.asc()).all()
    return [TaskAssigneeOption(id=user.id, username=user.username) for user in users]


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Task).options(joinedload(Task.meeting), joinedload(Task.assignee))
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Task.assigned_to == current_user.id)
    tasks = query.order_by(Task.created_at.desc()).all()
    return [serialize_task(task) for task in tasks]


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .options(joinedload(Task.meeting), joinedload(Task.assignee))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == UserRole.EMPLOYEE and task.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update tasks assigned to you",
        )

    previous_status = task.status.value if hasattr(task.status, "value") else task.status
    task.status = payload.status
    if payload.status == "done" and previous_status != "done":
        create_task_completed_notification(db, task, task.assigned_by)
    db.commit()
    db.refresh(task)
    return serialize_task(task)


@router.post("/meeting/{meeting_id}/extract", response_model=TaskExtractionResponse)
def extract_tasks(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager_or_admin(current_user)

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript missing",
        )

    transcript_text = meeting.transcript.strip()
    if not transcript_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty",
        )

    assignees = [
        TaskAssigneeOption(id=user.id, username=user.username)
        for user in db.query(User).filter(User.role.in_([UserRole.EMPLOYEE, UserRole.MANAGER])).all()
    ]
    # In earlier meeting model, participants_text was removed, let's just pass None
    extracted_tasks = extract_tasks_from_text(transcript_text, None, assignees)
    return TaskExtractionResponse(meeting_id=meeting.id, extracted_tasks=extracted_tasks)


@router.post("/meeting/{meeting_id}/save", response_model=list[TaskResponse])
def save_extracted_tasks(
    meeting_id: int,
    payload: TaskSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager_or_admin(current_user)

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    valid_assignee_ids = {
        user.id: user
        for user in db.query(User).all()
    }

    # Draft approval is idempotent: rerunning an extraction must not duplicate
    # the same task for a meeting.
    db_tasks = []
    for draft in payload.tasks:
        if draft.assigned_to is not None and draft.assigned_to not in valid_assignee_ids:
            raise HTTPException(status_code=400, detail=f"Unknown assignee id {draft.assigned_to}")

        existing = db.query(Task).filter(
            Task.meeting_id == meeting_id,
            Task.description == draft.description.strip(),
        ).first()
        if existing:
            db_tasks.append(existing)
            continue

        task = Task(
            meeting_id=meeting_id,
            title=draft.title or draft.description[:255],
            description=draft.description,
            assigned_to=draft.assigned_to,
            assigned_by=current_user.id,
            deadline=draft.deadline,
            status=draft.status,
            source=draft.source,
            confirmed=draft.confirmed,
            priority=TaskPriority(draft.priority),
        )
        db.add(task)
        db_tasks.append(task)
        
    db.commit()
    for task in db_tasks:
        db.refresh(task)
        if task.assigned_to:
            create_task_assignment_notification(db, task, valid_assignee_ids[task.assigned_to])

    db.commit()  # persist assignment notifications created after the task commit
    refreshed_tasks = (
        db.query(Task)
        .options(joinedload(Task.meeting), joinedload(Task.assignee))
        .filter(Task.meeting_id == meeting_id)
        .order_by(Task.created_at.asc())
        .all()
    )
    return [serialize_task(task) for task in refreshed_tasks]


@router.post("/{task_id}/confirm", response_model=TaskResponse)
def confirm_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager_or_admin(current_user)
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    task.confirmed = 1
    task.status = "pending"
    db.commit()
    db.refresh(task)
    
    if task.assigned_to:
        assignee = db.query(User).filter(User.id == task.assigned_to).first()
        if assignee:
            create_task_assignment_notification(db, task, assignee)
            
    return serialize_task(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_manager_or_admin(current_user)
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return None

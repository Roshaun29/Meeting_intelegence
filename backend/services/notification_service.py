from sqlalchemy.orm import Session

from backend.models.notification import Notification, NotificationType
from backend.models.task import Task
from backend.models.user import User
from backend.services.reminder_service import classify_reminder


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False,
    )
    db.add(notification)
    db.flush()
    return notification


def notification_exists(db: Session, user_id: int, title: str, message: str) -> bool:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.message == message,
        )
        .first()
        is not None
    )


def create_task_assignment_notification(db: Session, task: Task, assignee: User | None) -> None:
    if not assignee:
        return
    title = "New Task Assigned"
    meeting_title = task.meeting.title if getattr(task, "meeting", None) else "a meeting"
    message = f"New task assigned: '{task.description}' due by {task.deadline or 'TBD'} (Meeting: {meeting_title})."
    if not notification_exists(db, assignee.id, title, message):
        create_notification(db, assignee.id, title, message, NotificationType.INFO)


def create_task_completed_notification(db: Session, task: Task, task_giver_id: int) -> None:
    title = "Task Completed"
    assignee_name = task.assignee.username if getattr(task, "assignee", None) else "an assignee"
    message = f"Task '{task.description}' was marked as completed by {assignee_name}."
    if not notification_exists(db, task_giver_id, title, message):
        create_notification(db, task_giver_id, title, message, NotificationType.SUCCESS)


def sync_deadline_notifications(db: Session, user: User, tasks: list[Task]) -> None:
    for task in tasks:
        status_value = task.status.value if hasattr(task.status, "value") else task.status
        reminder_status, _ = classify_reminder(task.deadline, status_value)
        if reminder_status == "due_soon":
            title = "Deadline Approaching"
            message = f"Task '{task.title or task.description}' is due soon ({task.deadline})."
            notification_type = NotificationType.WARNING
        elif reminder_status == "overdue":
            title = "Task Overdue"
            message = f"Task '{task.title or task.description}' is overdue ({task.deadline})."
            notification_type = NotificationType.WARNING
        else:
            continue

        if user.role.value if hasattr(user.role, 'value') else user.role == "task_giver":
            owner_id = task.assigned_by_user_id
        else:
            owner_id = user.id

        if not notification_exists(db, owner_id, title, message):
            create_notification(db, owner_id, title, message, notification_type)

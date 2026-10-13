from datetime import datetime
from typing import Literal, List, Optional

from pydantic import BaseModel, ConfigDict


MeetingStatusValue = Literal["uploaded", "transcribed", "analyzed"]
TaskStatusValue = Literal["pending_approval", "pending", "in_progress", "blocked", "done"]
ReminderStatusValue = Literal["due_today", "due_soon", "overdue", "upcoming", "no_deadline", "completed"]


class TaskAssigneeOption(BaseModel):
    id: int
    username: str


class ExtractedTaskDraft(BaseModel):
    title: Optional[str] = None
    description: str
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    deadline: Optional[str] = None
    status: TaskStatusValue = "pending_approval"
    assigned_by_voice: Optional[str] = None
    source: str = "manual"
    confirmed: bool = False
    priority: Literal["low", "medium", "high", "urgent"] = "medium"


class TaskSaveRequest(BaseModel):
    tasks: List[ExtractedTaskDraft]


class TaskExtractionResponse(BaseModel):
    meeting_id: int
    extracted_tasks: List[ExtractedTaskDraft]


class TaskResponse(BaseModel):
    id: int
    meeting_id: int
    description: str
    title: Optional[str] = None
    assigned_to: Optional[int]
    assigned_by: Optional[int]
    deadline: Optional[str]
    status: TaskStatusValue
    created_at: datetime

    assigned_by_voice: Optional[str] = None
    confirmed: bool = False
    source: str = "manual"
    priority: Optional[str] = "medium"

    meeting_title: Optional[str] = None
    assigned_to_name: Optional[str] = None
    reminder_status: Optional[ReminderStatusValue] = None
    due_date_iso: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatusValue


class NLPResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    meeting_id: int
    summary: Optional[str]
    action_items: Optional[str]
    decisions: Optional[str]
    risks: Optional[str]
    sentiment: Optional[str]
    productivity_score: Optional[int]
    deadlines: Optional[str]
    assignments: Optional[str]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    audio_path: Optional[str]
    transcript: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    nlp_results: Optional[NLPResultResponse] = None
    tasks: List[TaskResponse] = []

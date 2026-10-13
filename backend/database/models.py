"""
backend/database/models.py
==========================
Unified SQLAlchemy ORM models for the AI Meeting Intelligence platform.

All models live here so that:
  - `Base.metadata.create_all()` sees every table in a single import.
  - The rest of the codebase can do `from backend.database.models import User, Meeting, …`

Table overview
--------------
  users              – platform users with role-based access
  classrooms         – logical groupings of users (team / workspace)
  classroom_members  – many-to-many link between users and classrooms
  meetings           – uploaded meeting recordings & their analysis state
  tasks              – action-items extracted from meetings
  notifications      – in-app alerts for individual users
  nlp_results        – (kept for backward compat) NLP analysis output per meeting
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    ADMIN    = "admin"
    MANAGER  = "manager"
    EMPLOYEE = "employee"


class MeetingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    # Backwards-compatible names used by older rows/routes.
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"


class TaskStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    PENDING          = "pending"
    IN_PROGRESS      = "in_progress"
    DONE             = "done"
    BLOCKED          = "blocked"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, enum.Enum):
    INFO    = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR   = "error"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    """
    Platform user.

    Columns
    -------
    id               – surrogate PK
    email            – unique login identifier (replaces legacy 'username')
    name             – display name
    hashed_password  – bcrypt hash (also exposed as password_hash alias column)
    role             – admin | manager | employee
    classroom_id     – optional primary classroom affiliation (FK → classrooms)
    created_at       – record creation timestamp
    """

    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    name            = Column(String(255), nullable=False, default="")
    # Stored as hashed_password; 'password_hash' property for backward compatibility
    hashed_password = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    classroom_id    = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # ------------------------------------------------------------------
    # Backward-compat property: many old modules read/write .password_hash
    # ------------------------------------------------------------------
    @property
    def password_hash(self) -> str:
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        self.hashed_password = value

    # ------------------------------------------------------------------
    # Backward-compat property: some old views use .username → email
    # ------------------------------------------------------------------
    @property
    def username(self) -> str:
        return self.email

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    primary_classroom   = relationship("Classroom", back_populates="members_via_fk", foreign_keys=[classroom_id])
    classroom_memberships = relationship("ClassroomMember", back_populates="user")

    meetings_uploaded   = relationship("Meeting", back_populates="uploader",  foreign_keys="Meeting.uploaded_by")
    assigned_tasks      = relationship("Task",    back_populates="assignee",   foreign_keys="Task.assigned_to_user_id")
    given_tasks         = relationship("Task",    back_populates="assigner",   foreign_keys="Task.assigned_by_user_id")
    notifications       = relationship("Notification", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


# ---------------------------------------------------------------------------
# Classroom
# ---------------------------------------------------------------------------

class Classroom(Base):
    """
    Logical workspace / team grouping users together.

    Columns
    -------
    id        – surrogate PK
    name      – human-readable workspace name
    admin_id  – FK to the User who owns/administers this classroom
    created_at
    """

    __tablename__ = "classrooms"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(255), nullable=False)
    admin_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # Relationships
    admin            = relationship("User", foreign_keys=[admin_id])
    members_via_fk   = relationship("User", back_populates="primary_classroom", foreign_keys="User.classroom_id")
    classroom_members = relationship("ClassroomMember", back_populates="classroom", cascade="all, delete-orphan")
    meetings         = relationship("Meeting", back_populates="classroom", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Classroom id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# ClassroomMember  (many-to-many link table with extra role_label)
# ---------------------------------------------------------------------------

class ClassroomMember(Base):
    """
    Junction table: which users belong to which classrooms and with what label.

    Columns
    -------
    id           – surrogate PK
    classroom_id – FK → classrooms
    user_id      – FK → users
    role_label   – free-text label (e.g. 'host', 'participant', 'viewer')
    """

    __tablename__ = "classroom_members"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id"),      nullable=False)
    role_label   = Column(String(100), nullable=True, default="participant")

    # Relationships
    classroom = relationship("Classroom", back_populates="classroom_members")
    user      = relationship("User",      back_populates="classroom_memberships")

    def __repr__(self) -> str:
        return f"<ClassroomMember classroom={self.classroom_id} user={self.user_id} label={self.role_label!r}>"


# ---------------------------------------------------------------------------
# Meeting
# ---------------------------------------------------------------------------

class Meeting(Base):
    """
    Uploaded meeting recording with its analysis artefacts.

    Columns
    -------
    id            – surrogate PK
    classroom_id  – FK → classrooms (optional: standalone meeting)
    uploaded_by   – FK → users (who uploaded)
    audio_path    – filesystem path / URL to the audio file
    transcript    – raw Whisper output text
    summary       – BART-generated summary (populated after analysis)
    status        – pending | processing | done
    created_at

    Legacy aliases (kept for backward compat)
    ------------------------------------------
    title         – Column still present; older code reads .title
    created_by    – property alias → uploaded_by
    """

    __tablename__ = "meetings"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    title        = Column(String(255), nullable=False, default="Untitled Meeting")
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    uploaded_by  = Column(Integer, ForeignKey("users.id"),      nullable=True)
    audio_path   = Column(String(500), nullable=True)
    transcript   = Column(Text, nullable=True)
    summary      = Column(Text, nullable=True)
    status       = Column(Enum(MeetingStatus), nullable=False, default=MeetingStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at   = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # ------------------------------------------------------------------
    # Backward-compat: old code reads .created_by (used to be the column name)
    # ------------------------------------------------------------------
    @property
    def created_by(self) -> int | None:
        return self.uploaded_by

    @created_by.setter
    def created_by(self, value: int | None) -> None:
        self.uploaded_by = value

    # Relationships
    classroom  = relationship("Classroom",  back_populates="meetings", foreign_keys=[classroom_id])
    uploader   = relationship("User",       back_populates="meetings_uploaded", foreign_keys=[uploaded_by])
    tasks      = relationship("Task",       back_populates="meeting", cascade="all, delete-orphan")
    nlp_results = relationship("NLPResult", back_populates="meeting", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Meeting id={self.id} title={self.title!r} status={self.status}>"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(Base):
    """
    Action-item extracted from a meeting, assigned to a user.

    Columns
    -------
    id                  – surrogate PK
    meeting_id          – FK → meetings
    assigned_to_user_id – FK → users (who must do it)
    assigned_by_user_id – FK → users (who created it)
    title               – short task label
    description         – full description / instruction
    due_date            – deadline string (natural language or ISO date)
    status              – pending_approval | pending | in_progress | done
    created_at

    Legacy aliases
    --------------
    assigned_to      → assigned_to_user_id
    assigned_by      → assigned_by_user_id
    deadline         → due_date
    assigned_by_voice, source, confirmed  – kept for voice-task pipeline
    """

    __tablename__ = "tasks"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id          = Column(Integer, ForeignKey("meetings.id"),  nullable=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"),     nullable=True)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"),     nullable=True)
    title               = Column(String(255), nullable=True, default="")
    description         = Column(Text, nullable=False, default="")
    due_date            = Column(String(100), nullable=True)
    priority            = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    source_excerpt      = Column(Text, nullable=True)

    # Voice-extraction pipeline extras
    assigned_by_voice   = Column(String(255), nullable=True)
    source              = Column(String(50),  default="manual")
    confirmed           = Column(Boolean,     default=False)

    status     = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ------------------------------------------------------------------
    # Backward-compat properties (old code used assigned_to / assigned_by / deadline)
    # ------------------------------------------------------------------
    @property
    def assigned_to(self) -> int | None:
        return self.assigned_to_user_id

    @assigned_to.setter
    def assigned_to(self, v: int | None) -> None:
        self.assigned_to_user_id = v

    @property
    def assigned_by(self) -> int | None:
        return self.assigned_by_user_id

    @assigned_by.setter
    def assigned_by(self, v: int | None) -> None:
        self.assigned_by_user_id = v

    @property
    def deadline(self) -> str | None:
        return self.due_date

    @deadline.setter
    def deadline(self, v: str | None) -> None:
        self.due_date = v

    # Relationships
    meeting  = relationship("Meeting", back_populates="tasks")
    assignee = relationship("User",    back_populates="assigned_tasks", foreign_keys=[assigned_to_user_id])
    assigner = relationship("User",    back_populates="given_tasks",    foreign_keys=[assigned_by_user_id])

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status} to={self.assigned_to_user_id}>"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notification(Base):
    """
    In-app notification delivered to a single user.

    Columns
    -------
    id         – surrogate PK
    user_id    – FK → users
    message    – notification body text
    is_read    – whether the user has dismissed it
    created_at

    Extra columns kept for compat: title, type
    """

    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(255), nullable=True)
    message    = Column(Text, nullable=False)
    type       = Column(Enum(NotificationType), default=NotificationType.INFO)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user={self.user_id} read={self.is_read}>"


class CalendarEvent(Base):
    """Internal calendar event; task deadlines may be linked through task_id."""

    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    starts_at = Column(DateTime, nullable=False, index=True)
    ends_at = Column(DateTime, nullable=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    description = Column(Text, nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, unique=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = relationship("Meeting", foreign_keys=[meeting_id])
    task = relationship("Task", foreign_keys=[task_id])
    creator = relationship("User", foreign_keys=[created_by_user_id])


# ---------------------------------------------------------------------------
# NLPResult  (kept for backward compatibility with routes/nlp.py)
# ---------------------------------------------------------------------------

class NLPResult(Base):
    """
    Stores the structured NLP output for a single meeting.
    All list-type fields (action_items, decisions, etc.) are JSON strings.
    """

    __tablename__ = "nlp_results"

    meeting_id        = Column(Integer, ForeignKey("meetings.id"), primary_key=True)
    summary           = Column(Text, nullable=True)
    action_items      = Column(Text, nullable=True)
    decisions         = Column(Text, nullable=True)
    risks             = Column(Text, nullable=True)
    sentiment         = Column(String(50), nullable=True)
    productivity_score = Column(Integer,   nullable=True)
    deadlines         = Column(Text, nullable=True)
    assignments       = Column(Text, nullable=True)

    # Relationship
    meeting = relationship("Meeting", back_populates="nlp_results")

    def __repr__(self) -> str:
        return f"<NLPResult meeting={self.meeting_id} sentiment={self.sentiment!r}>"

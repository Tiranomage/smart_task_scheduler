from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: int = 3  # 1-5 scale
    urgent: bool = False
    important: bool = False
    estimated_duration: int = 30  # in minutes
    source: str = "manual"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[int] = None
    urgent: Optional[bool] = None
    important: Optional[bool] = None
    status: Optional[TaskStatus] = None
    estimated_duration: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    actual_duration: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DailyScheduleItem(BaseModel):
    task_id: int
    title: str
    start_time: datetime
    end_time: datetime
    duration: int  # in minutes

class DailySchedule(BaseModel):
    date: str
    schedule: List[DailyScheduleItem]

class ProductivityReport(BaseModel):
    period: str
    total_tasks: int
    completed_tasks: int
    productivity_percentage: float
    insights: List[str]
    recommendations: List[str]

class GoogleCalendarCredentials(BaseModel):
    access_token: str
    refresh_token: str
    calendar_id: str = "primary"

class PomodoroTimer(BaseModel):
    work_duration: int = 25  # in minutes
    break_duration: int = 5  # in minutes
    long_break_duration: int = 15  # in minutes
    sessions_before_long_break: int = 4
    current_session: int = 1
    remaining_time: int = 0  # in seconds
    is_working: bool = True
    is_active: bool = False
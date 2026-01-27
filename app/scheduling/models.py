"""
Scheduling Models
Data structures for scheduled jobs, recurrence, and executions.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date, time
from enum import Enum
import uuid


class JobType(str, Enum):
    VIDEO_GENERATION = "video_generation"
    BATCH_GENERATION = "batch_generation"
    SCRIPT_GENERATION = "script_generation"
    CAPTION_GENERATION = "caption_generation"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    EXPORT = "export"


class ScheduleType(str, Enum):
    ONCE = "once"
    RECURRING = "recurring"


class ScheduleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class Frequency(str, Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class MissedPolicy(str, Enum):
    RUN_ALL = "run_all"
    RUN_LATEST = "run_latest"
    SKIP = "skip"


@dataclass
class RecurrenceRule:
    """Recurrence rule for recurring schedules"""
    frequency: Frequency
    interval: int = 1
    days_of_week: List[int] = field(default_factory=list)  # 1-7 (Mon-Sun)
    days_of_month: List[int] = field(default_factory=list)  # 1-31
    months: List[int] = field(default_factory=list)  # 1-12
    time_of_day: str = "09:00"  # HH:MM
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    count: Optional[int] = None
    exceptions: List[date] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "frequency": self.frequency.value,
            "interval": self.interval,
            "days_of_week": self.days_of_week,
            "days_of_month": self.days_of_month,
            "time_of_day": self.time_of_day,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "count": self.count
        }


@dataclass
class ScheduledJob:
    """Scheduled job model"""
    schedule_id: str
    user_id: str
    name: str
    job_type: JobType
    job_config: Dict
    schedule_type: ScheduleType
    scheduled_at: Optional[datetime] = None
    recurrence_rule: Optional[RecurrenceRule] = None
    timezone: str = "UTC"
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    priority: Priority = Priority.NORMAL
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    missed_policy: MissedPolicy = MissedPolicy.SKIP
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "schedule_id": self.schedule_id,
            "name": self.name,
            "description": self.description,
            "job_type": self.job_type.value,
            "schedule_type": self.schedule_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "timezone": self.timezone,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "recurrence_rule": self.recurrence_rule.to_dict() if self.recurrence_rule else None,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ScheduleExecution:
    """Execution record for a scheduled job"""
    execution_id: str
    schedule_id: str
    job_id: Optional[str] = None
    scheduled_for: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    is_manual: bool = False
    error_message: str = ""
    result_summary: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "schedule_id": self.schedule_id,
            "job_id": self.job_id,
            "scheduled_for": self.scheduled_for.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "is_manual": self.is_manual,
            "error_message": self.error_message
        }


@dataclass
class ScheduleSeries:
    """Series scheduling for content series"""
    series_id: str
    user_id: str
    name: str
    template_id: Optional[str] = None
    episode_count: int = 10
    recurrence_rule: Optional[RecurrenceRule] = None
    current_episode: int = 1
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "series_id": self.series_id,
            "name": self.name,
            "template_id": self.template_id,
            "episode_count": self.episode_count,
            "current_episode": self.current_episode,
            "status": self.status.value,
            "recurrence_rule": self.recurrence_rule.to_dict() if self.recurrence_rule else None
        }


# Common schedule patterns
SCHEDULE_PATTERNS = {
    "daily_9am": RecurrenceRule(frequency=Frequency.DAILY, time_of_day="09:00"),
    "weekdays_6pm": RecurrenceRule(frequency=Frequency.WEEKLY, days_of_week=[1,2,3,4,5], time_of_day="18:00"),
    "weekly_monday": RecurrenceRule(frequency=Frequency.WEEKLY, days_of_week=[1], time_of_day="10:00"),
    "twice_weekly": RecurrenceRule(frequency=Frequency.WEEKLY, days_of_week=[1,4], time_of_day="09:00"),
    "first_of_month": RecurrenceRule(frequency=Frequency.MONTHLY, days_of_month=[1], time_of_day="12:00"),
    "biweekly": RecurrenceRule(frequency=Frequency.WEEKLY, interval=2, days_of_week=[1], time_of_day="09:00")
}


def create_schedule_id() -> str:
    return str(uuid.uuid4())


def create_execution_id() -> str:
    return str(uuid.uuid4())

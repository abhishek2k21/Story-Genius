"""
Scheduling Service
Main scheduling operations.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import threading

from app.scheduling.models import (
    ScheduledJob, ScheduleExecution, ScheduleSeries, ScheduleType,
    ScheduleStatus, JobType, Priority, RecurrenceRule, Frequency,
    SCHEDULE_PATTERNS, create_schedule_id
)
from app.scheduling.recurrence import calculate_next_occurrence, get_next_n_occurrences, validate_recurrence_rule
from app.scheduling.executor import schedule_executor
from app.scheduling.calendar import get_calendar_view, get_upcoming_executions
from app.scheduling.bulk import bulk_pause, bulk_resume, bulk_cancel
from app.scheduling.timezone import to_utc, from_utc, is_valid_timezone


class SchedulingService:
    """Main scheduling service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._schedules: Dict[str, ScheduledJob] = {}
            cls._instance._series: Dict[str, ScheduleSeries] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_schedule(
        self,
        user_id: str,
        name: str,
        job_type: JobType,
        job_config: Dict,
        schedule_type: ScheduleType,
        scheduled_at: datetime = None,
        recurrence_rule: RecurrenceRule = None,
        timezone: str = "UTC",
        priority: Priority = Priority.NORMAL,
        max_runs: int = None,
        description: str = ""
    ) -> Tuple[Optional[ScheduledJob], str]:
        """Create a new schedule"""
        
        # Validate timezone
        if not is_valid_timezone(timezone):
            return None, f"Invalid timezone: {timezone}"
        
        # Validate recurrence if recurring
        if schedule_type == ScheduleType.RECURRING:
            if not recurrence_rule:
                return None, "Recurring schedule requires recurrence_rule"
            issues = validate_recurrence_rule(recurrence_rule)
            if issues:
                return None, f"Invalid recurrence: {', '.join(issues)}"
        
        # Validate one-time schedule
        if schedule_type == ScheduleType.ONCE:
            if not scheduled_at:
                return None, "One-time schedule requires scheduled_at"
            if scheduled_at <= datetime.utcnow():
                return None, "scheduled_at must be in the future"
        
        # Calculate next run
        if schedule_type == ScheduleType.ONCE:
            next_run = to_utc(scheduled_at, timezone) if timezone != "UTC" else scheduled_at
        else:
            next_run = calculate_next_occurrence(recurrence_rule)
        
        schedule = ScheduledJob(
            schedule_id=create_schedule_id(),
            user_id=user_id,
            name=name,
            job_type=job_type,
            job_config=job_config,
            schedule_type=schedule_type,
            scheduled_at=scheduled_at,
            recurrence_rule=recurrence_rule,
            timezone=timezone,
            priority=priority,
            max_runs=max_runs,
            description=description,
            next_run_at=next_run
        )
        
        with self._lock:
            self._schedules[schedule.schedule_id] = schedule
        
        schedule_executor.register_schedule(schedule)
        
        return schedule, "Schedule created"
    
    def get_schedule(self, schedule_id: str, user_id: str) -> Optional[ScheduledJob]:
        """Get schedule by ID"""
        schedule = self._schedules.get(schedule_id)
        if schedule and schedule.user_id == user_id:
            return schedule
        return None
    
    def list_schedules(
        self,
        user_id: str,
        status: ScheduleStatus = None,
        job_type: JobType = None
    ) -> List[ScheduledJob]:
        """List user's schedules"""
        schedules = [s for s in self._schedules.values() if s.user_id == user_id]
        
        if status:
            schedules = [s for s in schedules if s.status == status]
        if job_type:
            schedules = [s for s in schedules if s.job_type == job_type]
        
        return sorted(schedules, key=lambda s: s.created_at, reverse=True)
    
    def update_schedule(
        self,
        schedule_id: str,
        user_id: str,
        **kwargs
    ) -> Tuple[Optional[ScheduledJob], str]:
        """Update schedule"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return None, "Schedule not found"
        
        for key, value in kwargs.items():
            if value is not None and hasattr(schedule, key):
                setattr(schedule, key, value)
        
        # Recalculate next run if recurrence changed
        if "recurrence_rule" in kwargs and schedule.recurrence_rule:
            schedule.next_run_at = calculate_next_occurrence(schedule.recurrence_rule)
        
        schedule.updated_at = datetime.utcnow()
        return schedule, "Schedule updated"
    
    def delete_schedule(self, schedule_id: str, user_id: str) -> bool:
        """Delete schedule"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return False
        
        del self._schedules[schedule_id]
        schedule_executor.unregister_schedule(schedule_id)
        return True
    
    def pause_schedule(self, schedule_id: str, user_id: str) -> Tuple[Optional[ScheduledJob], str]:
        """Pause schedule"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return None, "Schedule not found"
        
        if schedule.status != ScheduleStatus.ACTIVE:
            return None, f"Cannot pause: {schedule.status.value}"
        
        schedule.status = ScheduleStatus.PAUSED
        schedule.updated_at = datetime.utcnow()
        return schedule, "Schedule paused"
    
    def resume_schedule(self, schedule_id: str, user_id: str) -> Tuple[Optional[ScheduledJob], str]:
        """Resume schedule"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return None, "Schedule not found"
        
        if schedule.status != ScheduleStatus.PAUSED:
            return None, f"Cannot resume: {schedule.status.value}"
        
        schedule.status = ScheduleStatus.ACTIVE
        
        # Recalculate next run
        if schedule.recurrence_rule:
            schedule.next_run_at = calculate_next_occurrence(schedule.recurrence_rule)
        
        schedule.updated_at = datetime.utcnow()
        return schedule, "Schedule resumed"
    
    def cancel_schedule(self, schedule_id: str, user_id: str) -> Tuple[Optional[ScheduledJob], str]:
        """Cancel schedule"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return None, "Schedule not found"
        
        if schedule.status in [ScheduleStatus.CANCELLED, ScheduleStatus.COMPLETED]:
            return None, f"Already: {schedule.status.value}"
        
        schedule.status = ScheduleStatus.CANCELLED
        schedule.next_run_at = None
        schedule.updated_at = datetime.utcnow()
        return schedule, "Schedule cancelled"
    
    def run_now(self, schedule_id: str, user_id: str) -> Tuple[Optional[ScheduleExecution], str]:
        """Execute schedule immediately"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return None, "Schedule not found"
        
        execution = schedule_executor.run_now(schedule)
        return execution, "Executed"
    
    def clone_schedule(
        self,
        schedule_id: str,
        user_id: str,
        new_name: str = None
    ) -> Tuple[Optional[ScheduledJob], str]:
        """Clone schedule"""
        original = self.get_schedule(schedule_id, user_id)
        if not original:
            return None, "Schedule not found"
        
        return self.create_schedule(
            user_id=user_id,
            name=new_name or f"{original.name} (Copy)",
            job_type=original.job_type,
            job_config=original.job_config.copy(),
            schedule_type=original.schedule_type,
            scheduled_at=original.scheduled_at,
            recurrence_rule=original.recurrence_rule,
            timezone=original.timezone,
            priority=original.priority,
            max_runs=original.max_runs,
            description=original.description
        )
    
    def get_executions(self, schedule_id: str, user_id: str, limit: int = 20) -> List[ScheduleExecution]:
        """Get execution history"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule:
            return []
        return schedule_executor.get_executions(schedule_id, limit)
    
    def get_next_occurrences(self, schedule_id: str, user_id: str, n: int = 10) -> List[datetime]:
        """Get next N occurrences"""
        schedule = self.get_schedule(schedule_id, user_id)
        if not schedule or not schedule.recurrence_rule:
            return []
        return get_next_n_occurrences(schedule.recurrence_rule, n)
    
    def get_calendar(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Get calendar view"""
        schedules = self.list_schedules(user_id)
        return get_calendar_view(schedules, start_date, end_date)
    
    def get_upcoming(self, user_id: str, limit: int = 10, hours: int = 24) -> List[Dict]:
        """Get upcoming executions"""
        schedules = self.list_schedules(user_id, status=ScheduleStatus.ACTIVE)
        return get_upcoming_executions(schedules, limit, hours)
    
    def get_patterns(self) -> List[Dict]:
        """Get common schedule patterns"""
        return [
            {"name": name, "rule": rule.to_dict()}
            for name, rule in SCHEDULE_PATTERNS.items()
        ]


scheduling_service = SchedulingService()

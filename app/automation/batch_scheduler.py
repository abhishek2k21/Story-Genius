"""
Batch Scheduler
Automated batch scheduling with cadence and retry windows.
"""
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BatchSchedule:
    """A scheduled batch job."""
    client_id: str
    batch_size: int
    
    # Cadence
    frequency: str  # "daily", "weekly"
    preferred_hours: List[int] = field(default_factory=lambda: [2, 3, 4])  # Off-peak
    
    # Retry
    retry_on_failure: bool = True
    retry_window_hours: int = 4
    max_retries: int = 2
    
    # State
    last_run: datetime = None
    next_scheduled: datetime = None
    consecutive_failures: int = 0
    is_paused: bool = False


class BatchScheduler:
    """
    Automated batch scheduling - no manual triggers.
    """
    
    def __init__(self):
        self._schedules: Dict[str, BatchSchedule] = {}
        self._batch_runner: Callable = None
    
    def set_batch_runner(self, runner: Callable):
        """Set the function to run batches."""
        self._batch_runner = runner
    
    def schedule_daily(
        self,
        client_id: str,
        batch_size: int = 10,
        preferred_hours: List[int] = None
    ):
        """Schedule daily batches for a client."""
        schedule = BatchSchedule(
            client_id=client_id,
            batch_size=batch_size,
            frequency="daily",
            preferred_hours=preferred_hours or [2, 3, 4]
        )
        schedule.next_scheduled = self._next_daily(schedule.preferred_hours)
        self._schedules[client_id] = schedule
        logger.info(f"Scheduled daily batch for {client_id[:8]}: {batch_size} videos")
    
    def schedule_weekly(
        self,
        client_id: str,
        batch_size: int = 50,
        day_of_week: int = 0  # Monday
    ):
        """Schedule weekly batches."""
        schedule = BatchSchedule(
            client_id=client_id,
            batch_size=batch_size,
            frequency="weekly"
        )
        schedule.next_scheduled = self._next_weekly(day_of_week, schedule.preferred_hours[0])
        self._schedules[client_id] = schedule
        logger.info(f"Scheduled weekly batch for {client_id[:8]}: {batch_size} videos")
    
    def _next_daily(self, preferred_hours: List[int]) -> datetime:
        """Calculate next daily run time."""
        now = datetime.utcnow()
        
        # Find next preferred hour
        for hour in sorted(preferred_hours):
            if now.hour < hour:
                return now.replace(hour=hour, minute=0, second=0)
        
        # Tomorrow at first preferred hour
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=preferred_hours[0], minute=0, second=0)
    
    def _next_weekly(self, day_of_week: int, hour: int) -> datetime:
        """Calculate next weekly run time."""
        now = datetime.utcnow()
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_date = now + timedelta(days=days_ahead)
        return next_date.replace(hour=hour, minute=0, second=0)
    
    def get_due_batches(self) -> List[str]:
        """Get client IDs with due batches."""
        now = datetime.utcnow()
        due = []
        
        for client_id, schedule in self._schedules.items():
            if schedule.is_paused:
                continue
            if schedule.next_scheduled and now >= schedule.next_scheduled:
                due.append(client_id)
        
        return due
    
    def run_due_batches(self) -> Dict:
        """Run all due batches."""
        if not self._batch_runner:
            return {"error": "No batch runner configured"}
        
        due = self.get_due_batches()
        results = {}
        
        for client_id in due:
            schedule = self._schedules[client_id]
            
            try:
                result = self._batch_runner(client_id, schedule.batch_size)
                schedule.last_run = datetime.utcnow()
                schedule.consecutive_failures = 0
                
                # Schedule next run
                if schedule.frequency == "daily":
                    schedule.next_scheduled = self._next_daily(schedule.preferred_hours)
                else:
                    schedule.next_scheduled = self._next_weekly(0, schedule.preferred_hours[0])
                
                results[client_id] = {"status": "success", "result": result}
                
            except Exception as e:
                schedule.consecutive_failures += 1
                
                if schedule.retry_on_failure and schedule.consecutive_failures <= schedule.max_retries:
                    # Schedule retry
                    retry_time = datetime.utcnow() + timedelta(hours=schedule.retry_window_hours)
                    schedule.next_scheduled = retry_time
                    results[client_id] = {"status": "retry_scheduled", "retry_at": retry_time.isoformat()}
                else:
                    # Pause after max retries
                    schedule.is_paused = True
                    results[client_id] = {"status": "paused", "error": str(e)}
                    logger.warning(f"Paused batch schedule for {client_id[:8]} after {schedule.consecutive_failures} failures")
        
        return results
    
    def pause(self, client_id: str):
        """Pause a schedule."""
        if client_id in self._schedules:
            self._schedules[client_id].is_paused = True
    
    def resume(self, client_id: str):
        """Resume a paused schedule."""
        if client_id in self._schedules:
            schedule = self._schedules[client_id]
            schedule.is_paused = False
            schedule.consecutive_failures = 0
    
    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            "total_schedules": len(self._schedules),
            "active": len([s for s in self._schedules.values() if not s.is_paused]),
            "paused": len([s for s in self._schedules.values() if s.is_paused]),
            "due_now": len(self.get_due_batches())
        }

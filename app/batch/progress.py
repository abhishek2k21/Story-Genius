"""
Progress Tracking System for Batch Processing
Tracks batch progress with ETA calculation.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, timedelta
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProgressReport:
    """Progress report for a batch"""
    batch_id: str
    total_items: int
    completed: int
    failed: int
    remaining: int
    progress_percent: float
    eta_seconds: Optional[float]
    current_velocity: float  # items per second
    started_at: datetime
    current_item: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "total_items": self.total_items,
            "completed": self.completed,
            "failed": self.failed,
            "remaining": self.remaining,
            "progress_percent": round(self.progress_percent, 2),
            "eta_seconds": round(self.eta_seconds, 1) if self.eta_seconds else None,
            "eta_human": self._format_eta(),
            "current_velocity": round(self.current_velocity, 2),
            "started_at": self.started_at.isoformat(),
            "current_item": self.current_item
        }
    
    def _format_eta(self) -> Optional[str]:
        """Format ETA in human-readable format"""
        if self.eta_seconds is None:
            return None
        
        if self.eta_seconds < 60:
            return f"{int(self.eta_seconds)}s"
        elif self.eta_seconds < 3600:
            minutes = int(self.eta_seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(self.eta_seconds / 3600)
            minutes = int((self.eta_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


class ProgressTracker:
    """
    Tracks progress of batch operations.
    """
    
    def __init__(self):
        # Store progress data for each batch
        self._batch_progress: Dict[str, Dict] = {}
        logger.info("ProgressTracker initialized")
    
    def start_batch(
        self,
        batch_id: str,
        total_items: int,
        metadata: Optional[Dict] = None
    ):
        """
        Start tracking a batch.
        
        Args:
            batch_id: Batch ID
            total_items: Total number of items
            metadata: Optional metadata
        """
        self._batch_progress[batch_id] = {
            "total_items": total_items,
            "completed": 0,
            "failed": 0,
            "started_at": datetime.utcnow(),
            "last_update": time.time(),
            "metadata": metadata or {},
            "current_item": None
        }
        
        logger.info(f"Started tracking batch {batch_id} ({total_items} items)")
    
    def update_progress(
        self,
        batch_id: str,
        completed: Optional[int] = None,
        failed: Optional[int] = None,
        current_item: Optional[str] = None
    ):
        """
        Update batch progress.
        
        Args:
            batch_id: Batch ID
            completed: Number of completed items
            failed: Number of failed items
            current_item: Current item being processed
        """
        if batch_id not in self._batch_progress:
            logger.warning(f"Batch {batch_id} not being tracked")
            return
        
        progress = self._batch_progress[batch_id]
        
        if completed is not None:
            progress["completed"] = completed
        if failed is not None:
            progress["failed"] = failed
        if current_item is not None:
            progress["current_item"] = current_item
        
        progress["last_update"] = time.time()
        
        logger.debug(
            f"Batch {batch_id} progress: {progress['completed']}/{progress['total_items']} "
            f"({(progress['completed']/progress['total_items'])*100:.1f}%)"
        )
    
    def increment_completed(self, batch_id: str):
        """Increment completed count"""
        if batch_id in self._batch_progress:
            self._batch_progress[batch_id]["completed"] += 1
            self._batch_progress[batch_id]["last_update"] = time.time()
    
    def increment_failed(self, batch_id: str):
        """Increment failed count"""
        if batch_id in self._batch_progress:
            self._batch_progress[batch_id]["failed"] += 1
            self._batch_progress[batch_id]["last_update"] = time.time()
    
    def get_progress(self, batch_id: str) -> Optional[ProgressReport]:
        """
        Get progress report for batch.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            ProgressReport or None
        """
        if batch_id not in self._batch_progress:
            logger.warning(f"Batch {batch_id} not found")
            return None
        
        progress = self._batch_progress[batch_id]
        
        total = progress["total_items"]
        completed = progress["completed"]
        failed = progress["failed"]
        remaining = total - completed - failed
        
        # Calculate progress percentage
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        # Calculate velocity and ETA
        started_at = progress["started_at"]
        elapsed_seconds = (datetime.utcnow() - started_at).total_seconds()
        
        if elapsed_seconds > 0 and completed > 0:
            velocity = completed / elapsed_seconds  # items per second
            
            if velocity > 0:
                eta_seconds = remaining / velocity
            else:
                eta_seconds = None
        else:
            velocity = 0.0
            eta_seconds = None
        
        report = ProgressReport(
            batch_id=batch_id,
            total_items=total,
            completed=completed,
            failed=failed,
            remaining=remaining,
            progress_percent=progress_percent,
            eta_seconds=eta_seconds,
            current_velocity=velocity,
            started_at=started_at,
            current_item=progress.get("current_item")
        )
        
        return report
    
    def finish_batch(self, batch_id: str):
        """
        Mark batch as finished and cleanup.
        
        Args:
            batch_id: Batch ID
        """
        if batch_id in self._batch_progress:
            report = self.get_progress(batch_id)
            
            if report:
                duration = (datetime.utcnow() - report.started_at).total_seconds()
                logger.info(
                    f"Batch {batch_id} finished: "
                    f"{report.completed} completed, {report.failed} failed "
                    f"in {duration:.1f}s"
                )
            
            del self._batch_progress[batch_id]


class MilestoneNotifier:
    """
    Sends notifications at progress milestones.
    """
    
    MILESTONES = [25, 50, 75, 100]  # Percentage milestones
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self._notified_milestones: Dict[str, set] = {}
    
    def check_milestones(self, batch_id: str) -> list:
        """
        Check and trigger milestone notifications.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            List of triggered milestones
        """
        report = self.progress_tracker.get_progress(batch_id)
        if not report:
            return []
        
        # Initialize milestone tracking for batch
        if batch_id not in self._notified_milestones:
            self._notified_milestones[batch_id] = set()
        
        triggered = []
        
        for milestone in self.MILESTONES:
            if (report.progress_percent >= milestone and 
                milestone not in self._notified_milestones[batch_id]):
                
                # Trigger notification
                self._notify_milestone(batch_id, milestone, report)
                self._notified_milestones[batch_id].add(milestone)
                triggered.append(milestone)
        
        return triggered
    
    def _notify_milestone(
        self,
        batch_id: str,
        milestone: int,
        report: ProgressReport
    ):
        """Send milestone notification"""
        logger.info(
            f"Batch {batch_id} reached {milestone}% milestone "
            f"({report.completed}/{report.total_items} items)"
        )
        
        # In production: send email, webhook, etc.
        # Example: send_notification(batch_id, milestone, report)
    
    def cleanup_batch(self, batch_id: str):
        """Cleanup milestone tracking for batch"""
        if batch_id in self._notified_milestones:
            del self._notified_milestones[batch_id]


# Global instances
progress_tracker = ProgressTracker()
milestone_notifier = MilestoneNotifier(progress_tracker)

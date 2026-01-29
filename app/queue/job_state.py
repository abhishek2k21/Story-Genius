"""
Job State Management and Tracking
Tracks job states and provides visibility APIs.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class JobState(str, Enum):
    """Job state enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class StateTransition:
    """State transition record"""
    from_state: Optional[JobState]
    to_state: JobState
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "from_state": self.from_state.value if self.from_state else None,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class JobStatus:
    """Complete job status"""
    job_id: str
    task_name: str
    current_state: JobState
    progress: float  # 0-100
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    retry_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "current_state": self.current_state.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result,
            "retry_count": self.retry_count,
            "duration_seconds": self._calculate_duration()
        }
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate job duration"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds()
        return round(duration, 2)


class JobTracker:
    """
    Tracks job states and maintains audit log.
    In production, this would use a database.
    """
    
    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._transitions: Dict[str, List[StateTransition]] = {}
        logger.info("JobTracker initialized")
    
    def create_job(
        self,
        job_id: str,
        task_name: str,
        initial_state: JobState = JobState.PENDING
    ) -> JobStatus:
        """
        Create new job.
        
        Args:
            job_id: Unique job ID
            task_name: Task name
            initial_state: Initial state
        
        Returns:
            JobStatus
        """
        status = JobStatus(
            job_id=job_id,
            task_name=task_name,
            current_state=initial_state,
            progress=0.0,
            created_at=datetime.utcnow()
        )
        
        self._jobs[job_id] = status
        self._transitions[job_id] = []
        
        # Record initial transition
        self._record_transition(
            job_id,
            from_state=None,
            to_state=initial_state,
            metadata={"task_name": task_name}
        )
        
        logger.info(f"Job created: {job_id} ({task_name})")
        return status
    
    def update_state(
        self,
        job_id: str,
        new_state: JobState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[JobStatus]:
        """
        Update job state.
        
        Args:
            job_id: Job ID
            new_state: New state
            metadata: Optional metadata
        
        Returns:
            Updated JobStatus or None if not found
        """
        status = self._jobs.get(job_id)
        if not status:
            logger.warning(f"Job {job_id} not found")
            return None
        
        old_state = status.current_state
        status.current_state = new_state
        
        # Update timestamps
        if new_state == JobState.EXECUTING and not status.started_at:
            status.started_at = datetime.utcnow()
        elif new_state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
            status.completed_at = datetime.utcnow()
        
        # Record transition
        self._record_transition(
            job_id,
            from_state=old_state,
            to_state=new_state,
            metadata=metadata or {}
        )
        
        logger.info(f"Job {job_id}: {old_state.value} → {new_state.value}")
        return status
    
    def update_progress(
        self,
        job_id: str,
        progress: float
    ) -> Optional[JobStatus]:
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
        
        Returns:
            Updated JobStatus or None
        """
        status = self._jobs.get(job_id)
        if not status:
            return None
        
        status.progress = min(100, max(0, progress))
        logger.debug(f"Job {job_id} progress: {status.progress:.1f}%")
        return status
    
    def set_result(
        self,
        job_id: str,
        result: Any
    ) -> Optional[JobStatus]:
        """Set job result"""
        status = self._jobs.get(job_id)
        if status:
            status.result = result
        return status
    
    def set_error(
        self,
        job_id: str,
        error: str
    ) -> Optional[JobStatus]:
        """Set job error"""
        status = self._jobs.get(job_id)
        if status:
            status.error = error
        return status
    
    def increment_retry(self, job_id: str) -> Optional[JobStatus]:
        """Increment retry count"""
        status = self._jobs.get(job_id)
        if status:
            status.retry_count += 1
            logger.info(f"Job {job_id} retry count: {status.retry_count}")
        return status
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status"""
        return self._jobs.get(job_id)
    
    def get_history(self, job_id: str) -> List[StateTransition]:
        """Get job state transition history"""
        return self._transitions.get(job_id, [])
    
    def list_jobs(
        self,
        state: Optional[JobState] = None,
        limit: int = 100
    ) -> List[JobStatus]:
        """
        List jobs, optionally filtered by state.
        
        Args:
            state: Filter by state
            limit: Max results
        
        Returns:
            List of JobStatus
        """
        jobs = list(self._jobs.values())
        
        if state:
            jobs = [j for j in jobs if j.current_state == state]
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    def _record_transition(
        self,
        job_id: str,
        from_state: Optional[JobState],
        to_state: JobState,
        metadata: Dict[str, Any]
    ):
        """Record state transition"""
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        if job_id not in self._transitions:
            self._transitions[job_id] = []
        
        self._transitions[job_id].append(transition)


# Global instance
job_tracker = JobTracker()


# Example usage helper
def track_celery_task(task_id: str, task_name: str):
    """Helper to track Celery task"""
    return job_tracker.create_job(
        job_id=task_id,
        task_name=task_name,
        initial_state=JobState.QUEUED
    )

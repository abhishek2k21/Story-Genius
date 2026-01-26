"""
Dead Letter Queue Management
Handles jobs that fail permanently after exhausting retries.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
import os

from app.reliability.checkpointing import JobCheckpoint, CheckpointService
from app.reliability.retry import RetryAttempt, FailureType
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResolutionStatus(str, Enum):
    """Status of dead letter resolution"""
    PENDING_REVIEW = "pending_review"
    RETRIED = "retried"
    DISMISSED = "dismissed"


@dataclass
class DeadLetterEntry:
    """A job in the dead letter queue"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    job_type: str = ""
    
    # Original state
    config_snapshot: Dict = field(default_factory=dict)
    checkpoint: Optional[Dict] = None
    
    # Failure information
    failure_stage: str = ""
    failure_type: str = ""
    final_error: str = ""
    retry_attempts: List[Dict] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    final_failure_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    # Resolution
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING_REVIEW
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_type": self.job_type,
            "config_snapshot": self.config_snapshot,
            "checkpoint": self.checkpoint,
            "failure_stage": self.failure_stage,
            "failure_type": self.failure_type,
            "final_error": self.final_error,
            "retry_attempts": self.retry_attempts,
            "created_at": self.created_at.isoformat(),
            "final_failure_at": self.final_failure_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_status": self.resolution_status.value,
            "resolution_notes": self.resolution_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DeadLetterEntry":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            job_id=data.get("job_id", ""),
            job_type=data.get("job_type", ""),
            config_snapshot=data.get("config_snapshot", {}),
            checkpoint=data.get("checkpoint"),
            failure_stage=data.get("failure_stage", ""),
            failure_type=data.get("failure_type", ""),
            final_error=data.get("final_error", ""),
            retry_attempts=data.get("retry_attempts", []),
            final_failure_at=datetime.fromisoformat(data["final_failure_at"]) if data.get("final_failure_at") else datetime.now(),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolution_status=ResolutionStatus(data.get("resolution_status", "pending_review")),
            resolution_notes=data.get("resolution_notes")
        )


# In-memory storage
_dead_letters: Dict[str, DeadLetterEntry] = {}


class DeadLetterService:
    """Service for managing dead letter queue"""
    
    def __init__(self):
        self.storage_path = ".story_assets/dead_letters"
        os.makedirs(self.storage_path, exist_ok=True)
        self.checkpoint_service = CheckpointService()
    
    def add_to_dead_letter(
        self,
        job_id: str,
        failure_stage: str,
        failure_type: FailureType,
        final_error: str,
        retry_attempts: List[RetryAttempt] = None,
        checkpoint: JobCheckpoint = None
    ) -> DeadLetterEntry:
        """Add a failed job to the dead letter queue"""
        entry = DeadLetterEntry(
            job_id=job_id,
            failure_stage=failure_stage,
            failure_type=failure_type.value,
            final_error=final_error,
            retry_attempts=[a.to_dict() for a in (retry_attempts or [])],
            checkpoint=checkpoint.to_dict() if checkpoint else None,
            config_snapshot=checkpoint.config_snapshot if checkpoint else {}
        )
        
        _dead_letters[entry.id] = entry
        self._save_entry(entry)
        
        logger.warning(f"Job {job_id} moved to dead letter queue: {final_error}")
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """Get a dead letter entry by ID"""
        if entry_id in _dead_letters:
            return _dead_letters[entry_id]
        return self._load_entry(entry_id)
    
    def get_by_job_id(self, job_id: str) -> Optional[DeadLetterEntry]:
        """Get dead letter entry by original job ID"""
        for entry in _dead_letters.values():
            if entry.job_id == job_id:
                return entry
        return None
    
    def list_entries(
        self,
        status: Optional[ResolutionStatus] = None,
        limit: int = 50
    ) -> List[DeadLetterEntry]:
        """List dead letter entries"""
        entries = list(_dead_letters.values())
        
        if status:
            entries = [e for e in entries if e.resolution_status == status]
        
        # Sort by failure time, newest first
        entries.sort(key=lambda e: e.final_failure_at, reverse=True)
        
        return entries[:limit]
    
    def get_pending_count(self) -> int:
        """Get count of pending review entries"""
        return len([
            e for e in _dead_letters.values()
            if e.resolution_status == ResolutionStatus.PENDING_REVIEW
        ])
    
    def retry_entry(self, entry_id: str) -> Dict:
        """Mark entry for retry and return job info"""
        entry = self.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Dead letter entry {entry_id} not found")
        
        if entry.resolution_status != ResolutionStatus.PENDING_REVIEW:
            raise ValueError(f"Entry already resolved: {entry.resolution_status.value}")
        
        entry.resolution_status = ResolutionStatus.RETRIED
        entry.resolved_at = datetime.now()
        entry.resolution_notes = "Retried via admin action"
        self._save_entry(entry)
        
        logger.info(f"Dead letter entry {entry_id} marked for retry")
        
        return {
            "job_id": entry.job_id,
            "checkpoint": entry.checkpoint,
            "config": entry.config_snapshot
        }
    
    def dismiss_entry(self, entry_id: str, notes: str = None) -> bool:
        """Dismiss entry permanently"""
        entry = self.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Dead letter entry {entry_id} not found")
        
        entry.resolution_status = ResolutionStatus.DISMISSED
        entry.resolved_at = datetime.now()
        entry.resolution_notes = notes or "Dismissed via admin action"
        self._save_entry(entry)
        
        logger.info(f"Dead letter entry {entry_id} dismissed")
        return True
    
    def get_statistics(self) -> Dict:
        """Get dead letter queue statistics"""
        entries = list(_dead_letters.values())
        
        by_status = {}
        for status in ResolutionStatus:
            by_status[status.value] = len([e for e in entries if e.resolution_status == status])
        
        by_failure_type = {}
        for entry in entries:
            ft = entry.failure_type
            by_failure_type[ft] = by_failure_type.get(ft, 0) + 1
        
        return {
            "total_entries": len(entries),
            "by_status": by_status,
            "by_failure_type": by_failure_type,
            "pending_review": by_status.get("pending_review", 0)
        }
    
    def _save_entry(self, entry: DeadLetterEntry):
        """Save entry to disk"""
        path = os.path.join(self.storage_path, f"{entry.id}.json")
        with open(path, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
    
    def _load_entry(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """Load entry from disk"""
        path = os.path.join(self.storage_path, f"{entry_id}.json")
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            entry = DeadLetterEntry.from_dict(data)
            _dead_letters[entry.id] = entry
            return entry
        except Exception as e:
            logger.error(f"Error loading dead letter {entry_id}: {e}")
            return None

"""
Job Checkpointing System
Saves job state at stage boundaries for recovery after failures.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
import os

from app.core.logging import get_logger

logger = get_logger(__name__)


class StageStatus(str, Enum):
    """Status of a stage in the pipeline"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageCheckpoint:
    """Checkpoint for a single stage"""
    stage_id: str
    stage_name: str
    status: StageStatus
    input_ref: Optional[str] = None  # Reference to input artifact
    output_ref: Optional[str] = None  # Reference to output artifact
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "status": self.status.value,
            "input_ref": self.input_ref,
            "output_ref": self.output_ref,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StageCheckpoint":
        return cls(
            stage_id=data["stage_id"],
            stage_name=data["stage_name"],
            status=StageStatus(data["status"]),
            input_ref=data.get("input_ref"),
            output_ref=data.get("output_ref"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0)
        )


@dataclass
class JobCheckpoint:
    """Full checkpoint for a job"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    job_type: str = ""  # "single", "batch_item", etc.
    
    # Stage tracking
    current_stage: str = ""
    stages: List[StageCheckpoint] = field(default_factory=list)
    
    # State
    total_retries: int = 0
    is_recoverable: bool = True
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Context
    config_snapshot: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def get_stage(self, stage_name: str) -> Optional[StageCheckpoint]:
        """Get checkpoint for a specific stage"""
        for stage in self.stages:
            if stage.stage_name == stage_name:
                return stage
        return None
    
    def get_last_completed_stage(self) -> Optional[StageCheckpoint]:
        """Get the last successfully completed stage"""
        completed = [s for s in self.stages if s.status == StageStatus.COMPLETED]
        if completed:
            return completed[-1]
        return None
    
    def get_failed_stages(self) -> List[StageCheckpoint]:
        """Get all failed stages"""
        return [s for s in self.stages if s.status == StageStatus.FAILED]
    
    def add_stage(self, stage_name: str, input_ref: str = None) -> StageCheckpoint:
        """Add a new stage checkpoint"""
        stage = StageCheckpoint(
            stage_id=str(uuid.uuid4()),
            stage_name=stage_name,
            status=StageStatus.PENDING,
            input_ref=input_ref
        )
        self.stages.append(stage)
        self.current_stage = stage_name
        self.updated_at = datetime.now()
        return stage
    
    def start_stage(self, stage_name: str):
        """Mark a stage as started"""
        stage = self.get_stage(stage_name)
        if stage:
            stage.status = StageStatus.IN_PROGRESS
            stage.started_at = datetime.now()
            self.current_stage = stage_name
            self.updated_at = datetime.now()
    
    def complete_stage(self, stage_name: str, output_ref: str = None):
        """Mark a stage as completed"""
        stage = self.get_stage(stage_name)
        if stage:
            stage.status = StageStatus.COMPLETED
            stage.output_ref = output_ref
            stage.completed_at = datetime.now()
            self.updated_at = datetime.now()
    
    def fail_stage(self, stage_name: str, error_message: str):
        """Mark a stage as failed"""
        stage = self.get_stage(stage_name)
        if stage:
            stage.status = StageStatus.FAILED
            stage.error_message = error_message
            stage.retry_count += 1
            self.total_retries += 1
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_type": self.job_type,
            "current_stage": self.current_stage,
            "stages": [s.to_dict() for s in self.stages],
            "total_retries": self.total_retries,
            "is_recoverable": self.is_recoverable,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "config_snapshot": self.config_snapshot,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "JobCheckpoint":
        checkpoint = cls(
            id=data.get("id", str(uuid.uuid4())),
            job_id=data.get("job_id", ""),
            job_type=data.get("job_type", ""),
            current_stage=data.get("current_stage", ""),
            total_retries=data.get("total_retries", 0),
            is_recoverable=data.get("is_recoverable", True),
            config_snapshot=data.get("config_snapshot", {}),
            metadata=data.get("metadata", {})
        )
        
        checkpoint.stages = [
            StageCheckpoint.from_dict(s) for s in data.get("stages", [])
        ]
        
        return checkpoint


# In-memory storage (replace with database in production)
_checkpoints: Dict[str, JobCheckpoint] = {}


class CheckpointService:
    """Service for managing job checkpoints"""
    
    def __init__(self):
        self.storage_path = ".story_assets/checkpoints"
        os.makedirs(self.storage_path, exist_ok=True)
    
    def create_checkpoint(
        self,
        job_id: str,
        job_type: str = "single",
        config: Dict = None
    ) -> JobCheckpoint:
        """Create a new checkpoint for a job"""
        checkpoint = JobCheckpoint(
            job_id=job_id,
            job_type=job_type,
            config_snapshot=config or {}
        )
        
        _checkpoints[job_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Created checkpoint for job {job_id}")
        return checkpoint
    
    def get_checkpoint(self, job_id: str) -> Optional[JobCheckpoint]:
        """Get checkpoint for a job"""
        if job_id in _checkpoints:
            return _checkpoints[job_id]
        return self._load_checkpoint(job_id)
    
    def save_checkpoint(self, checkpoint: JobCheckpoint):
        """Save checkpoint to storage"""
        checkpoint.updated_at = datetime.now()
        _checkpoints[checkpoint.job_id] = checkpoint
        self._save_checkpoint(checkpoint)
        logger.debug(f"Saved checkpoint for job {checkpoint.job_id}")
    
    def delete_checkpoint(self, job_id: str) -> bool:
        """Delete checkpoint for completed job"""
        if job_id in _checkpoints:
            del _checkpoints[job_id]
        
        path = os.path.join(self.storage_path, f"{job_id}.json")
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted checkpoint for job {job_id}")
            return True
        return False
    
    def list_checkpoints(self, recoverable_only: bool = False) -> List[JobCheckpoint]:
        """List all checkpoints"""
        checkpoints = list(_checkpoints.values())
        
        if recoverable_only:
            checkpoints = [c for c in checkpoints if c.is_recoverable]
        
        return checkpoints
    
    def get_interrupted_jobs(self) -> List[JobCheckpoint]:
        """Get jobs that were interrupted (in_progress stages)"""
        interrupted = []
        for checkpoint in _checkpoints.values():
            for stage in checkpoint.stages:
                if stage.status == StageStatus.IN_PROGRESS:
                    interrupted.append(checkpoint)
                    break
        return interrupted
    
    def validate_checkpoint(self, checkpoint: JobCheckpoint) -> Dict:
        """Validate checkpoint integrity"""
        errors = []
        warnings = []
        
        if not checkpoint.job_id:
            errors.append("Missing job_id")
        
        if not checkpoint.stages:
            warnings.append("No stages recorded")
        
        # Check for logical stage order
        has_completed = False
        for stage in checkpoint.stages:
            if stage.status == StageStatus.COMPLETED:
                has_completed = True
            elif stage.status == StageStatus.IN_PROGRESS and not has_completed:
                # First stage can be in progress without prior completions
                pass
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _save_checkpoint(self, checkpoint: JobCheckpoint):
        """Save to disk"""
        path = os.path.join(self.storage_path, f"{checkpoint.job_id}.json")
        with open(path, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
    
    def _load_checkpoint(self, job_id: str) -> Optional[JobCheckpoint]:
        """Load from disk"""
        path = os.path.join(self.storage_path, f"{job_id}.json")
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            checkpoint = JobCheckpoint.from_dict(data)
            _checkpoints[job_id] = checkpoint
            return checkpoint
        except Exception as e:
            logger.error(f"Error loading checkpoint {job_id}: {e}")
            return None

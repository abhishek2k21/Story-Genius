"""
State Recovery After Restart
Scans for interrupted jobs and resumes from checkpoints.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.reliability.checkpointing import (
    CheckpointService, JobCheckpoint, StageStatus
)
from app.reliability.dead_letter import DeadLetterService
from app.reliability.retry import FailureType
from app.core.logging import get_logger

logger = get_logger(__name__)


class RecoveryAction(str, Enum):
    """Actions taken during recovery"""
    RESUMED = "resumed"
    RESTARTED = "restarted"
    DEAD_LETTERED = "dead_lettered"
    SKIPPED = "skipped"
    COMPLETED = "completed"


@dataclass
class RecoveryResult:
    """Result of recovering a single job"""
    job_id: str
    action: RecoveryAction
    from_stage: Optional[str] = None
    message: str = ""
    
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "action": self.action.value,
            "from_stage": self.from_stage,
            "message": self.message
        }


class RecoveryService:
    """Handles recovery of interrupted jobs on startup"""
    
    def __init__(self):
        self.checkpoint_service = CheckpointService()
        self.dead_letter_service = DeadLetterService()
        self._recovery_run = False
    
    def run_recovery_scan(self) -> Dict:
        """
        Scan for and recover interrupted jobs.
        Should be called on application startup.
        """
        logger.info("Starting recovery scan...")
        
        results: List[RecoveryResult] = []
        
        # Get all checkpoints
        checkpoints = self.checkpoint_service.list_checkpoints()
        
        for checkpoint in checkpoints:
            result = self._recover_job(checkpoint)
            results.append(result)
        
        self._recovery_run = True
        
        summary = self._summarize_results(results)
        logger.info(f"Recovery scan complete: {summary}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "jobs_scanned": len(checkpoints),
            "results": [r.to_dict() for r in results],
            "summary": summary
        }
    
    def _recover_job(self, checkpoint: JobCheckpoint) -> RecoveryResult:
        """Attempt to recover a single job"""
        job_id = checkpoint.job_id
        
        # Validate checkpoint
        validation = self.checkpoint_service.validate_checkpoint(checkpoint)
        if not validation["valid"]:
            # Corrupted checkpoint - move to dead letter
            self.dead_letter_service.add_to_dead_letter(
                job_id=job_id,
                failure_stage=checkpoint.current_stage,
                failure_type=FailureType.UNKNOWN_ERROR,
                final_error=f"Corrupted checkpoint: {validation['errors']}",
                checkpoint=checkpoint
            )
            return RecoveryResult(
                job_id=job_id,
                action=RecoveryAction.DEAD_LETTERED,
                message="Corrupted checkpoint"
            )
        
        # Check if job is recoverable
        if not checkpoint.is_recoverable:
            self.dead_letter_service.add_to_dead_letter(
                job_id=job_id,
                failure_stage=checkpoint.current_stage,
                failure_type=FailureType.UNKNOWN_ERROR,
                final_error="Marked as non-recoverable",
                checkpoint=checkpoint
            )
            return RecoveryResult(
                job_id=job_id,
                action=RecoveryAction.DEAD_LETTERED,
                message="Non-recoverable"
            )
        
        # Find last completed stage
        last_completed = checkpoint.get_last_completed_stage()
        
        # Check for in-progress stages
        in_progress_stages = [
            s for s in checkpoint.stages 
            if s.status == StageStatus.IN_PROGRESS
        ]
        
        if not last_completed and not in_progress_stages:
            # Job just started, no progress - restart from beginning
            return RecoveryResult(
                job_id=job_id,
                action=RecoveryAction.RESTARTED,
                from_stage=None,
                message="Restarting from beginning"
            )
        
        if in_progress_stages:
            # Resume from the in-progress stage
            resume_stage = in_progress_stages[0]
            return RecoveryResult(
                job_id=job_id,
                action=RecoveryAction.RESUMED,
                from_stage=resume_stage.stage_name,
                message=f"Resuming from {resume_stage.stage_name}"
            )
        
        # Resume from after last completed stage
        return RecoveryResult(
            job_id=job_id,
            action=RecoveryAction.RESUMED,
            from_stage=last_completed.stage_name,
            message=f"Resuming after {last_completed.stage_name}"
        )
    
    def _summarize_results(self, results: List[RecoveryResult]) -> Dict:
        """Summarize recovery results"""
        summary = {
            "total": len(results),
            "resumed": 0,
            "restarted": 0,
            "dead_lettered": 0,
            "skipped": 0,
            "completed": 0
        }
        
        for result in results:
            key = result.action.value
            if key in summary:
                summary[key] += 1
        
        return summary
    
    def get_recoverable_jobs(self) -> List[Dict]:
        """Get list of jobs that can be recovered"""
        checkpoints = self.checkpoint_service.list_checkpoints(recoverable_only=True)
        
        jobs = []
        for checkpoint in checkpoints:
            last_completed = checkpoint.get_last_completed_stage()
            jobs.append({
                "job_id": checkpoint.job_id,
                "job_type": checkpoint.job_type,
                "current_stage": checkpoint.current_stage,
                "last_completed": last_completed.stage_name if last_completed else None,
                "total_retries": checkpoint.total_retries,
                "updated_at": checkpoint.updated_at.isoformat()
            })
        
        return jobs
    
    def force_dead_letter(self, job_id: str, reason: str) -> bool:
        """Force a job to dead letter queue"""
        checkpoint = self.checkpoint_service.get_checkpoint(job_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint found for job {job_id}")
        
        self.dead_letter_service.add_to_dead_letter(
            job_id=job_id,
            failure_stage=checkpoint.current_stage,
            failure_type=FailureType.UNKNOWN_ERROR,
            final_error=reason,
            checkpoint=checkpoint
        )
        
        # Mark checkpoint as non-recoverable
        checkpoint.is_recoverable = False
        self.checkpoint_service.save_checkpoint(checkpoint)
        
        logger.info(f"Force dead-lettered job {job_id}: {reason}")
        return True
    
    @property
    def has_run(self) -> bool:
        """Check if recovery has been run"""
        return self._recovery_run

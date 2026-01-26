"""
Admin API Routes
Health checks, dead letter management, recovery, and cleanup endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.reliability.health import HealthCheckService
from app.reliability.dead_letter import DeadLetterService, ResolutionStatus
from app.reliability.recovery import RecoveryService
from app.reliability.cleanup import CleanupService, ArtifactType
from app.reliability.checkpointing import CheckpointService

router = APIRouter(prefix="/v1/admin", tags=["admin"])

# Initialize services
health_service = HealthCheckService()
dead_letter_service = DeadLetterService()
recovery_service = RecoveryService()
cleanup_service = CleanupService()
checkpoint_service = CheckpointService()


# ==================== Health Endpoints ====================

@router.get("/health")
async def full_health_check():
    """Complete health check with all components"""
    return health_service.check_all()


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return health_service.check_liveness()


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    return health_service.check_readiness()


# ==================== Dead Letter Endpoints ====================

@router.get("/dead-letter")
async def list_dead_letters(status: Optional[str] = None, limit: int = 50):
    """List dead letter entries"""
    status_filter = ResolutionStatus(status) if status else None
    entries = dead_letter_service.list_entries(status=status_filter, limit=limit)
    
    return {
        "count": len(entries),
        "entries": [e.to_dict() for e in entries]
    }


@router.get("/dead-letter/stats")
async def dead_letter_stats():
    """Get dead letter queue statistics"""
    return dead_letter_service.get_statistics()


@router.get("/dead-letter/{entry_id}")
async def get_dead_letter(entry_id: str):
    """Get dead letter entry details"""
    entry = dead_letter_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry.to_dict()


@router.post("/dead-letter/{entry_id}/retry")
async def retry_dead_letter(entry_id: str):
    """Retry a dead letter job"""
    try:
        result = dead_letter_service.retry_entry(entry_id)
        return {
            "message": "Entry marked for retry",
            "job_info": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class DismissRequest(BaseModel):
    notes: Optional[str] = None


@router.post("/dead-letter/{entry_id}/dismiss")
async def dismiss_dead_letter(entry_id: str, request: DismissRequest = None):
    """Dismiss a dead letter entry permanently"""
    try:
        notes = request.notes if request else None
        dead_letter_service.dismiss_entry(entry_id, notes)
        return {"message": "Entry dismissed", "entry_id": entry_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Recovery Endpoints ====================

@router.post("/recovery/scan")
async def trigger_recovery_scan():
    """Trigger a recovery scan for interrupted jobs"""
    result = recovery_service.run_recovery_scan()
    return result


@router.get("/recovery/jobs")
async def list_recoverable_jobs():
    """List jobs that can be recovered"""
    jobs = recovery_service.get_recoverable_jobs()
    return {"count": len(jobs), "jobs": jobs}


class ForceDeadLetterRequest(BaseModel):
    reason: str


@router.post("/recovery/jobs/{job_id}/dead-letter")
async def force_dead_letter(job_id: str, request: ForceDeadLetterRequest):
    """Force a job to dead letter queue"""
    try:
        recovery_service.force_dead_letter(job_id, request.reason)
        return {"message": "Job moved to dead letter", "job_id": job_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Cleanup Endpoints ====================

@router.get("/cleanup/preview")
async def preview_cleanup(artifact_type: Optional[str] = None):
    """Preview what cleanup would delete"""
    atype = ArtifactType(artifact_type) if artifact_type else None
    return cleanup_service.preview_cleanup(atype)


@router.post("/cleanup/run")
async def run_cleanup(artifact_type: Optional[str] = None, dry_run: bool = False):
    """Run cleanup operation"""
    atype = ArtifactType(artifact_type) if artifact_type else None
    results = cleanup_service.run_cleanup(atype, dry_run)
    
    return {
        "dry_run": dry_run,
        "results": [r.to_dict() for r in results],
        "total_deleted": sum(r.items_deleted for r in results),
        "total_mb_reclaimed": round(sum(r.bytes_reclaimed for r in results) / (1024*1024), 2)
    }


@router.get("/cleanup/stats")
async def storage_stats():
    """Get storage usage statistics"""
    return cleanup_service.get_storage_stats()


# ==================== Checkpoint Endpoints ====================

@router.get("/jobs/{job_id}/checkpoints")
async def get_job_checkpoints(job_id: str):
    """Get checkpoint for a job"""
    checkpoint = checkpoint_service.get_checkpoint(job_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="No checkpoint found")
    return checkpoint.to_dict()


@router.get("/checkpoints")
async def list_checkpoints():
    """List all active checkpoints"""
    checkpoints = checkpoint_service.list_checkpoints()
    return {
        "count": len(checkpoints),
        "checkpoints": [
            {
                "job_id": c.job_id,
                "current_stage": c.current_stage,
                "total_retries": c.total_retries,
                "is_recoverable": c.is_recoverable,
                "updated_at": c.updated_at.isoformat()
            }
            for c in checkpoints
        ]
    }


@router.delete("/jobs/{job_id}/checkpoints")
async def delete_job_checkpoint(job_id: str):
    """Delete checkpoint for a completed job"""
    result = checkpoint_service.delete_checkpoint(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"message": "Checkpoint deleted", "job_id": job_id}

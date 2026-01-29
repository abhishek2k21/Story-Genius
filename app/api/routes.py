"""
API Routes for the Creative AI Shorts Platform.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.models import (
    ShortsGenerateRequest,
    ShortsGenerateResponse,
    JobStatusResponse,
    JobStatus
)
from app.core.database import get_db
from app.orchestrator.service import OrchestratorService

router = APIRouter(prefix="/v1", tags=["shorts"])


@router.post("/shorts/generate", response_model=ShortsGenerateResponse)
async def generate_shorts(
    request: ShortsGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a new short-form video.
    
    Creates a job and starts processing in the background.
    Returns immediately with job_id for status tracking.
    """
    orchestrator = OrchestratorService()
    
    try:
        # Create job
        job = orchestrator.create_job({
            "platform": request.platform.value if hasattr(request.platform, 'value') else request.platform,
            "audience": request.audience,
            "duration": request.duration,
            "genre": request.genre,
            "language": request.language
        })
        
        # Start job in background
        background_tasks.add_task(run_job_background, job.id)
        
        return ShortsGenerateResponse(
            job_id=job.id,
            status=job.status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        orchestrator.close()


def run_job_background(job_id: str):
    """Background task to run job processing."""
    import logging
    logger = logging.getLogger(__name__)
    orchestrator = OrchestratorService()
    try:
        logger.info(f"🔵 [BACKGROUND] Starting job {job_id}")
        result = orchestrator.start_job(job_id)
        logger.info(f"🟢 [BACKGROUND] Job {job_id} completed with result: {result}")
    except Exception as e:
        logger.error(f"🔴 [BACKGROUND] Job {job_id} failed with exception!")
        logger.error(f"🔴 [BACKGROUND] Exception type: {type(e).__name__}")
        logger.error(f"🔴 [BACKGROUND] Exception message: {str(e)}")
        import traceback
        logger.error(f"🔴 [BACKGROUND] Traceback:\n{traceback.format_exc()}")
    finally:
        orchestrator.close()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a job by ID.
    """
    orchestrator = OrchestratorService()
    
    try:
        job = orchestrator.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            platform=job.platform if isinstance(job.platform, str) else job.platform.value,
            audience=job.audience,
            duration=job.duration,
            created_at=job.created_at,
            updated_at=job.updated_at,
            video_url=job.video_url,
            error_message=job.error_message
        )
        
    finally:
        orchestrator.close()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Creative AI Shorts Platform"}

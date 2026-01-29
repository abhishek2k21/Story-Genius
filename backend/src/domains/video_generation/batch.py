"""
Batch Video Generation
Generate multiple videos from one project.
"""
import asyncio
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.domains.video_generation.styles import apply_style_to_prompt, get_style

logger = get_logger(__name__)


class BatchJobConfig(BaseModel):
    """Configuration for a single job in a batch."""
    prompt: str
    style_id: Optional[str] = None
    target_duration: int = 60
    voice_id: Optional[str] = None


class BatchRequest(BaseModel):
    """Batch video generation request."""
    project_id: uuid.UUID
    jobs: list[BatchJobConfig] = Field(..., min_length=1, max_length=10)
    parallel_limit: int = Field(2, ge=1, le=5)


class BatchJobStatus(BaseModel):
    """Status of a single batch job."""
    index: int
    prompt: str
    status: str  # pending, running, completed, failed
    job_id: Optional[str] = None
    video_path: Optional[str] = None
    error: Optional[str] = None


class BatchResult(BaseModel):
    """Result of batch generation."""
    batch_id: str
    project_id: uuid.UUID
    total_jobs: int
    completed: int
    failed: int
    jobs: list[BatchJobStatus]


async def generate_batch(
    request: BatchRequest,
    task_fn,
) -> BatchResult:
    """
    Generate multiple videos in batch.

    Args:
        request: Batch generation request
        task_fn: Celery task function to call for each job

    Returns:
        BatchResult with status of all jobs
    """
    batch_id = str(uuid.uuid4())
    results: list[BatchJobStatus] = []

    # Initialize all jobs as pending
    for i, config in enumerate(request.jobs):
        results.append(BatchJobStatus(
            index=i,
            prompt=config.prompt,
            status="pending",
        ))

    # Semaphore for parallel limit
    semaphore = asyncio.Semaphore(request.parallel_limit)

    async def process_job(index: int, config: BatchJobConfig):
        async with semaphore:
            results[index].status = "running"
            try:
                # Apply style if specified
                prompt = config.prompt
                if config.style_id:
                    prompt = apply_style_to_prompt(prompt, config.style_id)

                # Queue the Celery task
                task = task_fn.delay(
                    project_id=str(request.project_id),
                    prompt=prompt,
                    style_prefix=get_style(config.style_id).prompt_prefix if config.style_id else "",
                    voice_id=config.voice_id or "",
                    target_duration=config.target_duration,
                )

                results[index].job_id = task.id
                results[index].status = "queued"

            except Exception as e:
                logger.error(f"Batch job {index} failed: {e}")
                results[index].status = "failed"
                results[index].error = str(e)

    # Process all jobs
    await asyncio.gather(*[
        process_job(i, config)
        for i, config in enumerate(request.jobs)
    ])

    # Calculate summary
    completed = sum(1 for r in results if r.status == "queued")
    failed = sum(1 for r in results if r.status == "failed")

    return BatchResult(
        batch_id=batch_id,
        project_id=request.project_id,
        total_jobs=len(request.jobs),
        completed=completed,
        failed=failed,
        jobs=results,
    )

"""
Video Generation API Endpoints
"""
import uuid
from typing import Optional

from fastapi import APIRouter

from src.core.dependencies import DbSession, OptionalApiKey
from src.domains.video_generation.entities import (
    ClipResponse,
    SceneAssetRequest,
    SceneAssetResponse,
    StitchRequest,
    StitchResponse,
    VideoJobCreate,
    VideoJobResponse,
    VideoJobStatus,
)
from src.domains.video_generation.services import VideoGenerationService

router = APIRouter()


def get_user_id(api_key: Optional[str]) -> str:
    """Get user ID from API key (temp implementation)."""
    return api_key or "default_user"


@router.post("/jobs", response_model=dict, status_code=202)
async def start_video_generation(
    data: VideoJobCreate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> dict:
    """
    Start a video generation job.

    This triggers a Celery task to generate all assets and stitch the final video.
    """
    from src.domains.video_generation.tasks import generate_story_video

    # Queue the job
    task = generate_story_video.delay(
        story_id=str(data.story_id),
        generate_audio=data.generate_audio,
        generate_video=data.generate_video,
        stitch_final=data.stitch_final,
    )

    return {
        "job_id": task.id,
        "story_id": str(data.story_id),
        "status": "queued",
        "message": "Video generation job queued",
    }


@router.get("/jobs/{job_id}", response_model=dict)
async def get_job_status(
    job_id: str,
    api_key: OptionalApiKey,
) -> dict:
    """Get status of a video generation job."""
    from celery.result import AsyncResult

    from src.tasks.celery_app import celery_app

    result = AsyncResult(job_id, app=celery_app)

    response = {
        "job_id": job_id,
        "status": result.status,
        "ready": result.ready(),
    }

    if result.status == "PROGRESS":
        response["progress"] = result.info
    elif result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)

    return response


@router.post("/scenes/{scene_id}/generate", response_model=dict, status_code=202)
async def generate_scene(
    scene_id: uuid.UUID,
    data: SceneAssetRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> dict:
    """Generate assets for a single scene."""
    from src.domains.video_generation.tasks import generate_scene_assets

    task = generate_scene_assets.delay(
        scene_id=str(scene_id),
        generate_audio=data.generate_audio,
        generate_video=data.generate_video,
    )

    return {
        "task_id": task.id,
        "scene_id": str(scene_id),
        "status": "queued",
    }


@router.get("/stories/{story_id}/clips", response_model=list[ClipResponse])
async def get_clips(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> list[ClipResponse]:
    """Get status of all clips for a story."""
    service = VideoGenerationService(db)
    return await service.get_clip_status(story_id)


@router.post("/stories/{story_id}/stitch", response_model=dict, status_code=202)
async def stitch_video(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
    output_filename: Optional[str] = None,
) -> dict:
    """Stitch all clips for a story into final video."""
    from src.domains.video_generation.tasks import stitch_story_video

    task = stitch_story_video.delay(
        story_id=str(story_id),
        output_filename=output_filename,
    )

    return {
        "task_id": task.id,
        "story_id": str(story_id),
        "status": "queued",
    }


@router.post("/stitch", response_model=StitchResponse)
async def stitch_manual(
    data: StitchRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> StitchResponse:
    """Manually stitch specific clips into a video (synchronous)."""
    service = VideoGenerationService(db)
    return await service.stitch_video(data.story_id, data.output_filename)

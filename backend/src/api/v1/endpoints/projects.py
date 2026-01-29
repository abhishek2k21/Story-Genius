"""
Projects API Endpoints
Enhanced with video generation trigger.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from src.core.dependencies import DbSession, OptionalApiKey
from src.domains.projects.entities import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStories,
)
from src.domains.projects.services import ProjectService

router = APIRouter()


def get_user_id(api_key: Optional[str]) -> str:
    """Get user ID from API key (temp implementation)."""
    return api_key or "default_user"


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> ProjectResponse:
    """Create a new project."""
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    return await service.create_project(data, user_id)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: DbSession,
    api_key: OptionalApiKey,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> ProjectListResponse:
    """List all projects for the current user."""
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    return await service.list_projects(user_id, page, size, status)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
    include_stories: bool = Query(False),
) -> ProjectResponse | ProjectWithStories:
    """Get a project by ID."""
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    return await service.get_project(project_id, user_id, include_stories)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> ProjectResponse:
    """Update a project."""
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    return await service.update_project(project_id, user_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> None:
    """Delete a project."""
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    await service.delete_project(project_id, user_id)


# ========================
# Video Generation
# ========================

from pydantic import BaseModel, Field


class GenerateVideoRequest(BaseModel):
    """Request to generate video from prompt."""
    prompt: str = Field(..., min_length=10, max_length=2000)
    style_prefix: Optional[str] = None
    voice_id: Optional[str] = None
    target_duration: int = Field(60, ge=15, le=180)


@router.post("/{project_id}/generate-video", response_model=dict, status_code=202)
async def generate_video(
    project_id: uuid.UUID,
    data: GenerateVideoRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> dict:
    """
    Generate a complete video from prompt.

    Full pipeline:
    1. Generate story script with Gemini
    2. Generate scenes with Veo (with fallbacks)
    3. Generate audio with ElevenLabs
    4. Stitch final video with MoviePy

    Returns job_id for status polling.
    """
    from src.domains.video_generation.enhanced_tasks import generate_project_video

    # Queue the full pipeline
    task = generate_project_video.delay(
        project_id=str(project_id),
        prompt=data.prompt,
        style_prefix=data.style_prefix or "",
        voice_id=data.voice_id or "",
        target_duration=data.target_duration,
    )

    return {
        "job_id": task.id,
        "project_id": str(project_id),
        "status": "queued",
        "message": "Video generation started",
    }

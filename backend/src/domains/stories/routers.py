"""
Stories API Endpoints
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from src.core.dependencies import DbSession, OptionalApiKey
from src.domains.stories.entities import (
    SceneResponse,
    StoryCreate,
    StoryGenerateRequest,
    StoryListResponse,
    StoryResponse,
    StoryUpdate,
    StoryWithScenes,
)
from src.domains.stories.services import StoryService

router = APIRouter()


def get_user_id(api_key: Optional[str]) -> str:
    """Get user ID from API key (temp implementation)."""
    return api_key or "default_user"


@router.post("", response_model=StoryResponse, status_code=201)
async def create_story(
    data: StoryCreate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> StoryResponse:
    """Create a story manually without AI generation."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.create_story(data, user_id)


@router.post("/generate", response_model=StoryWithScenes, status_code=201)
async def generate_story(
    data: StoryGenerateRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> StoryWithScenes:
    """
    Generate a story with AI.

    Uses Gemini to generate a script with scenes based on the prompt.
    """
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.generate_story(data, user_id)


@router.get("", response_model=StoryListResponse)
async def list_stories(
    project_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> StoryListResponse:
    """List stories for a project."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.list_stories(project_id, user_id, page, size, status)


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
    include_scenes: bool = Query(False),
) -> StoryResponse | StoryWithScenes:
    """Get a story by ID."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.get_story(story_id, user_id, include_scenes)


@router.patch("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: uuid.UUID,
    data: StoryUpdate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> StoryResponse:
    """Update a story."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.update_story(story_id, user_id, data)


@router.delete("/{story_id}", status_code=204)
async def delete_story(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> None:
    """Delete a story and its scenes."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    await service.delete_story(story_id, user_id)


@router.get("/{story_id}/scenes", response_model=list[SceneResponse])
async def get_scenes(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> list[SceneResponse]:
    """Get all scenes for a story."""
    service = StoryService(db)
    user_id = get_user_id(api_key)
    return await service.get_scenes(story_id, user_id)

"""
Projects API Endpoints
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


# Temporary: Use API key as user_id until auth is migrated
def get_user_id(api_key: Optional[str]) -> str:
    """Get user ID from API key (temp implementation)."""
    return api_key or "default_user"


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: DbSession,
    api_key: OptionalApiKey,
) -> ProjectResponse:
    """
    Create a new project.

    - **name**: Project name (required)
    - **description**: Optional description
    - **default_voice**: Default TTS voice
    - **default_style**: Default visual style for videos
    """
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
    """
    List all projects for the current user.

    Supports pagination and optional status filter.
    """
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
    """
    Get a project by ID.

    Optionally include stories.
    """
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
    """
    Update a project.

    Only provided fields will be updated.
    """
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    return await service.update_project(project_id, user_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> None:
    """
    Delete a project.

    This will also delete all associated stories and scenes.
    """
    service = ProjectService(db)
    user_id = get_user_id(api_key)
    await service.delete_project(project_id, user_id)

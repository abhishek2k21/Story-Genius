"""
Project Entities (Pydantic Schemas)
Request/Response models for the projects domain.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    """Project status values."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


# ========================
# Request Schemas
# ========================

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    default_voice: Optional[str] = Field(None, max_length=100)
    default_style: Optional[str] = Field(None, max_length=100)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatus] = None
    default_voice: Optional[str] = Field(None, max_length=100)
    default_style: Optional[str] = Field(None, max_length=100)


# ========================
# Response Schemas
# ========================

class ProjectResponse(BaseModel):
    """Schema for project response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    user_id: str
    default_voice: Optional[str] = None
    default_style: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    story_count: int = 0


class ProjectListResponse(BaseModel):
    """Schema for paginated project list."""
    items: list[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int


class ProjectWithStories(ProjectResponse):
    """Project with its stories included."""
    stories: list["StoryBrief"] = []


class StoryBrief(BaseModel):
    """Brief story info for inclusion in project."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str
    created_at: datetime

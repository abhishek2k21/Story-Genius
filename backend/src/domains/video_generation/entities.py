"""
Video Generation Entities (Pydantic Schemas)
Request/Response models for video generation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VideoJobStatus(str, Enum):
    """Video job status values."""
    PENDING = "pending"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    STITCHING = "stitching"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipStatus(str, Enum):
    """Individual clip status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ========================
# Job Schemas
# ========================

class VideoJobCreate(BaseModel):
    """Schema for creating a video generation job."""
    story_id: uuid.UUID
    generate_audio: bool = Field(True, description="Generate audio for scenes")
    generate_video: bool = Field(True, description="Generate video clips")
    stitch_final: bool = Field(True, description="Stitch clips into final video")


class VideoJobResponse(BaseModel):
    """Schema for video job response."""
    id: str
    story_id: uuid.UUID
    status: VideoJobStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    video_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VideoJobProgress(BaseModel):
    """Detailed job progress."""
    job_id: str
    status: VideoJobStatus
    progress: float
    current_step: str
    clips_completed: int
    clips_total: int
    audio_completed: int
    audio_total: int


# ========================
# Clip Schemas
# ========================

class ClipResponse(BaseModel):
    """Schema for video clip response."""
    scene_id: uuid.UUID
    scene_order: int
    status: ClipStatus
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class StitchRequest(BaseModel):
    """Request to stitch clips manually."""
    story_id: uuid.UUID
    clip_paths: list[str]
    output_filename: Optional[str] = None


class StitchResponse(BaseModel):
    """Response from stitching operation."""
    video_path: str
    duration_seconds: float
    file_size_mb: float


# ========================
# Scene Generation
# ========================

class SceneAssetRequest(BaseModel):
    """Request to generate assets for a single scene."""
    scene_id: uuid.UUID
    generate_audio: bool = True
    generate_video: bool = True


class SceneAssetResponse(BaseModel):
    """Response for scene asset generation."""
    scene_id: uuid.UUID
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    image_path: Optional[str] = None
    status: ClipStatus

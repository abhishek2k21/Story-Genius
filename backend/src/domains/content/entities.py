"""
Content Entities (Pydantic Schemas)
Models for captions, exports, and preview.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CaptionStyle(str, Enum):
    """Caption styling options."""
    STANDARD = "standard"
    BOLD = "bold"
    OUTLINE = "outline"
    SHADOW = "shadow"
    HIGHLIGHTED = "highlighted"


class CaptionPosition(str, Enum):
    """Caption position on video."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class ExportFormat(str, Enum):
    """Video export formats."""
    MP4_1080P = "mp4_1080p"
    MP4_720P = "mp4_720p"
    MP4_480P = "mp4_480p"
    WEBM = "webm"
    GIF = "gif"


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ========================
# Caption Schemas
# ========================

class CaptionWord(BaseModel):
    """Single word in captions with timing."""
    word: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None


class CaptionSegment(BaseModel):
    """Caption segment for a scene."""
    scene_order: int
    text: str
    start_time: float
    end_time: float
    words: Optional[list[CaptionWord]] = None


class CaptionRequest(BaseModel):
    """Request to generate captions."""
    story_id: uuid.UUID
    style: CaptionStyle = CaptionStyle.STANDARD
    position: CaptionPosition = CaptionPosition.BOTTOM
    font_size: int = Field(24, ge=12, le=72)
    font_color: str = Field("#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_opacity: float = Field(0.5, ge=0.0, le=1.0)


class CaptionResponse(BaseModel):
    """Response with generated captions."""
    story_id: uuid.UUID
    segments: list[CaptionSegment]
    total_duration: float
    word_count: int


class CaptionSettings(BaseModel):
    """Caption rendering settings."""
    style: CaptionStyle = CaptionStyle.STANDARD
    position: CaptionPosition = CaptionPosition.BOTTOM
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_color: Optional[str] = None
    background_opacity: float = 0.5


# ========================
# Export Schemas
# ========================

class ExportRequest(BaseModel):
    """Request to export a video."""
    story_id: uuid.UUID
    format: ExportFormat = ExportFormat.MP4_1080P
    include_captions: bool = False
    caption_settings: Optional[CaptionSettings] = None
    watermark: Optional[str] = None


class ExportResponse(BaseModel):
    """Response for export job."""
    export_id: str
    story_id: uuid.UUID
    status: ExportStatus
    progress: float = 0.0
    output_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    created_at: datetime


class ExportProgress(BaseModel):
    """Detailed export progress."""
    export_id: str
    status: ExportStatus
    progress: float
    current_step: str
    eta_seconds: Optional[int] = None


# ========================
# Preview Schemas
# ========================

class PreviewStatus(BaseModel):
    """Status for video preview."""
    story_id: uuid.UUID
    ready: bool
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    scenes_ready: int = 0
    scenes_total: int = 0


class ThumbnailRequest(BaseModel):
    """Request to generate thumbnail."""
    story_id: uuid.UUID
    frame_time: float = Field(0.5, ge=0.0, le=1.0, description="Relative position (0-1)")
    width: int = Field(1280, ge=320, le=1920)
    height: int = Field(720, ge=180, le=1080)

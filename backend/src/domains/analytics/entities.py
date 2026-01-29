"""
Analytics Entities (Pydantic Schemas)
Usage tracking and statistics models.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Types of usage events."""
    PROJECT_CREATED = "project_created"
    STORY_GENERATED = "story_generated"
    VIDEO_STARTED = "video_started"
    VIDEO_COMPLETED = "video_completed"
    VIDEO_FAILED = "video_failed"
    AUDIO_GENERATED = "audio_generated"
    EXPORT_COMPLETED = "export_completed"
    API_CALL = "api_call"


class ServiceType(str, Enum):
    """External services tracked."""
    GEMINI = "gemini"
    VEO = "veo"
    IMAGEN = "imagen"
    ELEVENLABS = "elevenlabs"
    EDGE_TTS = "edge_tts"


# ========================
# Event Schemas
# ========================

class UsageEvent(BaseModel):
    """Schema for logging a usage event."""
    event_type: EventType
    user_id: str
    project_id: Optional[uuid.UUID] = None
    story_id: Optional[uuid.UUID] = None
    service: Optional[ServiceType] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Optional[dict] = None


class UsageLogResponse(BaseModel):
    """Schema for usage log response."""
    id: uuid.UUID
    event_type: str
    user_id: str
    project_id: Optional[uuid.UUID] = None
    story_id: Optional[uuid.UUID] = None
    service: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    created_at: datetime


# ========================
# Stats Schemas
# ========================

class GenerationStats(BaseModel):
    """Aggregated generation statistics."""
    total_projects: int = 0
    total_stories: int = 0
    total_videos: int = 0
    videos_completed: int = 0
    videos_failed: int = 0
    total_duration_seconds: int = 0
    total_api_calls: int = 0
    gemini_calls: int = 0
    veo_calls: int = 0
    tts_calls: int = 0
    estimated_cost_usd: float = 0.0


class UserStats(BaseModel):
    """Stats for a specific user."""
    user_id: str
    stats: GenerationStats
    period_start: datetime
    period_end: datetime


class DailyStats(BaseModel):
    """Daily aggregated stats."""
    date: str  # YYYY-MM-DD
    events_count: int
    videos_generated: int
    errors_count: int
    avg_generation_time_ms: Optional[float] = None


class StatsResponse(BaseModel):
    """Response for stats endpoint."""
    overall: GenerationStats
    daily: list[DailyStats]
    period: str  # e.g., "last_7_days"

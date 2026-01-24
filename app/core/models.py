"""
Data Models for the Creative AI Shorts Platform.
Defines Job, Story, Scene, and Media models.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Platform(str, Enum):
    """Target platform enumeration."""
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"


class ScenePurpose(str, Enum):
    """Scene purpose for shorts optimization."""
    HOOK = "hook"
    ESCALATE = "escalate"
    TENSION = "tension"
    TWIST = "twist"
    LOOP = "loop"


# ============== Request/Response Models ==============

class ShortsGenerateRequest(BaseModel):
    """Request model for generating shorts."""
    platform: Platform = Platform.YOUTUBE_SHORTS
    audience: str = "kids_india"
    duration: int = Field(default=30, ge=15, le=60)
    genre: str = "kids"
    language: str = "en-hi"
    quantity: int = Field(default=1, ge=1, le=10)


class ShortsGenerateResponse(BaseModel):
    """Response model for shorts generation request."""
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    """Response model for job status query."""
    job_id: str
    status: JobStatus
    platform: str
    audience: str
    duration: int
    created_at: datetime
    updated_at: datetime
    video_url: Optional[str] = None
    error_message: Optional[str] = None


# ============== Domain Models ==============

class Scene(BaseModel):
    """A single scene in a story."""
    id: int
    start_sec: int
    end_sec: int
    purpose: ScenePurpose
    narration_text: str
    visual_prompt: str
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    image_path: Optional[str] = None


class Story(BaseModel):
    """A complete story with scenes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    total_duration: int
    scenes: List[Scene] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """Job model representing a shorts generation request."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.QUEUED
    platform: Platform = Platform.YOUTUBE_SHORTS
    audience: str = "kids_india"
    duration: int = 30
    genre: str = "kids"
    language: str = "en-hi"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Results
    story_id: Optional[str] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # Critic scores
    hook_score: Optional[float] = None
    pacing_score: Optional[float] = None
    loop_score: Optional[float] = None
    total_score: Optional[float] = None
    retry_count: int = 0


class CriticScore(BaseModel):
    """Critic evaluation scores with emotion alignment and retention (Week 2+3)."""
    hook_score: float = Field(ge=0, le=1)
    pacing_score: float = Field(ge=0, le=1)
    loop_score: float = Field(ge=0, le=1)
    emotion_alignment: float = Field(default=0.5, ge=0, le=1)  # Week 2
    estimated_retention: float = Field(default=0.5, ge=0, le=1)  # Week 3
    total_score: float = Field(ge=0, le=1)
    verdict: str  # "accept" or "retry"
    retry_target: Optional[str] = None  # "hook_only", "ending_only", "full", None
    feedback: Optional[str] = None



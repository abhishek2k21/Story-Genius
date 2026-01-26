"""
Video Format API Routes
Endpoints for multi-platform video format information and generation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

from app.core.video_formats import Platform, VIDEO_FORMATS, get_format

router = APIRouter(prefix="/v1/video", tags=["video-formats"])


class PlatformChoice(str, Enum):
    """Available platform choices for API"""
    youtube_shorts = "youtube_shorts"
    instagram_reels = "instagram_reels"
    tiktok = "tiktok"
    youtube_long = "youtube_long"
    instagram_post = "instagram_post"


class VideoFormatResponse(BaseModel):
    """Video format information"""
    platform: str
    aspect_ratio: str
    resolution: str
    max_duration: int
    recommended_duration_min: int
    recommended_duration_max: int
    fps: int
    safe_zone: dict


class MultiPlatformGenerateRequest(BaseModel):
    """Request for multi-platform video generation"""
    story_id: str = Field(..., description="Story ID to generate video from")
    target_platforms: List[PlatformChoice] = Field(
        default=[PlatformChoice.youtube_shorts],
        description="Target platforms for export"
    )
    duration: Optional[int] = Field(
        default=30,
        ge=5,
        le=180,
        description="Target duration in seconds"
    )


@router.get("/formats")
async def get_available_formats():
    """Get all available video formats with specifications"""
    
    formats = {}
    for platform, fmt in VIDEO_FORMATS.items():
        formats[platform.value] = {
            "aspect_ratio": f"{fmt.aspect_ratio[0]}:{fmt.aspect_ratio[1]}",
            "resolution": f"{fmt.resolution[0]}x{fmt.resolution[1]}",
            "max_duration": fmt.max_duration,
            "recommended_duration": {
                "min": fmt.recommended_duration[0],
                "max": fmt.recommended_duration[1]
            },
            "fps": fmt.fps,
            "safe_zone": fmt.safe_zone
        }
    
    return formats


@router.get("/formats/{platform}", response_model=VideoFormatResponse)
async def get_platform_format(platform: PlatformChoice):
    """Get video format for a specific platform"""
    
    fmt = get_format(Platform(platform.value))
    
    if not fmt:
        raise HTTPException(status_code=404, detail=f"Format not found for {platform}")
    
    return VideoFormatResponse(
        platform=fmt.platform.value,
        aspect_ratio=f"{fmt.aspect_ratio[0]}:{fmt.aspect_ratio[1]}",
        resolution=f"{fmt.resolution[0]}x{fmt.resolution[1]}",
        max_duration=fmt.max_duration,
        recommended_duration_min=fmt.recommended_duration[0],
        recommended_duration_max=fmt.recommended_duration[1],
        fps=fmt.fps,
        safe_zone=fmt.safe_zone
    )


@router.post("/generate")
async def generate_multi_platform_video(request: MultiPlatformGenerateRequest):
    """Generate video for multiple platforms"""
    
    # Validate platforms and duration
    for platform in request.target_platforms:
        fmt = get_format(Platform(platform.value))
        if request.duration > fmt.max_duration:
            raise HTTPException(
                status_code=400,
                detail=f"Duration {request.duration}s exceeds {platform.value} max of {fmt.max_duration}s"
            )
    
    # Return format info (actual generation handled by orchestrator)
    return {
        "story_id": request.story_id,
        "target_platforms": [p.value for p in request.target_platforms],
        "duration": request.duration,
        "status": "ready_for_processing",
        "formats": {
            p.value: {
                "resolution": f"{get_format(Platform(p.value)).resolution[0]}x{get_format(Platform(p.value)).resolution[1]}",
                "aspect_ratio": f"{get_format(Platform(p.value)).aspect_ratio[0]}:{get_format(Platform(p.value)).aspect_ratio[1]}"
            }
            for p in request.target_platforms
        }
    }

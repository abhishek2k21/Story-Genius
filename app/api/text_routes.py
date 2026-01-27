"""
Text Overlay API Routes
Endpoints for text overlay generation, safe zones, and styles.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict

from app.engines.base import EngineInput
from app.engines.registry import EngineRegistry
from app.engines.text_overlay.engine import text_overlay_engine
from app.engines.text_overlay.positioning import list_safe_zones, get_safe_zone, Platform
from app.engines.text_overlay.styling import list_styles, get_style
from app.engines.text_overlay.animation import list_animations, get_animation
from app.engines.text_overlay.timing import generate_timeline

router = APIRouter(prefix="/v1/text", tags=["text_overlay"])


# ==================== Overlay Generation ====================

class GenerateOverlayRequest(BaseModel):
    text: str = Field(..., min_length=1)
    duration: float = Field(..., gt=0, le=300)
    platform: str = Field(default="youtube_shorts")
    style: str = Field(default="boxed")
    position: str = Field(default="lower_third")
    animation_in: str = Field(default="fade_in")
    animation_out: str = Field(default="fade_out")
    fps: int = Field(default=30, ge=24, le=60)


@router.post("/overlay/generate")
async def generate_overlay(request: GenerateOverlayRequest):
    """Generate text overlay with synchronized timing"""
    try:
        input_data = EngineInput(
            job_id="api_request",
            engine_id="text_overlay_engine_v1",
            parameters={
                "text": request.text,
                "duration": request.duration,
                "platform": request.platform,
                "style": request.style,
                "position": request.position,
                "animation_in": request.animation_in,
                "animation_out": request.animation_out,
                "fps": request.fps
            }
        )
        
        output = await text_overlay_engine.execute(input_data)
        
        EngineRegistry.record_execution(
            "text_overlay_engine_v1",
            success=True,
            duration_ms=output.duration_ms
        )
        
        return output.metadata
        
    except Exception as e:
        EngineRegistry.record_execution("text_overlay_engine_v1", success=False, duration_ms=0)
        raise HTTPException(status_code=500, detail=str(e))


class PreviewOverlayRequest(BaseModel):
    text: str = Field(..., min_length=1)
    duration: float = Field(..., gt=0, le=300)
    position: str = Field(default="lower_third")


@router.post("/overlay/preview")
async def preview_overlay(request: PreviewOverlayRequest):
    """Preview overlay timing without full generation"""
    timeline = generate_timeline(
        text=request.text,
        duration=request.duration,
        position=request.position
    )
    return timeline


# ==================== Safe Zones ====================

@router.get("/safe-zones")
async def get_all_safe_zones():
    """List all platform safe zones"""
    return list_safe_zones()


@router.get("/safe-zones/{platform}")
async def get_platform_safe_zone(platform: str):
    """Get safe zone for specific platform"""
    try:
        zone = get_safe_zone(platform)
        return zone.to_dict()
    except Exception:
        raise HTTPException(status_code=404, detail=f"Platform {platform} not found")


# ==================== Styles ====================

@router.get("/styles")
async def get_all_styles():
    """List all style presets"""
    return list_styles()


@router.get("/styles/{preset}")
async def get_style_preset(preset: str):
    """Get specific style preset"""
    style = get_style(preset)
    return style.to_dict()


# ==================== Animations ====================

@router.get("/animations")
async def get_all_animations():
    """List all animation types"""
    return list_animations()


@router.get("/animations/{anim_type}")
async def get_animation_type(anim_type: str):
    """Get specific animation details"""
    anim = get_animation(anim_type)
    return anim.to_dict()


# ==================== Validation ====================

class ValidateOverlayRequest(BaseModel):
    text: str
    duration: float
    platform: str = "youtube_shorts"


@router.post("/validate")
async def validate_overlay_config(request: ValidateOverlayRequest):
    """Validate overlay configuration"""
    errors = []
    warnings = []
    
    # Check text length
    words = request.text.split()
    if len(words) > 100:
        warnings.append("Text has many words, may be hard to read")
    
    # Check duration
    words_per_second = len(words) / request.duration
    if words_per_second > 4:
        warnings.append("Text may appear too fast for comfortable reading")
    if words_per_second < 1:
        warnings.append("Text may stay on screen too long")
    
    # Check platform
    try:
        Platform(request.platform)
    except ValueError:
        errors.append(f"Invalid platform: {request.platform}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "word_count": len(words),
            "words_per_second": round(words_per_second, 2)
        }
    }

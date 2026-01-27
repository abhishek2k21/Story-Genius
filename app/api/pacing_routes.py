"""
Pacing API Routes
Endpoints for pacing generation and presets.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.engines.base import EngineInput
from app.engines.registry import EngineRegistry
from app.engines.pacing.engine import pacing_engine
from app.engines.pacing.presets import list_presets, get_preset, get_optimal_interval

router = APIRouter(prefix="/v1/pacing", tags=["pacing"])


class GeneratePacingRequest(BaseModel):
    target_duration: int = Field(..., ge=5, le=300)
    preset: str = Field(default="standard")
    main_points: int = Field(default=3, ge=1, le=10)


@router.post("/generate")
async def generate_pacing(request: GeneratePacingRequest):
    """Generate pacing for video content"""
    try:
        input_data = EngineInput(
            job_id="api_request",
            engine_id="pacing_engine_v1",
            parameters={
                "target_duration": request.target_duration,
                "preset": request.preset,
                "main_points": request.main_points
            }
        )
        
        output = await pacing_engine.execute(input_data)
        
        EngineRegistry.record_execution(
            "pacing_engine_v1",
            success=True,
            duration_ms=output.duration_ms
        )
        
        return output.metadata
        
    except Exception as e:
        EngineRegistry.record_execution("pacing_engine_v1", success=False, duration_ms=0)
        raise HTTPException(status_code=500, detail=str(e))


class PreviewPacingRequest(BaseModel):
    target_duration: int = Field(..., ge=5, le=300)
    preset: str = Field(default="standard")


@router.post("/preview")
async def preview_pacing(request: PreviewPacingRequest):
    """Preview pacing configuration"""
    preset = get_preset(request.preset)
    interval = get_optimal_interval(request.target_duration)
    
    # Estimate bump count
    bump_count = int((request.target_duration - 4) / ((preset.min_interval + preset.max_interval) / 2))
    
    return {
        "duration": request.target_duration,
        "preset": preset.to_dict(),
        "estimated_bumps": bump_count,
        "optimal_interval": interval
    }


@router.get("/presets")
async def get_all_presets():
    """List all pacing presets"""
    return list_presets()


@router.get("/presets/{name}")
async def get_preset_details(name: str):
    """Get specific preset details"""
    preset = get_preset(name)
    return preset.to_dict()


@router.get("/intervals/{duration}")
async def get_recommended_interval(duration: int):
    """Get recommended bump interval for duration"""
    if duration < 5 or duration > 300:
        raise HTTPException(status_code=400, detail="Duration must be 5-300 seconds")
    return get_optimal_interval(duration)


class ValidatePacingRequest(BaseModel):
    target_duration: int
    bump_count: int
    preset: str = "standard"


@router.post("/validate")
async def validate_pacing(request: ValidatePacingRequest):
    """Validate pacing configuration"""
    preset = get_preset(request.preset)
    warnings = []
    
    # Check interval
    avg_interval = request.target_duration / max(1, request.bump_count)
    if avg_interval < preset.min_interval:
        warnings.append("Too many bumps may overwhelm viewers")
    if avg_interval > preset.max_interval:
        warnings.append("Too few bumps may lose viewer attention")
    
    # Check minimum bumps
    min_bumps = int(request.target_duration / 10)
    if request.bump_count < min_bumps:
        warnings.append(f"Recommend at least {min_bumps} bumps for {request.target_duration}s video")
    
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "stats": {
            "avg_interval": round(avg_interval, 2),
            "recommended_interval": (preset.min_interval + preset.max_interval) / 2
        }
    }

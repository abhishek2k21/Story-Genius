"""
Thumbnail API Routes
Endpoints for thumbnail generation and management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.engines.base import EngineInput
from app.engines.registry import EngineRegistry
from app.engines.thumbnail.engine import thumbnail_engine
from app.engines.thumbnail.presets import list_styles, get_style, optimize_text
from app.engines.thumbnail.export import list_platforms, get_platform_spec
from app.engines.thumbnail.scoring import calculate_ctr_score
from app.engines.thumbnail.analysis import _mock_analysis

router = APIRouter(prefix="/v1/thumbnails", tags=["thumbnails"])


class GenerateThumbnailRequest(BaseModel):
    video_path: Optional[str] = None
    text: str = Field(default="Amazing Content!")
    style: str = Field(default="bold_shadow")
    candidate_count: int = Field(default=5, ge=1, le=10)
    platforms: Optional[List[str]] = None
    output_dir: str = Field(default="output/thumbnails")
    mock_mode: bool = Field(default=True)  # For testing without video


@router.post("/generate")
async def generate_thumbnails(request: GenerateThumbnailRequest):
    """Generate thumbnails for video"""
    try:
        input_data = EngineInput(
            job_id="api_request",
            engine_id="thumbnail_engine_v1",
            parameters={
                "video_path": request.video_path,
                "text": request.text,
                "style": request.style,
                "candidate_count": request.candidate_count,
                "platforms": request.platforms,
                "output_dir": request.output_dir,
                "mock_mode": request.mock_mode
            }
        )
        
        output = await thumbnail_engine.execute(input_data)
        
        EngineRegistry.record_execution(
            "thumbnail_engine_v1",
            success=True,
            duration_ms=output.duration_ms
        )
        
        return output.metadata
        
    except Exception as e:
        EngineRegistry.record_execution("thumbnail_engine_v1", success=False, duration_ms=0)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles")
async def get_all_styles():
    """List all thumbnail style presets"""
    return list_styles()


@router.get("/styles/{preset}")
async def get_style_preset(preset: str):
    """Get specific style preset"""
    style = get_style(preset)
    return style.to_dict()


@router.get("/platforms")
async def get_all_platforms():
    """List all platform specifications"""
    return list_platforms()


@router.get("/platforms/{platform}")
async def get_platform_specification(platform: str):
    """Get platform specification"""
    spec = get_platform_spec(platform)
    return spec.to_dict()


class OptimizeTextRequest(BaseModel):
    text: str
    max_words: int = Field(default=7)


@router.post("/text/optimize")
async def optimize_thumbnail_text(request: OptimizeTextRequest):
    """Optimize text for thumbnail use"""
    optimized = optimize_text(request.text, request.max_words)
    return {
        "original": request.text,
        "optimized": optimized,
        "word_count": len(optimized.split())
    }


class ScoreTextRequest(BaseModel):
    text: str


@router.post("/score")
async def score_thumbnail_text(request: ScoreTextRequest):
    """Score text for CTR prediction"""
    mock_analysis = _mock_analysis("test")
    score = calculate_ctr_score(mock_analysis, request.text)
    return {
        "text": request.text,
        "ctr_score": score.to_dict()
    }

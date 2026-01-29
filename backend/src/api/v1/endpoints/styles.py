"""
Styles API Endpoint
Style presets and batch generation.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from src.domains.video_generation.batch import BatchRequest, BatchResult, generate_batch
from src.domains.video_generation.enhanced_tasks import generate_project_video
from src.domains.video_generation.styles import (
    StyleCategory,
    get_style,
    get_style_categories,
    list_styles,
)

router = APIRouter()


@router.get("/styles")
async def get_available_styles(
    category: Optional[str] = Query(None, description="Filter by category"),
) -> dict:
    """
    Get all available style presets.

    Categories: animation, cinematic, artistic, realistic, vintage
    """
    cat = None
    if category:
        try:
            cat = StyleCategory(category.lower())
        except ValueError:
            pass

    styles = list_styles(cat)

    return {
        "styles": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category.value,
                "preview": s.thumbnail_style,
            }
            for s in styles
        ],
        "categories": get_style_categories(),
    }


@router.get("/styles/{style_id}")
async def get_style_details(style_id: str) -> dict:
    """Get details for a specific style."""
    style = get_style(style_id)

    if not style:
        return {"error": "Style not found"}

    return {
        "id": style.id,
        "name": style.name,
        "category": style.category.value,
        "prompt_prefix": style.prompt_prefix,
        "prompt_suffix": style.prompt_suffix,
        "thumbnail_style": style.thumbnail_style,
        "recommended_duration": style.recommended_duration,
    }


@router.post("/batch", response_model=BatchResult, status_code=202)
async def generate_batch_videos(request: BatchRequest) -> BatchResult:
    """
    Generate multiple videos in batch.

    Max 10 videos per batch, processed in parallel.
    """
    return await generate_batch(request, generate_project_video)

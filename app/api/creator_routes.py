"""
Creator API Routes
Exposes Week 18 features: Preview, Editor, Brand, Calendar, Analytics.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.preview.models import PreviewResult
from app.preview.service import generate_preview
from app.editor.script_editor import get_script_editor
from app.brand.brand_kit import get_brand_service
from app.calendar.service import get_calendar_service
from app.analytics.performance import get_analytics

router = APIRouter(prefix="/v1", tags=["creator"])

# --- PREVIEW ---
@router.post("/preview", response_model=PreviewResult)
async def create_preview(
    topic: str,
    audience: str = "general_adult",
    tone: str = "neutral",
    scenes: int = 5
):
    """Generate a lightweight video preview."""
    result = generate_preview(topic, audience, tone, num_scenes=scenes)
    return result

# --- EDITOR ---
@router.patch("/preview/{preview_id}/scene/{scene_idx}")
async def edit_scene(preview_id: str, scene_idx: int, text: str):
    """Edit script text for a scene."""
    editor = get_script_editor()
    try:
        return editor.update_scene_text(preview_id, scene_idx, text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- BRANDING ---
@router.post("/branding/kits")
async def create_brand_kit(user_id: str, name: str, style: str = "cinematic"):
    """Create a new brand kit."""
    service = get_brand_service()
    return service.create_kit(user_id, name=name, visual_style=style)

@router.get("/branding/kits/{user_id}")
async def list_brand_kits(user_id: str):
    """List brand kits for a user."""
    service = get_brand_service()
    return service.list_user_kits(user_id)

# --- CALENDAR ---
@router.post("/calendar/plan")
async def create_content_plan(user_id: str, start_date: str, end_date: str, freq: int = 3):
    """Generate a content calendar."""
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        service = get_calendar_service()
        return service.create_plan(user_id, start, end, frequency=freq)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ANALYTICS ---
@router.get("/analytics/top/{user_id}")
async def get_top_performing_videos(user_id: str, metric: str = "views"):
    """Get top performing videos."""
    analytics = get_analytics()
    return analytics.get_top_performers(user_id, metric=metric)

@router.get("/analytics/insights/{user_id}")
async def get_creator_insights(user_id: str):
    """Get aggregated insights."""
    analytics = get_analytics()
    return analytics.get_insights(user_id)

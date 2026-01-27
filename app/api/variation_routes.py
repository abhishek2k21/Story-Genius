"""
Variation API Routes
Script variations, hook testing, and preferences.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.scripts.variations.models import VariationStrategy, SelectionType
from app.scripts.variations.service import variation_service
from app.scripts.variations.hooks import hook_test_service
from app.scripts.variations.preferences import preference_service
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/scripts/variations", tags=["variations"])


# ==================== Request Models ====================

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    content_category: str = Field(..., min_length=1)
    target_duration: int = Field(..., ge=15, le=600)
    platform: str = "youtube"
    variation_count: int = Field(default=3, ge=2, le=5)
    variation_strategy: str = "mixed"
    style_hints: Optional[List[str]] = None
    avoid_phrases: Optional[List[str]] = None
    use_preferences: bool = True


class SelectRequest(BaseModel):
    variation_index: int = Field(..., ge=1)
    selection_reason: Optional[str] = None
    modifications: Optional[dict] = None


class HookTestRequest(BaseModel):
    base_script_id: str
    body: str
    cta: str
    topic: str
    hook_count: int = Field(default=5, ge=2, le=10)
    hook_styles: Optional[List[str]] = None


class HookSelectRequest(BaseModel):
    hook_index: int = Field(..., ge=1)
    reason: Optional[str] = None


# ==================== Variation Endpoints ====================

@router.post("/generate")
async def generate_variations(
    request: GenerateRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Generate script variations"""
    try:
        strategy = VariationStrategy(request.variation_strategy)
    except ValueError:
        strategy = VariationStrategy.MIXED
    
    req, variations = variation_service.generate_variations(
        user_id=auth.user.user_id,
        topic=request.topic,
        content_category=request.content_category,
        target_duration=request.target_duration,
        platform=request.platform,
        variation_count=request.variation_count,
        strategy=strategy,
        style_hints=request.style_hints,
        avoid_phrases=request.avoid_phrases,
        use_preferences=request.use_preferences
    )
    
    return {
        "request_id": req.request_id,
        "variation_count": len(variations),
        "variations": [v.to_dict() for v in variations],
        "recommended_index": variations[0].variation_index if variations else None
    }


@router.get("/{request_id}")
async def get_variation_request(
    request_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get variation request details"""
    request = variation_service.get_request(request_id, auth.user.user_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request.to_dict()


@router.get("/{request_id}/variations")
async def list_variations(
    request_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """List all variations for request"""
    variations = variation_service.get_variations(request_id, auth.user.user_id)
    if not variations:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "count": len(variations),
        "variations": [v.to_dict() for v in variations]
    }


@router.get("/{request_id}/compare")
async def compare_variations(
    request_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get comparison view"""
    comparison = variation_service.get_comparison(request_id, auth.user.user_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Request not found")
    return comparison


@router.post("/{request_id}/select")
async def select_variation(
    request_id: str,
    request: SelectRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Select a variation"""
    result, msg = variation_service.select_variation(
        request_id=request_id,
        user_id=auth.user.user_id,
        variation_index=request.variation_index,
        selection_type=SelectionType.MANUAL,
        reason=request.selection_reason or "",
        modifications=request.modifications
    )
    
    if not result:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "selection": result}


@router.post("/{request_id}/finalize")
async def finalize_variation(
    request_id: str,
    request: SelectRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Finalize variation for production"""
    result, msg = variation_service.finalize_variation(
        request_id=request_id,
        user_id=auth.user.user_id,
        variation_index=request.variation_index
    )
    
    if not result:
        raise HTTPException(status_code=400, detail=msg)
    
    return result


# ==================== Hook Testing Endpoints ====================

@router.post("/hooks/test")
async def create_hook_test(
    request: HookTestRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create hook A/B test"""
    test = hook_test_service.create_test(
        user_id=auth.user.user_id,
        base_script_id=request.base_script_id,
        body=request.body,
        cta=request.cta,
        topic=request.topic,
        hook_count=request.hook_count,
        hook_styles=request.hook_styles
    )
    return test.to_dict()


@router.get("/hooks/{test_id}")
async def get_hook_test(
    test_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get hook test details"""
    test = hook_test_service.get_test(test_id, auth.user.user_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test.to_dict()


@router.get("/hooks/{test_id}/compare")
async def compare_hooks(
    test_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get hook comparison view"""
    comparison = hook_test_service.get_comparison(test_id, auth.user.user_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Test not found")
    return comparison


@router.post("/hooks/{test_id}/select")
async def select_hook(
    test_id: str,
    request: HookSelectRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Select hook for test"""
    script, msg = hook_test_service.select_hook(
        test_id=test_id,
        user_id=auth.user.user_id,
        hook_index=request.hook_index,
        reason=request.reason or ""
    )
    
    if not script:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "final_script": script}


# ==================== Preferences Endpoints ====================

@router.get("/history")
async def get_variation_history(
    limit: int = 50,
    auth: AuthContext = Depends(get_current_user)
):
    """Get variation selection history"""
    history = preference_service.get_history(auth.user.user_id, limit)
    return {
        "count": len(history),
        "history": [
            {
                "request_id": h.request_id,
                "topic": h.topic,
                "variation_count": h.variation_count,
                "selected_index": h.selected_index,
                "selected_score": h.selected_score,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
    }


@router.get("/preferences")
async def get_preferences(auth: AuthContext = Depends(get_current_user)):
    """Get learned preferences"""
    prefs = preference_service.get_preferences(auth.user.user_id)
    return prefs.to_dict()


@router.get("/analytics")
async def get_analytics(auth: AuthContext = Depends(get_current_user)):
    """Get variation analytics"""
    return preference_service.get_analytics(auth.user.user_id)

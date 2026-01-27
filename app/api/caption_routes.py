"""
Caption API Routes
Generate, export, and manage captions.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from app.captions.models import CaptionType, SUPPORTED_LANGUAGES
from app.captions.service import caption_service
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/captions", tags=["captions"])


# ==================== Request Models ====================

class GenerateCaptionsRequest(BaseModel):
    project_id: str
    text: str = Field(..., min_length=1)
    start_time: float = 0.0
    duration: float = Field(..., gt=0)
    language_code: str = "en"
    caption_type: str = "subtitle"
    style_preset: str = "default"


class UpdateCueRequest(BaseModel):
    text: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ExportRequest(BaseModel):
    format: str = "srt"
    include_styling: bool = False
    include_positioning: bool = False
    style_preset: Optional[str] = None


class CreateStyleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = Field(default=0.75, ge=0, le=1)
    text_align: str = "center"


class TranslationCue(BaseModel):
    text: str


class AddTranslationRequest(BaseModel):
    language_code: str
    cues: List[TranslationCue]


# ==================== Caption Endpoints ====================

@router.post("/generate")
async def generate_captions(
    request: GenerateCaptionsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Generate captions from text"""
    try:
        caption_type = CaptionType(request.caption_type)
    except ValueError:
        caption_type = CaptionType.SUBTITLE
    
    caption = caption_service.generate_captions(
        project_id=request.project_id,
        text=request.text,
        start_time=request.start_time,
        duration=request.duration,
        language_code=request.language_code,
        caption_type=caption_type,
        style_preset_id=request.style_preset
    )
    
    return caption.to_dict()


@router.get("/{caption_id}")
async def get_caption(
    caption_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get caption details"""
    caption = caption_service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    return caption.to_dict()


@router.delete("/{caption_id}")
async def delete_caption(
    caption_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete caption"""
    if caption_service.delete_caption(caption_id):
        return {"message": "Caption deleted"}
    raise HTTPException(status_code=404, detail="Caption not found")


@router.get("/{caption_id}/cues")
async def list_cues(
    caption_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """List all cues for caption"""
    caption = caption_service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    
    return {
        "count": len(caption.cues),
        "cues": [c.to_dict() for c in caption.cues]
    }


@router.put("/{caption_id}/cues/{cue_id}")
async def update_cue(
    caption_id: str,
    cue_id: str,
    request: UpdateCueRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Update a specific cue"""
    cue, msg = caption_service.update_cue(
        caption_id=caption_id,
        cue_id=cue_id,
        text=request.text,
        start_time=request.start_time,
        end_time=request.end_time
    )
    
    if not cue:
        raise HTTPException(status_code=404, detail=msg)
    
    return {"message": msg, "cue": cue.to_dict()}


# ==================== Export Endpoints ====================

@router.get("/{caption_id}/export/srt")
async def export_srt(
    caption_id: str,
    include_styling: bool = False,
    auth: AuthContext = Depends(get_current_user)
):
    """Export caption as SRT"""
    content, msg = caption_service.export(
        caption_id=caption_id,
        format="srt",
        include_styling=include_styling
    )
    
    if not content:
        raise HTTPException(status_code=404, detail=msg)
    
    return PlainTextResponse(content, media_type="text/plain")


@router.get("/{caption_id}/export/vtt")
async def export_vtt(
    caption_id: str,
    include_styling: bool = False,
    include_positioning: bool = False,
    style_preset: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """Export caption as VTT"""
    content, msg = caption_service.export(
        caption_id=caption_id,
        format="vtt",
        include_styling=include_styling,
        include_positioning=include_positioning,
        style_preset_id=style_preset
    )
    
    if not content:
        raise HTTPException(status_code=404, detail=msg)
    
    return PlainTextResponse(content, media_type="text/vtt")


# ==================== Validation Endpoints ====================

@router.get("/{caption_id}/validate")
async def validate_caption(
    caption_id: str,
    audio_duration: Optional[float] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """Validate caption accessibility"""
    report = caption_service.validate(caption_id, audio_duration)
    if not report:
        raise HTTPException(status_code=404, detail="Caption not found")
    return report


# ==================== Style Endpoints ====================

@router.get("/styles/list")
async def list_styles(auth: AuthContext = Depends(get_current_user)):
    """List style presets"""
    styles = caption_service.get_styles()
    return {
        "count": len(styles),
        "styles": [s.to_dict() for s in styles]
    }


@router.post("/styles")
async def create_style(
    request: CreateStyleRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create custom style preset"""
    style = caption_service.create_style(
        name=request.name,
        font_color=request.font_color,
        background_color=request.background_color,
        background_opacity=request.background_opacity,
        text_align=request.text_align
    )
    return {"message": "Style created", "style": style.to_dict()}


# ==================== Language Endpoints ====================

@router.get("/languages")
async def list_languages():
    """List supported languages"""
    return {
        "count": len(SUPPORTED_LANGUAGES),
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    }


@router.get("/{caption_id}/languages")
async def get_caption_languages(
    caption_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get available languages for caption"""
    caption = caption_service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    
    # Find all versions
    all_captions = caption_service.list_captions(caption.project_id)
    languages = [{"code": c.language_code, "caption_id": c.caption_id} for c in all_captions]
    
    return {"languages": languages}


@router.post("/{caption_id}/languages")
async def add_translation(
    caption_id: str,
    request: AddTranslationRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Add translation for caption"""
    translation, msg = caption_service.add_language_version(
        caption_id=caption_id,
        language_code=request.language_code,
        cues=[{"text": c.text} for c in request.cues]
    )
    
    if not translation:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "caption": translation.to_dict()}


# ==================== Project Integration ====================

@router.get("/project/{project_id}")
async def get_project_captions(
    project_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get all captions for project"""
    captions = caption_service.list_captions(project_id)
    return {
        "count": len(captions),
        "captions": [c.to_dict() for c in captions]
    }

"""
AI Creative API Routes
Endpoints for smart editing, captions, voice, style, and enhancement.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.ai_creative import (
    smart_editor, caption_generator, voice_synthesis,
    style_transfer, content_enhancer,
    CaptionFormat, Emotion, ArtisticStyle, ColorGrading,
    InstagramFilter, Resolution, EnhancementType
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ai-creative", tags=["ai-creative"])


# Request Models

class DetectHighlightsRequest(BaseModel):
    min_duration: float = 2.0
    max_highlights: int = 10


class RemoveSilencesRequest(BaseModel):
    threshold: float = 0.03
    min_silence_duration: float = 0.5


class GenerateCaptionsRequest(BaseModel):
    language: str = "en"
    include_speakers: bool = False


class TranslateCaptionsRequest(BaseModel):
    target_language: str


class TextToSpeechRequest(BaseModel):
    text: str
    voice_profile: str = "default_male"
    emotion: str = "neutral"
    speed: float = 1.0


class CloneVoiceRequest(BaseModel):
    profile_name: str
    voice_samples: List[str]


class ApplyStyleRequest(BaseModel):
    style: str
    intensity: float = 1.0


class UpscaleRequest(BaseModel):
    target_resolution: str  # 720p, 1080p, 1440p, 2160p


class EnhanceRequest(BaseModel):
    enhancements: List[str]
    auto_optimize: bool = True


# SMART EDITING ROUTES

@router.post("/smart-edit/{video_id}/highlights")
async def detect_highlights(video_id: str, request: DetectHighlightsRequest):
    """Detect highlight moments in video"""
    try:
        highlights = smart_editor.auto_detect_highlights(
            video_id=video_id,
            min_duration=request.min_duration,
            max_highlights=request.max_highlights
        )
        
        return {
            "video_id": video_id,
            "highlights": [
                {
                    "start": h.start,
                    "end": h.end,
                    "confidence": h.confidence
                }
                for h in highlights
            ],
            "count": len(highlights)
        }
    except Exception as e:
        logger.error(f"Failed to detect highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-edit/{video_id}/remove-silences")
async def remove_silences(video_id: str, request: RemoveSilencesRequest):
    """Remove silent segments from video"""
    try:
        keep_ranges = smart_editor.remove_silences(
            video_id=video_id,
            threshold=request.threshold,
            min_silence_duration=request.min_silence_duration
        )
        
        return {
            "video_id": video_id,
            "keep_ranges": [
                {"start": r.start, "end": r.end}
                for r in keep_ranges
            ],
            "segments": len(keep_ranges)
        }
    except Exception as e:
        logger.error(f"Failed to remove silences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-edit/{video_id}/cut-points")
async def find_cut_points(video_id: str, sensitivity: float = 0.7):
    """Find optimal cut points"""
    try:
        cut_points = smart_editor.find_cut_points(video_id, sensitivity)
        
        return {
            "video_id": video_id,
            "cut_points": cut_points,
            "count": len(cut_points)
        }
    except Exception as e:
        logger.error(f"Failed to find cut points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CAPTION ROUTES

@router.post("/captions/{video_id}/generate")
async def generate_captions(video_id: str, request: GenerateCaptionsRequest):
    """Generate captions from video audio"""
    try:
        captions = caption_generator.generate_captions(
            video_id=video_id,
            language=request.language,
            include_speakers=request.include_speakers
        )
        
        return {
            "video_id": video_id,
            "language": request.language,
            "captions": [
                {
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "text": c.text,
                    "speaker": c.speaker,
                    "confidence": c.confidence
                }
                for c in captions
            ],
            "count": len(captions)
        }
    except Exception as e:
        logger.error(f"Failed to generate captions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/captions/languages")
async def get_supported_languages():
    """Get supported languages"""
    return {
        "languages": caption_generator.get_supported_languages()
    }


# VOICE SYNTHESIS ROUTES

@router.post("/voice/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Generate speech from text"""
    try:
        emotion = Emotion(request.emotion)
        
        audio = voice_synthesis.text_to_speech(
            text=request.text,
            voice_profile=request.voice_profile,
            emotion=emotion,
            speed=request.speed
        )
        
        return audio
    except Exception as e:
        logger.error(f"Failed to generate speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/profiles")
async def get_voice_profiles(include_custom: bool = True):
    """Get available voice profiles"""
    try:
        profiles = voice_synthesis.get_voice_profiles(include_custom)
        
        return {
            "profiles": [
                {
                    "profile_id": p.profile_id,
                    "name": p.name,
                    "gender": p.gender,
                    "language": p.language,
                    "accent": p.accent,
                    "is_custom": p.is_custom
                }
                for p in profiles
            ],
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to get voice profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# STYLE TRANSFER ROUTES

@router.post("/style/{video_id}/artistic")
async def apply_artistic_style(video_id: str, request: ApplyStyleRequest):
    """Apply artistic style to video"""
    try:
        style = ArtisticStyle(request.style)
        
        result = style_transfer.apply_artistic_style(
            video_id=video_id,
            style=style,
            intensity=request.intensity
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to apply artistic style: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/style/{video_id}/color-grading")
async def apply_color_grading(video_id: str, request: ApplyStyleRequest):
    """Apply color grading preset"""
    try:
        preset = ColorGrading(request.style)
        
        result = style_transfer.apply_color_grading(
            video_id=video_id,
            preset=preset,
            intensity=request.intensity
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to apply color grading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/style/presets")
async def get_style_presets(category: Optional[str] = None):
    """Get available style presets"""
    try:
        presets = style_transfer.get_style_presets(category)
        
        return {
            "presets": [
                {
                    "style_id": p.style_id,
                    "name": p.name,
                    "category": p.category
                }
                for p in presets
            ],
            "count": len(presets)
        }
    except Exception as e:
        logger.error(f"Failed to get style presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ENHANCEMENT ROUTES

@router.post("/enhance/{video_id}/upscale")
async def upscale_video(video_id: str, request: UpscaleRequest):
    """Upscale video to higher resolution"""
    try:
        resolution = Resolution(request.target_resolution)
        
        result = content_enhancer.upscale_video(
            video_id=video_id,
            target_resolution=resolution
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to upscale video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/{video_id}/interpolate")
async def interpolate_frames(video_id: str, target_fps: int = 60):
    """Interpolate frames for smooth slow-motion"""
    try:
        result = content_enhancer.interpolate_frames(
            video_id=video_id,
            target_fps=target_fps
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to interpolate frames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/{video_id}/quality")
async def enhance_quality(video_id: str, request: EnhanceRequest):
    """Apply multiple quality enhancements"""
    try:
        enhancements = [EnhancementType(e) for e in request.enhancements]
        
        result = content_enhancer.enhance_quality(
            video_id=video_id,
            enhancements=enhancements,
            auto_optimize=request.auto_optimize
        )
        
        return {
            "enhanced_video_id": result.enhanced_video_id,
            "original_video_id": result.original_video_id,
            "enhancements_applied": result.enhancements_applied,
            "quality_improvement": f"{result.quality_improvement:.1f}%",
            "processing_time": f"{result.processing_time:.1f}s"
        }
    except Exception as e:
        logger.error(f"Failed to enhance quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

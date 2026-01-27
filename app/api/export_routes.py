"""
Export API Routes
Video export with codecs, presets, and multi-resolution support.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.exports.models import ExportStatus
from app.exports.service import export_service
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/exports", tags=["exports"])


# ==================== Request Models ====================

class CreateExportRequest(BaseModel):
    source_id: str
    video_codec: str = "h264"
    audio_codec: str = "aac"
    resolution: str = "1080p"
    quality_preset: str = "medium"
    bitrate_mode: str = "crf"
    target_size_mb: Optional[float] = None
    two_pass: bool = False
    optimize_for: str = "streaming"
    webhook_url: Optional[str] = None
    custom_settings: Optional[dict] = None


class ExportConfigItem(BaseModel):
    resolution: str = "1080p"
    video_codec: str = "h264"
    quality_preset: str = "medium"


class MultiExportRequest(BaseModel):
    source_id: str
    exports: List[ExportConfigItem]
    naming_pattern: str = "{name}_{resolution}"
    parallel: bool = False


class EstimateRequest(BaseModel):
    duration_seconds: float = Field(..., gt=0)
    video_codec: str = "h264"
    resolution: str = "1080p"
    quality_preset: str = "medium"


# ==================== Export Endpoints ====================

@router.post("")
async def create_export(
    request: CreateExportRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create export job"""
    job, msg = export_service.create_export(
        user_id=auth.user.user_id,
        source_id=request.source_id,
        video_codec=request.video_codec,
        audio_codec=request.audio_codec,
        resolution=request.resolution,
        quality_preset=request.quality_preset,
        bitrate_mode=request.bitrate_mode,
        target_size_mb=request.target_size_mb,
        two_pass=request.two_pass,
        optimize_for=request.optimize_for,
        webhook_url=request.webhook_url or "",
        custom_settings=request.custom_settings
    )
    
    if not job:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "export": job.to_dict()}


@router.get("")
async def list_exports(
    status: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """List export jobs"""
    status_enum = ExportStatus(status) if status else None
    jobs = export_service.list_exports(auth.user.user_id, status_enum)
    
    return {
        "count": len(jobs),
        "exports": [j.to_dict() for j in jobs]
    }


@router.get("/{export_id}")
async def get_export(
    export_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get export details"""
    job = export_service.get_export(export_id, auth.user.user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    return job.to_dict()


@router.delete("/{export_id}")
async def cancel_export(
    export_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Cancel export"""
    success, msg = export_service.cancel_export(export_id, auth.user.user_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.get("/{export_id}/progress")
async def get_progress(
    export_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get export progress"""
    job = export_service.get_export(export_id, auth.user.user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return {
        "export_id": job.export_id,
        "status": job.status.value,
        "progress": job.progress,
        "current_stage": job.current_stage
    }


# ==================== Multi-Export Endpoints ====================

@router.post("/multi")
async def create_multi_export(
    request: MultiExportRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create multiple exports"""
    exports_config = [e.dict() for e in request.exports]
    
    jobs, msg = export_service.create_multi_export(
        user_id=auth.user.user_id,
        source_id=request.source_id,
        exports=exports_config,
        naming_pattern=request.naming_pattern,
        parallel=request.parallel
    )
    
    return {
        "message": msg,
        "count": len(jobs),
        "exports": [j.to_dict() for j in jobs]
    }


# ==================== Estimation Endpoints ====================

@router.post("/estimate")
async def estimate_export(request: EstimateRequest):
    """Estimate file size and encoding time"""
    return export_service.estimate_export(
        duration_seconds=request.duration_seconds,
        video_codec=request.video_codec,
        resolution=request.resolution,
        quality_preset=request.quality_preset
    )


# ==================== Codec Endpoints ====================

@router.get("/codecs/list")
async def list_codecs():
    """List available codecs"""
    return export_service.get_codecs()


@router.get("/codecs/{codec_id}")
async def get_codec(codec_id: str):
    """Get codec details"""
    from app.exports.codecs import get_video_codec, get_audio_codec
    
    video = get_video_codec(codec_id)
    if video:
        return {"type": "video", "codec": video.to_dict()}
    
    audio = get_audio_codec(codec_id)
    if audio:
        return {"type": "audio", "codec": audio.to_dict()}
    
    raise HTTPException(status_code=404, detail="Codec not found")


# ==================== Preset Endpoints ====================

@router.get("/presets/list")
async def list_presets():
    """List quality presets"""
    presets = export_service.get_presets()
    return {"count": len(presets), "presets": presets}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get preset details"""
    from app.exports.presets import get_preset as fetch_preset
    preset = fetch_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset.to_dict()


# ==================== Resolution Endpoints ====================

@router.get("/resolutions/list")
async def list_resolutions(aspect_ratio: Optional[str] = None):
    """List available resolutions"""
    resolutions = export_service.get_resolutions(aspect_ratio)
    return {"count": len(resolutions), "resolutions": resolutions}


# ==================== Platform Endpoints ====================

@router.get("/platforms/list")
async def list_platforms():
    """List platform presets"""
    platforms = export_service.get_platforms()
    return {"count": len(platforms), "platforms": platforms}


@router.get("/platforms/{platform_id}")
async def get_platform(platform_id: str):
    """Get platform settings"""
    from app.exports.presets import get_platform as fetch_platform
    platform = fetch_platform(platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    return platform.to_dict()


@router.get("/platforms/{platform_id}/settings")
async def get_platform_settings(
    platform_id: str,
    duration_seconds: float = 60
):
    """Get optimized settings for platform"""
    settings = export_service.get_platform_settings(platform_id, duration_seconds)
    if not settings:
        raise HTTPException(status_code=404, detail="Platform not found")
    return settings

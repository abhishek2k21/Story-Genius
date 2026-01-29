"""
Content API Endpoints
Captions, exports, and preview.
"""
import uuid
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.core.dependencies import DbSession, OptionalApiKey
from src.domains.content.entities import (
    CaptionRequest,
    CaptionResponse,
    ExportRequest,
    ExportResponse,
    PreviewStatus,
    ThumbnailRequest,
)
from src.domains.content.services import ContentService

router = APIRouter()


@router.post("/captions", response_model=CaptionResponse)
async def generate_captions(
    request: CaptionRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> CaptionResponse:
    """
    Generate captions from story narrations.

    Returns timed caption segments for video overlay.
    """
    service = ContentService(db)
    return await service.generate_captions(request)


@router.post("/exports", response_model=ExportResponse, status_code=202)
async def export_video(
    request: ExportRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> ExportResponse:
    """
    Start video export job.

    Returns job ID for status polling.
    """
    service = ContentService(db)
    return await service.export_video(request)


@router.get("/preview/{story_id}", response_model=PreviewStatus)
async def get_preview(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> PreviewStatus:
    """Get video preview status."""
    service = ContentService(db)
    return await service.get_preview_status(story_id)


@router.post("/thumbnails", response_model=dict)
async def generate_thumbnail(
    request: ThumbnailRequest,
    db: DbSession,
    api_key: OptionalApiKey,
) -> dict:
    """Generate video thumbnail."""
    service = ContentService(db)
    path = await service.generate_thumbnail(request)
    return {"thumbnail_path": path}


@router.get("/stream/{story_id}")
async def stream_preview(
    story_id: uuid.UUID,
    db: DbSession,
    api_key: OptionalApiKey,
) -> StreamingResponse:
    """
    Stream video preview.

    Returns video as streaming response.
    """
    from pathlib import Path

    service = ContentService(db)
    status = await service.get_preview_status(story_id)

    if not status.ready or not status.preview_url:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not ready")

    video_path = Path(status.preview_url)

    def iterfile():
        with open(video_path, "rb") as f:
            while chunk := f.read(65536):  # 64KB chunks
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename={video_path.name}",
            "Content-Length": str(video_path.stat().st_size),
        },
    )

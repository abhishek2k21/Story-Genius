"""
Content Service
Caption generation, video export, and preview.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ExternalServiceError
from src.core.logging import get_logger
from src.core.settings import settings
from src.database.models import Scene, Story
from src.domains.content.entities import (
    CaptionRequest,
    CaptionResponse,
    CaptionSegment,
    CaptionSettings,
    ExportFormat,
    ExportRequest,
    ExportResponse,
    ExportStatus,
    PreviewStatus,
    ThumbnailRequest,
)
from src.domains.stories.repositories import SceneRepository, StoryRepository

logger = get_logger(__name__)


class ContentService:
    """Service for content operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.story_repo = StoryRepository(session)
        self.scene_repo = SceneRepository(session)

    async def generate_captions(
        self,
        request: CaptionRequest,
    ) -> CaptionResponse:
        """
        Generate captions from scene narrations.

        Creates timed caption segments based on scene durations.
        """
        story = await self.story_repo.get_by_id(request.story_id)
        if not story:
            raise NotFoundError("Story", str(request.story_id))

        scenes = await self.scene_repo.get_by_story(request.story_id)
        if not scenes:
            raise NotFoundError("Scenes", f"No scenes for story {request.story_id}")

        segments = []
        current_time = 0.0
        total_words = 0

        for scene in scenes:
            duration = scene.duration_seconds or 5.0
            text = scene.narration

            # Create segment
            segment = CaptionSegment(
                scene_order=scene.order,
                text=text,
                start_time=current_time,
                end_time=current_time + duration,
            )
            segments.append(segment)

            total_words += len(text.split())
            current_time += duration

        logger.info(f"Generated {len(segments)} caption segments for story {request.story_id}")

        return CaptionResponse(
            story_id=request.story_id,
            segments=segments,
            total_duration=current_time,
            word_count=total_words,
        )

    async def export_video(
        self,
        request: ExportRequest,
    ) -> ExportResponse:
        """
        Start video export job.

        Returns immediately with job ID for async polling.
        """
        story = await self.story_repo.get_by_id(request.story_id)
        if not story:
            raise NotFoundError("Story", str(request.story_id))

        export_id = str(uuid.uuid4())[:8]

        # Queue export task (in production, this would be a Celery task)
        logger.info(f"Starting export {export_id} for story {request.story_id}")

        return ExportResponse(
            export_id=export_id,
            story_id=request.story_id,
            status=ExportStatus.PENDING,
            progress=0.0,
            created_at=datetime.now(timezone.utc),
        )

    async def process_export(
        self,
        story_id: uuid.UUID,
        export_format: ExportFormat,
        include_captions: bool = False,
        caption_settings: Optional[CaptionSettings] = None,
    ) -> str:
        """
        Process video export synchronously.

        Returns path to exported video.
        """
        story = await self.story_repo.get_by_id(story_id)
        if not story or not story.video_path:
            raise NotFoundError("Video", f"No video for story {story_id}")

        input_path = story.video_path
        output_dir = settings.media_dir / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine output settings based on format
        resolution_map = {
            ExportFormat.MP4_1080P: (1920, 1080),
            ExportFormat.MP4_720P: (1280, 720),
            ExportFormat.MP4_480P: (854, 480),
        }

        width, height = resolution_map.get(export_format, (1920, 1080))
        output_path = output_dir / f"export_{story_id}_{export_format.value}.mp4"

        def _do_export():
            from moviepy import VideoFileClip

            video = VideoFileClip(input_path)

            # Resize if needed
            if video.w != width or video.h != height:
                video = video.resized((width, height))

            # Add captions if requested
            if include_captions and caption_settings:
                # TODO: Implement caption overlay with TextClip
                pass

            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=4,
                logger=None,
            )
            video.close()

            return str(output_path)

        result = await asyncio.get_event_loop().run_in_executor(None, _do_export)

        logger.info(f"Exported video to {result}")
        return result

    async def get_preview_status(
        self,
        story_id: uuid.UUID,
    ) -> PreviewStatus:
        """Get preview status for a story."""
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise NotFoundError("Story", str(story_id))

        scenes = await self.scene_repo.get_by_story(story_id)
        scenes_ready = sum(1 for s in scenes if s.video_path and Path(s.video_path).exists())

        ready = story.video_path and Path(story.video_path).exists()

        return PreviewStatus(
            story_id=story_id,
            ready=ready,
            preview_url=story.video_path if ready else None,
            thumbnail_url=story.thumbnail_path,
            duration_seconds=story.duration_seconds,
            scenes_ready=scenes_ready,
            scenes_total=len(scenes),
        )

    async def generate_thumbnail(
        self,
        request: ThumbnailRequest,
    ) -> str:
        """Generate thumbnail from video."""
        story = await self.story_repo.get_by_id(request.story_id)
        if not story or not story.video_path:
            raise NotFoundError("Video", f"No video for story {request.story_id}")

        input_path = story.video_path
        output_dir = settings.media_dir / "thumbnails"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"thumb_{request.story_id}.jpg"

        def _generate():
            from moviepy import VideoFileClip

            video = VideoFileClip(input_path)
            frame_time = video.duration * request.frame_time

            frame = video.get_frame(frame_time)
            video.close()

            # Save frame as image
            from PIL import Image
            img = Image.fromarray(frame)
            img = img.resize((request.width, request.height))
            img.save(str(output_path), "JPEG", quality=90)

            return str(output_path)

        result = await asyncio.get_event_loop().run_in_executor(None, _generate)

        # Update story thumbnail
        story.thumbnail_path = result
        await self.story_repo.update(story)

        logger.info(f"Generated thumbnail: {result}")
        return result

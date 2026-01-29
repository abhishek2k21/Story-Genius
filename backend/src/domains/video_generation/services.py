"""
Video Generation Service
Orchestrates Veo video generation and MoviePy stitching.
"""
import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.elevenlabs_client import get_elevenlabs_client
from src.clients.storage_client import get_storage_client
from src.clients.vertex_client import get_vertex_client
from src.core.exceptions import NotFoundError, ExternalServiceError
from src.core.logging import get_logger
from src.core.settings import settings
from src.database.models import Scene, Story
from src.domains.stories.repositories import SceneRepository, StoryRepository
from src.domains.video_generation.entities import (
    ClipResponse,
    ClipStatus,
    SceneAssetResponse,
    StitchResponse,
    VideoJobResponse,
    VideoJobStatus,
)

logger = get_logger(__name__)


class VideoGenerationService:
    """Service for video generation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.story_repo = StoryRepository(session)
        self.scene_repo = SceneRepository(session)
        self.vertex_client = get_vertex_client()
        self.tts_client = get_elevenlabs_client()
        self.storage = get_storage_client()

    async def generate_scene_audio(
        self,
        scene: Scene,
        voice_id: Optional[str] = None,
    ) -> str:
        """Generate audio for a single scene."""
        output_path = settings.media_dir / "audio" / f"scene_{scene.id}.mp3"

        audio_path = await self.tts_client.generate_speech(
            text=scene.narration,
            output_path=str(output_path),
            voice=voice_id or "en-US-AriaNeural",
        )

        # Update scene
        scene.audio_path = str(audio_path)
        await self.scene_repo.update(scene)

        logger.info(f"Generated audio for scene {scene.id}")
        return audio_path

    async def generate_scene_video(
        self,
        scene: Scene,
        style_prefix: Optional[str] = None,
    ) -> str:
        """Generate video for a single scene using Veo."""
        output_path = settings.media_dir / "video" / f"clip_{scene.id}.mp4"

        # Build prompt with style prefix
        prompt = scene.visual_prompt
        if style_prefix:
            prompt = f"{style_prefix}. {prompt}"

        video_path = await self.vertex_client.generate_video(
            prompt=prompt,
            output_path=str(output_path),
            duration_seconds=int(scene.duration_seconds or 5),
        )

        # Update scene
        scene.video_path = str(video_path)
        await self.scene_repo.update(scene)

        logger.info(f"Generated video for scene {scene.id}")
        return video_path

    async def generate_scene_assets(
        self,
        scene_id: uuid.UUID,
        generate_audio: bool = True,
        generate_video: bool = True,
    ) -> SceneAssetResponse:
        """Generate all assets for a scene."""
        scene = await self.scene_repo.get_by_id(scene_id)
        if not scene:
            raise NotFoundError("Scene", str(scene_id))

        audio_path = None
        video_path = None

        try:
            if generate_audio:
                audio_path = await self.generate_scene_audio(scene)

            if generate_video:
                story = await self.story_repo.get_by_id(scene.story_id)
                video_path = await self.generate_scene_video(
                    scene,
                    style_prefix=story.style_prefix if story else None,
                )

            return SceneAssetResponse(
                scene_id=scene_id,
                audio_path=audio_path,
                video_path=video_path,
                image_path=scene.image_path,
                status=ClipStatus.COMPLETED,
            )

        except Exception as e:
            logger.error(f"Failed to generate assets for scene {scene_id}: {e}")
            return SceneAssetResponse(
                scene_id=scene_id,
                audio_path=audio_path,
                video_path=video_path,
                status=ClipStatus.FAILED,
            )

    async def stitch_video(
        self,
        story_id: uuid.UUID,
        output_filename: Optional[str] = None,
    ) -> StitchResponse:
        """Stitch all scene clips into final video using MoviePy."""
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise NotFoundError("Story", str(story_id))

        scenes = await self.scene_repo.get_by_story(story_id)
        if not scenes:
            raise NotFoundError("Scenes", f"No scenes for story {story_id}")

        # Collect clip paths
        clips_data = []
        for scene in scenes:
            if not scene.video_path or not Path(scene.video_path).exists():
                raise ExternalServiceError(
                    "Stitch",
                    f"Missing video for scene {scene.id}",
                )
            clips_data.append({
                "video_path": scene.video_path,
                "audio_path": scene.audio_path,
                "duration": scene.duration_seconds,
            })

        # Stitch using MoviePy
        output_path = settings.media_dir / "video" / (
            output_filename or f"final_{story_id}.mp4"
        )

        final_path, duration = await self._stitch_clips(clips_data, str(output_path))

        # Update story
        story.video_path = final_path
        story.status = "completed"
        story.duration_seconds = int(duration)
        await self.story_repo.update(story)

        # Get file size
        file_size_mb = os.path.getsize(final_path) / (1024 * 1024)

        logger.info(f"Stitched final video for story {story_id}: {final_path}")

        return StitchResponse(
            video_path=final_path,
            duration_seconds=duration,
            file_size_mb=round(file_size_mb, 2),
        )

    async def _stitch_clips(
        self,
        clips_data: list[dict],
        output_path: str,
    ) -> tuple[str, float]:
        """Stitch clips together with audio using MoviePy."""

        def _do_stitch():
            from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips

            clips = []
            total_duration = 0.0

            for data in clips_data:
                video = VideoFileClip(data["video_path"])

                # Sync audio if available
                if data.get("audio_path") and Path(data["audio_path"]).exists():
                    audio = AudioFileClip(data["audio_path"])
                    # Adjust video duration to match audio
                    if audio.duration:
                        video = video.with_duration(audio.duration)
                        video = video.with_audio(audio)
                    total_duration += audio.duration
                else:
                    total_duration += video.duration

                clips.append(video)

            # Concatenate all clips
            final = concatenate_videoclips(clips, method="compose")

            # Write final video
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                preset="medium",
                threads=4,
                logger=None,  # Suppress moviepy logs
            )

            # Cleanup
            for clip in clips:
                clip.close()
            final.close()

            return output_path, total_duration

        # Run in thread pool (MoviePy is synchronous)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            _do_stitch,
        )

        return result

    async def get_clip_status(
        self,
        story_id: uuid.UUID,
    ) -> list[ClipResponse]:
        """Get status of all clips for a story."""
        scenes = await self.scene_repo.get_by_story(story_id)

        clips = []
        for scene in scenes:
            status = ClipStatus.PENDING
            if scene.video_path and Path(scene.video_path).exists():
                status = ClipStatus.COMPLETED
            elif scene.video_path:
                status = ClipStatus.FAILED

            clips.append(ClipResponse(
                scene_id=scene.id,
                scene_order=scene.order,
                status=status,
                video_path=scene.video_path,
                audio_path=scene.audio_path,
                duration_seconds=scene.duration_seconds,
            ))

        return clips

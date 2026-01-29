"""
Video Generation Celery Tasks
Async orchestration for video generation pipeline.
"""
import uuid
from datetime import datetime

from celery import shared_task

from src.core.logging import get_logger
from src.database.session import async_session_context
from src.domains.stories.repositories import SceneRepository, StoryRepository
from src.domains.video_generation.services import VideoGenerationService
from src.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="generate_story_video")
def generate_story_video(
    self,
    story_id: str,
    generate_audio: bool = True,
    generate_video: bool = True,
    stitch_final: bool = True,
) -> dict:
    """
    Generate complete video for a story.

    Pipeline:
    1. Generate audio for each scene (TTS)
    2. Generate video clips for each scene (Veo)
    3. Stitch all clips into final video (MoviePy)

    This task runs the async code in a sync context for Celery.
    """
    import asyncio

    async def _run():
        async with async_session_context() as session:
            story_repo = StoryRepository(session)
            scene_repo = SceneRepository(session)
            service = VideoGenerationService(session)

            story_uuid = uuid.UUID(story_id)
            story = await story_repo.get_by_id(story_uuid)

            if not story:
                raise ValueError(f"Story {story_id} not found")

            scenes = await scene_repo.get_by_story(story_uuid)
            total_scenes = len(scenes)

            if total_scenes == 0:
                raise ValueError(f"No scenes found for story {story_id}")

            logger.info(f"Starting video generation for story {story_id} ({total_scenes} scenes)")

            # Update story status
            story.status = "generating_assets"
            await story_repo.update(story)
            await session.commit()

            # Step 1: Generate audio for all scenes
            if generate_audio:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": "audio", "progress": 0.0, "current": 0, "total": total_scenes},
                )

                for i, scene in enumerate(scenes):
                    try:
                        await service.generate_scene_audio(scene, story.voice_id)
                        await session.commit()

                        progress = (i + 1) / total_scenes * 0.3  # Audio is 30% of work
                        self.update_state(
                            state="PROGRESS",
                            meta={"step": "audio", "progress": progress, "current": i + 1, "total": total_scenes},
                        )
                    except Exception as e:
                        logger.error(f"Audio generation failed for scene {scene.id}: {e}")

            # Step 2: Generate video clips
            if generate_video:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": "video", "progress": 0.3, "current": 0, "total": total_scenes},
                )

                for i, scene in enumerate(scenes):
                    try:
                        await service.generate_scene_video(scene, story.style_prefix)
                        await session.commit()

                        progress = 0.3 + (i + 1) / total_scenes * 0.5  # Video is 50% of work
                        self.update_state(
                            state="PROGRESS",
                            meta={"step": "video", "progress": progress, "current": i + 1, "total": total_scenes},
                        )
                    except Exception as e:
                        logger.error(f"Video generation failed for scene {scene.id}: {e}")

            # Step 3: Stitch final video
            if stitch_final:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": "stitching", "progress": 0.8},
                )

                result = await service.stitch_video(story_uuid)
                await session.commit()

                return {
                    "story_id": story_id,
                    "video_path": result.video_path,
                    "duration_seconds": result.duration_seconds,
                    "file_size_mb": result.file_size_mb,
                    "status": "completed",
                }

            return {
                "story_id": story_id,
                "status": "completed",
                "message": "Assets generated, stitching skipped",
            }

    # Run async code
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="generate_scene_assets")
def generate_scene_assets(
    self,
    scene_id: str,
    generate_audio: bool = True,
    generate_video: bool = True,
) -> dict:
    """Generate assets for a single scene."""
    import asyncio

    async def _run():
        async with async_session_context() as session:
            service = VideoGenerationService(session)
            result = await service.generate_scene_assets(
                uuid.UUID(scene_id),
                generate_audio,
                generate_video,
            )
            await session.commit()

            return {
                "scene_id": scene_id,
                "audio_path": result.audio_path,
                "video_path": result.video_path,
                "status": result.status.value,
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="stitch_story_video")
def stitch_story_video(
    self,
    story_id: str,
    output_filename: str | None = None,
) -> dict:
    """Stitch clips for a story into final video."""
    import asyncio

    async def _run():
        async with async_session_context() as session:
            service = VideoGenerationService(session)
            result = await service.stitch_video(
                uuid.UUID(story_id),
                output_filename,
            )
            await session.commit()

            return {
                "story_id": story_id,
                "video_path": result.video_path,
                "duration_seconds": result.duration_seconds,
                "file_size_mb": result.file_size_mb,
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()

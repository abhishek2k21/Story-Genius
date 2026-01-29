"""
Advanced Video Generation Celery Tasks
Parallel scene generation with fallbacks.
"""
import uuid

from celery import shared_task

from src.core.logging import get_logger
from src.database.session import async_session_context
from src.domains.stories.repositories import SceneRepository, StoryRepository
from src.domains.video_generation.enhanced_service import EnhancedVideoService
from src.domains.video_generation.services import VideoGenerationService
from src.tasks.celery_app import celery_app
from src.utils.video.pacing import calculate_pacing

logger = get_logger(__name__)


@celery_app.task(bind=True, name="generate_video_enhanced")
def generate_video_enhanced(
    self,
    story_id: str,
    max_concurrent: int = 3,
    use_reference_images: bool = True,
) -> dict:
    """
    Enhanced video generation with parallel processing.

    Features:
    - Parallel scene generation
    - Reference image generation
    - Automatic fallbacks
    - Progress tracking
    """
    import asyncio

    async def _run():
        async with async_session_context() as session:
            service = EnhancedVideoService(session)
            story_repo = StoryRepository(session)
            scene_repo = SceneRepository(session)

            story_uuid = uuid.UUID(story_id)
            story = await story_repo.get_by_id(story_uuid)

            if not story:
                raise ValueError(f"Story {story_id} not found")

            scenes = await scene_repo.get_by_story(story_uuid)
            total_scenes = len(scenes)

            logger.info(f"Enhanced generation for story {story_id} ({total_scenes} scenes)")

            # Initial progress
            self.update_state(
                state="PROGRESS",
                meta={"step": "init", "progress": 0.0, "total": total_scenes},
            )

            # Generate all scenes with fallbacks
            results = await service.generate_story_parallel(
                story_uuid,
                max_concurrent=max_concurrent,
            )

            # Stitch if successful
            if results["success"] > 0:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": "stitching", "progress": 0.9},
                )

                basic_service = VideoGenerationService(session)
                stitch_result = await basic_service.stitch_video(story_uuid)
                await session.commit()

                return {
                    "story_id": story_id,
                    "video_path": stitch_result.video_path,
                    "duration_seconds": stitch_result.duration_seconds,
                    "scenes_generated": results["success"],
                    "scenes_failed": results["failed"],
                    "status": "completed",
                }

            return {
                "story_id": story_id,
                "status": "failed",
                "scenes_failed": results["failed"],
                "message": "All scene generations failed",
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="generate_project_video")
def generate_project_video(
    self,
    project_id: str,
    prompt: str,
    style_prefix: str = "",
    voice_id: str = "",
    target_duration: int = 60,
) -> dict:
    """
    Full pipeline: prompt → story → scenes → video.

    This is the main endpoint task that orchestrates everything.
    """
    import asyncio
    import json

    async def _run():
        async with async_session_context() as session:
            from src.domains.stories.entities import StoryGenerateRequest
            from src.domains.stories.services import StoryService

            story_service = StoryService(session)
            video_service = EnhancedVideoService(session)

            # Step 1: Generate story with Gemini
            self.update_state(
                state="PROGRESS",
                meta={"step": "generating_script", "progress": 0.1},
            )

            request = StoryGenerateRequest(
                project_id=uuid.UUID(project_id),
                prompt=prompt,
                style_prefix=style_prefix or None,
                voice_id=voice_id or None,
                target_duration_seconds=target_duration,
                num_scenes=max(3, target_duration // 15),
            )

            story = await story_service.generate_story(request, "celery_worker")
            await session.commit()

            logger.info(f"Generated story {story.id} with {story.scene_count} scenes")

            # Step 2: Generate all assets
            self.update_state(
                state="PROGRESS",
                meta={"step": "generating_assets", "progress": 0.3, "story_id": str(story.id)},
            )

            results = await video_service.generate_story_parallel(story.id)
            await session.commit()

            # Step 3: Stitch final video
            if results["success"] > 0:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": "stitching", "progress": 0.9},
                )

                basic_service = VideoGenerationService(session)
                stitch_result = await basic_service.stitch_video(story.id)
                await session.commit()

                return {
                    "project_id": project_id,
                    "story_id": str(story.id),
                    "video_path": stitch_result.video_path,
                    "duration_seconds": stitch_result.duration_seconds,
                    "file_size_mb": stitch_result.file_size_mb,
                    "scenes_generated": results["success"],
                    "status": "completed",
                }

            return {
                "project_id": project_id,
                "story_id": str(story.id),
                "status": "failed",
                "message": "Asset generation failed",
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()

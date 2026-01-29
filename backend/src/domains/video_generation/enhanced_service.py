"""
Enhanced Video Generation Service
Advanced pipeline with reference images, parallel generation, and fallbacks.
"""
import asyncio
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.vertex_client import get_vertex_client
from src.clients.elevenlabs_client import get_elevenlabs_client
from src.core.exceptions import ExternalServiceError, NotFoundError
from src.core.logging import get_logger
from src.core.observability import trace
from src.core.retry import VEO_RETRY, retry
from src.core.settings import settings
from src.database.models import Scene, Story
from src.domains.stories.repositories import SceneRepository, StoryRepository
from src.utils.video.effects import EffectType, apply_effect, EffectConfig
from src.utils.video.pacing import calculate_pacing, PacingConfig

logger = get_logger(__name__)


class EnhancedVideoService:
    """
    Enhanced video generation service.

    Features:
    - Reference image generation with Imagen
    - Parallel scene processing
    - Fallback strategies (cartoon style, Ken Burns)
    - Quality enhancements
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.story_repo = StoryRepository(session)
        self.scene_repo = SceneRepository(session)
        self.vertex_client = get_vertex_client()
        self.tts_client = get_elevenlabs_client()

    @trace("generate_reference_image")
    async def generate_reference_image(
        self,
        scene: Scene,
        style_prefix: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate reference image for scene using Imagen.

        Args:
            scene: Scene to generate image for
            style_prefix: Visual style prefix

        Returns:
            Path to generated image or None
        """
        output_dir = settings.media_dir / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"ref_{scene.id}.png"

        prompt = scene.visual_prompt
        if style_prefix:
            prompt = f"{style_prefix}. {prompt}"

        try:
            image_path = await self.vertex_client.generate_image(
                prompt=prompt,
                output_path=str(output_path),
            )

            scene.image_path = image_path
            await self.scene_repo.update(scene)

            logger.info(f"Generated reference image for scene {scene.id}")
            return image_path

        except Exception as e:
            logger.warning(f"Failed to generate reference image: {e}")
            return None

    @retry(config=VEO_RETRY, operation_name="generate_scene_video")
    async def generate_scene_video_with_ref(
        self,
        scene: Scene,
        reference_image: Optional[str] = None,
        style_prefix: Optional[str] = None,
    ) -> str:
        """
        Generate video for scene with optional reference image.

        Args:
            scene: Scene to generate video for
            reference_image: Path to reference image
            style_prefix: Visual style prefix

        Returns:
            Path to generated video
        """
        output_dir = settings.media_dir / "video"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"clip_{scene.id}.mp4"

        prompt = scene.visual_prompt
        if style_prefix:
            prompt = f"{style_prefix}. {prompt}"

        video_path = await self.vertex_client.generate_video(
            prompt=prompt,
            output_path=str(output_path),
            reference_image=reference_image,
            duration_seconds=int(scene.duration_seconds or 5),
        )

        scene.video_path = video_path
        await self.scene_repo.update(scene)

        return video_path

    async def generate_fallback_video(
        self,
        scene: Scene,
        fallback_type: str = "ken_burns",
    ) -> str:
        """
        Generate fallback video from static image.

        Used when Veo generation fails.

        Args:
            scene: Scene to generate video for
            fallback_type: "ken_burns" or "cartoon"

        Returns:
            Path to generated video
        """
        output_dir = settings.media_dir / "video"
        output_path = output_dir / f"fallback_{scene.id}.mp4"

        if not scene.image_path or not Path(scene.image_path).exists():
            # Generate reference image first
            await self.generate_reference_image(scene)

        if not scene.image_path:
            raise ExternalServiceError("Fallback", "No image available for fallback")

        # Create video from image with Ken Burns effect
        from moviepy import ImageClip

        duration = scene.duration_seconds or 5.0
        clip = ImageClip(scene.image_path, duration=duration)
        clip = clip.resized((1920, 1080))

        temp_path = str(output_path).replace(".mp4", "_temp.mp4")
        clip.write_videofile(temp_path, fps=30, codec="libx264", logger=None)
        clip.close()

        # Apply Ken Burns effect
        effect = EffectConfig(effect_type=EffectType.KEN_BURNS, duration=duration)
        final_path = apply_effect(temp_path, str(output_path), effect)

        # Cleanup temp
        Path(temp_path).unlink(missing_ok=True)

        scene.video_path = final_path
        await self.scene_repo.update(scene)

        logger.info(f"Generated fallback video for scene {scene.id}")
        return final_path

    @trace("generate_scene_with_fallback")
    async def generate_scene_with_fallback(
        self,
        scene: Scene,
        style_prefix: Optional[str] = None,
    ) -> str:
        """
        Generate scene video with automatic fallback.

        Attempts:
        1. Veo with reference image
        2. Veo without reference
        3. Ken Burns fallback

        Returns:
            Path to generated video
        """
        # Try to generate reference image
        ref_image = await self.generate_reference_image(scene, style_prefix)

        # Attempt Veo with reference
        try:
            return await self.generate_scene_video_with_ref(scene, ref_image, style_prefix)
        except Exception as e:
            logger.warning(f"Veo with reference failed: {e}")

        # Attempt Veo without reference
        try:
            return await self.generate_scene_video_with_ref(scene, None, style_prefix)
        except Exception as e:
            logger.warning(f"Veo without reference failed: {e}")

        # Fallback to Ken Burns
        return await self.generate_fallback_video(scene)

    async def generate_story_parallel(
        self,
        story_id: uuid.UUID,
        max_concurrent: int = 3,
    ) -> dict:
        """
        Generate all scenes for a story in parallel.

        Args:
            story_id: Story UUID
            max_concurrent: Max concurrent scene generations

        Returns:
            Generation results
        """
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise NotFoundError("Story", str(story_id))

        scenes = await self.scene_repo.get_by_story(story_id)
        if not scenes:
            raise NotFoundError("Scenes", f"No scenes for {story_id}")

        # Update story status
        story.status = "generating_assets"
        await self.story_repo.update(story)

        # Calculate pacing
        word_counts = [len(s.narration.split()) for s in scenes]
        timings = calculate_pacing(word_counts)

        # Update scene durations
        for scene, timing in zip(scenes, timings):
            scene.duration_seconds = timing.duration_seconds
            await self.scene_repo.update(scene)

        await self.session.commit()

        # Parallel generation with semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {"success": 0, "failed": 0, "fallback": 0}

        async def generate_one(s: Scene):
            async with semaphore:
                try:
                    # Generate audio
                    audio_path = await self._generate_audio(s, story.voice_id)
                    s.audio_path = audio_path

                    # Generate video with fallback
                    video_path = await self.generate_scene_with_fallback(s, story.style_prefix)
                    s.video_path = video_path

                    await self.session.commit()
                    results["success"] += 1

                except Exception as e:
                    logger.error(f"Scene {s.id} generation failed: {e}")
                    results["failed"] += 1

        # Run all generations
        await asyncio.gather(*[generate_one(s) for s in scenes])

        # Final status
        if results["failed"] == 0:
            story.status = "pending"  # Ready for stitching
        else:
            story.status = "failed" if results["success"] == 0 else "partial"
            story.error_message = f"{results['failed']} scenes failed"

        await self.story_repo.update(story)
        await self.session.commit()

        return results

    async def _generate_audio(
        self,
        scene: Scene,
        voice_id: Optional[str] = None,
    ) -> str:
        """Generate audio for scene."""
        output_dir = settings.media_dir / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"scene_{scene.id}.mp3"

        return await self.tts_client.generate_speech(
            text=scene.narration,
            output_path=str(output_path),
            voice=voice_id,
        )

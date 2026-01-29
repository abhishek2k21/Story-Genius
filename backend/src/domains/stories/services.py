"""
Story Service
Business logic for story generation with Gemini.
"""
import json
import uuid
from math import ceil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.vertex_client import get_vertex_client
from src.core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from src.core.logging import get_logger
from src.database.models import Scene, Story
from src.domains.stories.entities import (
    GeneratedScene,
    GeneratedScript,
    SceneResponse,
    StoryCreate,
    StoryGenerateRequest,
    StoryListResponse,
    StoryResponse,
    StoryUpdate,
    StoryWithScenes,
)
from src.domains.stories.repositories import SceneRepository, StoryRepository

logger = get_logger(__name__)

# Prompt template for Gemini
SCRIPT_GENERATION_PROMPT = """You are a professional short-form video scriptwriter. Generate a compelling video script based on the user's prompt.

USER PROMPT: {prompt}

TARGET DURATION: {target_duration} seconds
NUMBER OF SCENES: {num_scenes}

Generate a JSON response with the following structure:
{{
    "title": "Engaging title for the video",
    "scenes": [
        {{
            "scene_number": 1,
            "narration": "Voice-over text for this scene (2-3 sentences)",
            "visual_description": "Detailed visual description for video generation",
            "duration_seconds": 8.0
        }}
    ],
    "total_duration_seconds": 60.0
}}

Requirements:
- Each scene narration should be 2-3 concise sentences
- Visual descriptions should be cinematic and detailed
- Total duration should match the target
- Create smooth narrative flow between scenes
- Make the content engaging and retention-focused

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""


class StoryService:
    """Service for story business operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.story_repo = StoryRepository(session)
        self.scene_repo = SceneRepository(session)
        self.vertex_client = get_vertex_client()

    async def create_story(
        self,
        data: StoryCreate,
        user_id: str,
    ) -> StoryResponse:
        """Create a story manually (without AI generation)."""
        story = Story(
            project_id=data.project_id,
            title=data.title,
            prompt=data.prompt,
            style_prefix=data.style_prefix,
            voice_id=data.voice_id,
            status="pending",
        )

        story = await self.story_repo.create(story)
        logger.info(f"Created story {story.id}")

        return self._to_response(story, scene_count=0)

    async def generate_story(
        self,
        data: StoryGenerateRequest,
        user_id: str,
    ) -> StoryWithScenes:
        """
        Generate a complete story with scenes using Gemini.

        1. Create story record
        2. Call Gemini to generate script
        3. Parse into scenes
        4. Save scenes to database
        """
        # Create story
        story = Story(
            project_id=data.project_id,
            title="Generating...",
            prompt=data.prompt,
            style_prefix=data.style_prefix,
            voice_id=data.voice_id,
            status="generating_script",
        )
        story = await self.story_repo.create(story)

        try:
            # Generate script with Gemini
            generated = await self._generate_script(
                prompt=data.prompt,
                target_duration=data.target_duration_seconds,
                num_scenes=data.num_scenes,
            )

            # Update story with generated content
            story.title = generated.title
            story.script = json.dumps(
                [s.model_dump() for s in generated.scenes],
                indent=2,
            )
            story.duration_seconds = int(generated.total_duration_seconds)
            story.status = "pending"  # Ready for video generation

            # Create scenes
            scenes = []
            for gs in generated.scenes:
                scene = Scene(
                    story_id=story.id,
                    order=gs.scene_number - 1,
                    narration=gs.narration,
                    visual_prompt=gs.visual_description,
                    duration_seconds=gs.duration_seconds,
                )
                scenes.append(scene)

            await self.scene_repo.create_many(scenes)
            story = await self.story_repo.update(story)

            logger.info(f"Generated story {story.id} with {len(scenes)} scenes")

            return StoryWithScenes(
                **self._to_dict(story),
                scene_count=len(scenes),
                scenes=[self._scene_to_response(s) for s in scenes],
            )

        except Exception as e:
            # Mark story as failed
            story.status = "failed"
            story.error_message = str(e)[:500]
            await self.story_repo.update(story)

            logger.error(f"Story generation failed: {e}")
            raise

    async def _generate_script(
        self,
        prompt: str,
        target_duration: int,
        num_scenes: int,
    ) -> GeneratedScript:
        """Generate script using Gemini."""
        full_prompt = SCRIPT_GENERATION_PROMPT.format(
            prompt=prompt,
            target_duration=target_duration,
            num_scenes=num_scenes,
        )

        try:
            response = await self.vertex_client.generate_text(
                prompt=full_prompt,
                temperature=0.8,
                max_tokens=4096,
            )

            # Parse JSON response
            # Clean up response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            scenes = [
                GeneratedScene(
                    scene_number=s["scene_number"],
                    narration=s["narration"],
                    visual_description=s["visual_description"],
                    duration_seconds=s["duration_seconds"],
                )
                for s in data["scenes"]
            ]

            return GeneratedScript(
                title=data["title"],
                scenes=scenes,
                total_duration_seconds=data["total_duration_seconds"],
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise ExternalServiceError("Gemini", f"Invalid JSON response: {e}")

    async def get_story(
        self,
        story_id: uuid.UUID,
        user_id: str,
        include_scenes: bool = False,
    ) -> StoryResponse | StoryWithScenes:
        """Get a story by ID."""
        story = await self.story_repo.get_by_id(story_id, include_scenes)

        if not story:
            raise NotFoundError("Story", str(story_id))

        scene_count = await self.story_repo.get_scene_count(story_id)

        if include_scenes:
            scenes = [self._scene_to_response(s) for s in story.scenes]
            return StoryWithScenes(
                **self._to_dict(story),
                scene_count=scene_count,
                scenes=scenes,
            )

        return self._to_response(story, scene_count)

    async def list_stories(
        self,
        project_id: uuid.UUID,
        user_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
    ) -> StoryListResponse:
        """List stories for a project."""
        offset = (page - 1) * size

        stories = await self.story_repo.get_by_project(
            project_id=project_id,
            offset=offset,
            limit=size,
            status=status,
        )

        total = await self.story_repo.count_by_project(project_id, status)

        items = []
        for story in stories:
            scene_count = await self.story_repo.get_scene_count(story.id)
            items.append(self._to_response(story, scene_count))

        return StoryListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
        )

    async def update_story(
        self,
        story_id: uuid.UUID,
        user_id: str,
        data: StoryUpdate,
    ) -> StoryResponse:
        """Update a story."""
        story = await self.story_repo.get_by_id(story_id)

        if not story:
            raise NotFoundError("Story", str(story_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(story, field, value)

        story = await self.story_repo.update(story)
        scene_count = await self.story_repo.get_scene_count(story_id)

        return self._to_response(story, scene_count)

    async def delete_story(
        self,
        story_id: uuid.UUID,
        user_id: str,
    ) -> bool:
        """Delete a story and its scenes."""
        story = await self.story_repo.get_by_id(story_id)

        if not story:
            raise NotFoundError("Story", str(story_id))

        await self.story_repo.delete(story)
        logger.info(f"Deleted story {story_id}")

        return True

    async def get_scenes(
        self,
        story_id: uuid.UUID,
        user_id: str,
    ) -> list[SceneResponse]:
        """Get all scenes for a story."""
        scenes = await self.scene_repo.get_by_story(story_id)
        return [self._scene_to_response(s) for s in scenes]

    def _to_response(self, story: Story, scene_count: int) -> StoryResponse:
        """Convert story model to response."""
        return StoryResponse(
            **self._to_dict(story),
            scene_count=scene_count,
        )

    def _to_dict(self, story: Story) -> dict:
        """Convert story model to dict."""
        return {
            "id": story.id,
            "project_id": story.project_id,
            "title": story.title,
            "prompt": story.prompt,
            "script": story.script,
            "status": story.status,
            "error_message": story.error_message,
            "video_path": story.video_path,
            "thumbnail_path": story.thumbnail_path,
            "duration_seconds": story.duration_seconds,
            "style_prefix": story.style_prefix,
            "voice_id": story.voice_id,
            "quality_score": story.quality_score,
            "created_at": story.created_at,
            "updated_at": story.updated_at,
        }

    def _scene_to_response(self, scene: Scene) -> SceneResponse:
        """Convert scene model to response."""
        return SceneResponse(
            id=scene.id,
            story_id=scene.story_id,
            order=scene.order,
            narration=scene.narration,
            visual_prompt=scene.visual_prompt,
            audio_path=scene.audio_path,
            video_path=scene.video_path,
            image_path=scene.image_path,
            duration_seconds=scene.duration_seconds,
            created_at=scene.created_at,
        )

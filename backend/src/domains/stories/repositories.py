"""
Story Repository
Database operations for stories and scenes.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Scene, Story


class StoryRepository:
    """Repository for story database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, story: Story) -> Story:
        """Create a new story."""
        self.session.add(story)
        await self.session.flush()
        await self.session.refresh(story)
        return story

    async def get_by_id(
        self,
        story_id: uuid.UUID,
        include_scenes: bool = False,
    ) -> Optional[Story]:
        """Get a story by ID."""
        query = select(Story).where(Story.id == story_id)

        if include_scenes:
            query = query.options(selectinload(Story.scenes))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Sequence[Story]:
        """Get stories for a project."""
        query = select(Story).where(Story.project_id == project_id)

        if status:
            query = query.where(Story.status == status)

        query = query.order_by(Story.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_project(
        self,
        project_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> int:
        """Count stories for a project."""
        query = select(func.count(Story.id)).where(Story.project_id == project_id)

        if status:
            query = query.where(Story.status == status)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, story: Story) -> Story:
        """Update a story."""
        await self.session.flush()
        await self.session.refresh(story)
        return story

    async def delete(self, story: Story) -> bool:
        """Delete a story."""
        await self.session.delete(story)
        await self.session.flush()
        return True

    async def get_scene_count(self, story_id: uuid.UUID) -> int:
        """Get scene count for a story."""
        query = select(func.count(Scene.id)).where(Scene.story_id == story_id)
        result = await self.session.execute(query)
        return result.scalar() or 0


class SceneRepository:
    """Repository for scene database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, scene: Scene) -> Scene:
        """Create a new scene."""
        self.session.add(scene)
        await self.session.flush()
        await self.session.refresh(scene)
        return scene

    async def create_many(self, scenes: list[Scene]) -> list[Scene]:
        """Create multiple scenes."""
        self.session.add_all(scenes)
        await self.session.flush()
        for scene in scenes:
            await self.session.refresh(scene)
        return scenes

    async def get_by_story(self, story_id: uuid.UUID) -> Sequence[Scene]:
        """Get all scenes for a story."""
        query = (
            select(Scene)
            .where(Scene.story_id == story_id)
            .order_by(Scene.order)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, scene_id: uuid.UUID) -> Optional[Scene]:
        """Get a scene by ID."""
        result = await self.session.execute(
            select(Scene).where(Scene.id == scene_id)
        )
        return result.scalar_one_or_none()

    async def update(self, scene: Scene) -> Scene:
        """Update a scene."""
        await self.session.flush()
        await self.session.refresh(scene)
        return scene

    async def delete(self, scene: Scene) -> bool:
        """Delete a scene."""
        await self.session.delete(scene)
        await self.session.flush()
        return True

    async def delete_by_story(self, story_id: uuid.UUID) -> int:
        """Delete all scenes for a story."""
        scenes = await self.get_by_story(story_id)
        for scene in scenes:
            await self.session.delete(scene)
        await self.session.flush()
        return len(scenes)

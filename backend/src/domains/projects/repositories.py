"""
Project Repository
Database operations for projects.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Project, Story


class ProjectRepository:
    """Repository for project database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project: Project) -> Project:
        """Create a new project."""
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        include_stories: bool = False,
    ) -> Optional[Project]:
        """Get a project by ID."""
        query = select(Project).where(Project.id == project_id)

        if include_stories:
            query = query.options(selectinload(Project.stories))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Sequence[Project]:
        """Get projects for a user with pagination."""
        query = select(Project).where(Project.user_id == user_id)

        if status:
            query = query.where(Project.status == status)

        query = query.order_by(Project.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count projects for a user."""
        query = select(func.count(Project.id)).where(Project.user_id == user_id)

        if status:
            query = query.where(Project.status == status)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, project: Project) -> Project:
        """Update a project."""
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> bool:
        """Delete a project."""
        await self.session.delete(project)
        await self.session.flush()
        return True

    async def get_story_count(self, project_id: uuid.UUID) -> int:
        """Get story count for a project."""
        query = select(func.count(Story.id)).where(Story.project_id == project_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

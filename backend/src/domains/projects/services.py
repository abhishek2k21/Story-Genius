"""
Project Service
Business logic for project operations.
"""
import uuid
from math import ceil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import get_logger
from src.database.models import Project
from src.domains.projects.entities import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStories,
    StoryBrief,
)
from src.domains.projects.repositories import ProjectRepository

logger = get_logger(__name__)


class ProjectService:
    """Service for project business operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProjectRepository(session)

    async def create_project(
        self,
        data: ProjectCreate,
        user_id: str,
    ) -> ProjectResponse:
        """
        Create a new project.

        Args:
            data: Project creation data
            user_id: Owner user ID

        Returns:
            Created project
        """
        project = Project(
            name=data.name,
            description=data.description,
            user_id=user_id,
            default_voice=data.default_voice,
            default_style=data.default_style,
            status="draft",
        )

        project = await self.repository.create(project)
        logger.info(f"Created project {project.id} for user {user_id}")

        return ProjectResponse(
            **self._to_dict(project),
            story_count=0,
        )

    async def get_project(
        self,
        project_id: uuid.UUID,
        user_id: str,
        include_stories: bool = False,
    ) -> ProjectResponse | ProjectWithStories:
        """
        Get a project by ID.

        Args:
            project_id: Project UUID
            user_id: Owner user ID (for authorization)
            include_stories: Whether to include stories

        Returns:
            Project data

        Raises:
            NotFoundError: If project not found or not owned by user
        """
        project = await self.repository.get_by_id(project_id, include_stories)

        if not project or project.user_id != user_id:
            raise NotFoundError("Project", str(project_id))

        story_count = await self.repository.get_story_count(project_id)

        if include_stories:
            stories = [
                StoryBrief(
                    id=s.id,
                    title=s.title,
                    status=s.status,
                    created_at=s.created_at,
                )
                for s in project.stories
            ]
            return ProjectWithStories(
                **self._to_dict(project),
                story_count=story_count,
                stories=stories,
            )

        return ProjectResponse(
            **self._to_dict(project),
            story_count=story_count,
        )

    async def list_projects(
        self,
        user_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
    ) -> ProjectListResponse:
        """
        List projects for a user with pagination.

        Args:
            user_id: Owner user ID
            page: Page number (1-indexed)
            size: Items per page
            status: Optional status filter

        Returns:
            Paginated project list
        """
        offset = (page - 1) * size

        projects = await self.repository.get_by_user(
            user_id=user_id,
            offset=offset,
            limit=size,
            status=status,
        )

        total = await self.repository.count_by_user(user_id, status)
        pages = ceil(total / size) if size > 0 else 0

        items = []
        for project in projects:
            story_count = await self.repository.get_story_count(project.id)
            items.append(ProjectResponse(
                **self._to_dict(project),
                story_count=story_count,
            ))

        return ProjectListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_project(
        self,
        project_id: uuid.UUID,
        user_id: str,
        data: ProjectUpdate,
    ) -> ProjectResponse:
        """
        Update a project.

        Args:
            project_id: Project UUID
            user_id: Owner user ID
            data: Update data

        Returns:
            Updated project
        """
        project = await self.repository.get_by_id(project_id)

        if not project or project.user_id != user_id:
            raise NotFoundError("Project", str(project_id))

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(project, field, value)

        project = await self.repository.update(project)
        story_count = await self.repository.get_story_count(project_id)

        logger.info(f"Updated project {project_id}")

        return ProjectResponse(
            **self._to_dict(project),
            story_count=story_count,
        )

    async def delete_project(
        self,
        project_id: uuid.UUID,
        user_id: str,
    ) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project UUID
            user_id: Owner user ID

        Returns:
            True if deleted
        """
        project = await self.repository.get_by_id(project_id)

        if not project or project.user_id != user_id:
            raise NotFoundError("Project", str(project_id))

        await self.repository.delete(project)
        logger.info(f"Deleted project {project_id}")

        return True

    def _to_dict(self, project: Project) -> dict:
        """Convert project model to dict."""
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "user_id": project.user_id,
            "default_voice": project.default_voice,
            "default_style": project.default_style,
            "thumbnail_path": project.thumbnail_path,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

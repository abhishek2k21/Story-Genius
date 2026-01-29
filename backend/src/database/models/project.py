"""
Project Model
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models.story import Story


class ProjectStatus(str, Enum):
    """Project status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base, UUIDMixin, TimestampMixin):
    """
    Project model - represents a video generation project.

    A project contains multiple stories and configuration.
    """
    __tablename__ = "projects"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ProjectStatus.DRAFT.value,
        nullable=False,
    )

    # Owner
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Configuration
    default_voice: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Media paths
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    stories: Mapped[list["Story"]] = relationship(
        "Story",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} ({self.id})>"

"""
Story and Scene Models
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.database.models.project import Project


class StoryStatus(str, Enum):
    """Story status enum."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Story(Base, UUIDMixin, TimestampMixin):
    """
    Story model - represents a generated video story.

    A story contains multiple scenes and metadata.
    """
    __tablename__ = "stories"

    # Relationship
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=StoryStatus.PENDING.value,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated output
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    style_prefix: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    voice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Quality scores
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="stories")
    scenes: Mapped[list["Scene"]] = relationship(
        "Scene",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="Scene.order",
    )

    def __repr__(self) -> str:
        return f"<Story {self.title[:30]} ({self.status})>"


class Scene(Base, UUIDMixin, TimestampMixin):
    """
    Scene model - represents a single scene within a story.
    """
    __tablename__ = "scenes"

    # Relationship
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Order
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Content
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    visual_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Generated paths
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timing
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationship
    story: Mapped["Story"] = relationship("Story", back_populates="scenes")

    def __repr__(self) -> str:
        return f"<Scene {self.order} of Story {self.story_id}>"

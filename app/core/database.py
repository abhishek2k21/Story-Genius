"""
Database Module for the Creative AI Shorts Platform.
Uses SQLAlchemy with SQLite (upgradeable to PostgreSQL).
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from app.core.config import settings
from app.core.models import JobStatus, Platform, ScenePurpose

# Create engine and session
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============== Database Models ==============

class DBJob(Base):
    """SQLAlchemy model for jobs table."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default=JobStatus.QUEUED.value)
    platform = Column(String, default=Platform.YOUTUBE_SHORTS.value)
    audience = Column(String, default="kids_india")
    duration = Column(Integer, default=30)
    genre = Column(String, default="kids")
    language = Column(String, default="en-hi")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Results
    story_id = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Critic scores
    hook_score = Column(Float, nullable=True)
    pacing_score = Column(Float, nullable=True)
    loop_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    stories = relationship("DBStory", back_populates="job")


class DBStory(Base):
    """SQLAlchemy model for stories table."""
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    total_duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("DBJob", back_populates="stories")
    scenes = relationship("DBScene", back_populates="story")


class DBScene(Base):
    """SQLAlchemy model for story_scenes table."""
    __tablename__ = "story_scenes"
    
    id = Column(String, primary_key=True, index=True)
    story_id = Column(String, ForeignKey("stories.id"))
    scene_order = Column(Integer)
    start_sec = Column(Integer)
    end_sec = Column(Integer)
    purpose = Column(String)
    narration_text = Column(Text)
    visual_prompt = Column(Text)
    
    # Media paths
    audio_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    
    # Relationships
    story = relationship("DBStory", back_populates="scenes")


class DBImage(Base):
    """SQLAlchemy model for images table."""
    __tablename__ = "images"
    
    id = Column(String, primary_key=True, index=True)
    scene_id = Column(String, ForeignKey("story_scenes.id"))
    storage_url = Column(String)
    style = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBAudioTrack(Base):
    """SQLAlchemy model for audio_tracks table."""
    __tablename__ = "audio_tracks"
    
    id = Column(String, primary_key=True, index=True)
    scene_id = Column(String, ForeignKey("story_scenes.id"))
    storage_url = Column(String)
    voice_id = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBVideo(Base):
    """SQLAlchemy model for videos table."""
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    storage_url = Column(String)
    duration = Column(Integer, nullable=True)
    resolution = Column(String, default="1080x1920")
    created_at = Column(DateTime, default=datetime.utcnow)


class DBCriticScore(Base):
    """SQLAlchemy model for critic_scores table."""
    __tablename__ = "critic_scores"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    platform = Column(String)
    total_score = Column(Float)
    hook_score = Column(Float)
    pacing_score = Column(Float)
    loop_score = Column(Float)
    verdict = Column(String)  # accept or retry
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============== Database Operations ==============

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session (dependency for FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a new database session (for non-FastAPI use)."""
    return SessionLocal()

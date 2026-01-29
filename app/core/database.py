"""
Database Module for the Creative AI Shorts Platform.
Uses SQLAlchemy with SQLite (upgradeable to PostgreSQL).
"""
from datetime import datetime
from typing import Optional, List, Generator
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base

from app.core.config import settings
from app.core.models import JobStatus, Platform
# Note: ScenePurpose used in DBScene but not imported in original, fixing import if needed or ensuring generic string

# Create engine with pooling configuration
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_size=settings.DB_POOL_SIZE if "sqlite" not in settings.DATABASE_URL else None,
    max_overflow=settings.DB_MAX_OVERFLOW if "sqlite" not in settings.DATABASE_URL else None,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    # SQLite doesn't support pool_size/max_overflow with StaticPool (default for memory) or NullPool/QueuePool with check_same_thread=False
    # However, for file-based SQLite, QueuePool is used but single-threaded access is preferred.
    # We apply pooling params only if NOT sqlite or if we want to force it.
    # For simplicity/safety with SQLite, we often omit pool_size/max_overflow to let SQLAlchemy handle defaults or use NullPool.
    # But since user wants "Connection Pooling", we'll apply what we can. 
    # SQLAlchemy ignores pool_size for SQLite's default SingletonThreadPool/NullPool depending on URL.
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



class DBUser(Base):
    """SQLAlchemy model for users table."""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    status = Column(String, default="active")
    role = Column(String, default="creator")
    email_verified = Column(Integer, default=0)  # Boolean as 0/1 for SQLite compat
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, default="{}")  # Store metadata as JSON string


class DBAPIKey(Base):
    """SQLAlchemy model for api_keys table."""
    __tablename__ = "api_keys"
    
    key_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    key_hash = Column(String, unique=True, index=True)
    key_prefix = Column(String)
    name = Column(String)
    status = Column(String, default="active")
    permissions = Column(Text, default="read,write")  # CSV string
    rate_limit = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)


# ============== Database Operations ==============


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session (dependency for FastAPI).
    Ensures safe session handling.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a new database session (for non-FastAPI use)."""
    return SessionLocal()

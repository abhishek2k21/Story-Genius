"""
Application Configuration Module
Centralized settings using pydantic-settings for environment variable support.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Info
    APP_NAME: str = "Creative AI Shorts Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./shorts_platform.db"
    
    # Output Paths
    OUTPUT_DIR: Path = Path(".story_assets")
    MEDIA_DIR: Path = Path(".story_assets/media")
    
    # LLM Settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    VERTEX_AI_LOCATION: str = "us-central1"
    
    # TTS Settings
    DEFAULT_VOICE: str = "en-US-AnaNeural"
    
    # Shorts Platform Settings
    DEFAULT_PLATFORM: str = "youtube_shorts"
    DEFAULT_DURATION: int = 30
    MIN_DURATION: int = 25
    MAX_DURATION: int = 35
    HOOK_WINDOW_SECONDS: float = 2.0
    
    # Critic Settings
    CRITIC_RETRY_THRESHOLD: float = 0.6
    MAX_RETRIES: int = 2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure output directories exist
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

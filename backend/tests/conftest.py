"""
Pytest Configuration
Test fixtures and database setup.
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.settings import settings
from src.database.models import Base
from src.database.session import get_session
from src.main import app

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with injected DB session."""

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Create synchronous test client."""
    with TestClient(app) as c:
        yield c


# ========================
# Test Data Fixtures
# ========================

@pytest.fixture
def sample_project_data() -> dict:
    """Sample project creation data."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "default_voice": "nova",
        "default_style": "cinematic",
    }


@pytest.fixture
def sample_story_data() -> dict:
    """Sample story generation data."""
    return {
        "prompt": "Create a 30-second video about artificial intelligence",
        "style_prefix": "cinematic, professional",
        "voice_id": "nova",
        "target_duration_seconds": 30,
        "num_scenes": 3,
    }


@pytest.fixture
def sample_video_job_data() -> dict:
    """Sample video job data."""
    return {
        "generate_audio": True,
        "generate_video": True,
        "stitch_final": True,
    }


# ========================
# Mock Fixtures
# ========================

@pytest.fixture
def mock_gemini_response() -> dict:
    """Mock Gemini API response."""
    return {
        "title": "Test Story",
        "scenes": [
            {
                "order": 1,
                "narration": "This is the first scene.",
                "visual_prompt": "A beautiful sunrise over mountains",
                "duration_seconds": 10,
            },
            {
                "order": 2,
                "narration": "This is the second scene.",
                "visual_prompt": "Birds flying in the sky",
                "duration_seconds": 10,
            },
        ],
        "total_duration_seconds": 20,
    }


@pytest.fixture
def mock_vertex_client(mocker):
    """Mock Vertex AI client."""
    mock = mocker.patch("src.clients.vertex_client.get_vertex_client")
    mock.return_value.generate_text.return_value = asyncio.coroutine(lambda: "{}")()
    mock.return_value.generate_video.return_value = asyncio.coroutine(lambda: "/tmp/video.mp4")()
    mock.return_value.generate_image.return_value = asyncio.coroutine(lambda: "/tmp/image.png")()
    return mock


@pytest.fixture
def mock_tts_client(mocker):
    """Mock TTS client."""
    mock = mocker.patch("src.clients.elevenlabs_client.get_elevenlabs_client")
    mock.return_value.generate_speech.return_value = asyncio.coroutine(lambda: "/tmp/audio.mp3")()
    return mock

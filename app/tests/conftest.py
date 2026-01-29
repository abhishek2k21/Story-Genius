"""
Pytest Configuration and Shared Fixtures
"""
import pytest
import os
from datetime import datetime
from typing import Generator
from unittest.mock import Mock, patch

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEBUG"] = "true"


# ==================== Database Fixtures ====================

@pytest.fixture
def test_db():
    """In-memory SQLite database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


# ==================== User Fixtures ====================

@pytest.fixture
def test_user():
    """Test user data"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "plan": "pro",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def test_users():
    """Multiple test users"""
    return [
        {"user_id": f"user_{i}", "email": f"user{i}@example.com", "plan": "free"}
        for i in range(5)
    ]


# ==================== Batch Fixtures ====================

@pytest.fixture
def test_batch():
    """Test batch configuration"""
    from app.batch.models import Batch, BatchConfig
    
    config = BatchConfig(
        platform="youtube_shorts",
        duration=60,
        audience="teens",
        genre="comedy"
    )
    
    return Batch(
        name="Test Batch",
        user_id="test_user_123",
        config=config
    )


@pytest.fixture
def test_batch_items():
    """Test batch items"""
    from app.batch.models import BatchItem
    
    return [
        BatchItem(order=i, content=f"Test content {i}")
        for i in range(5)
    ]


# ==================== Prompt Fixtures ====================

@pytest.fixture
def test_prompt():
    """Test prompt"""
    from app.core.prompts.base_prompts import Prompt, PromptType
    
    return Prompt(
        id="test_prompt",
        name="Test Prompt",
        type=PromptType.HOOK,
        template="Generate a hook for {{platform}} about {{topic}}",
        version="1.0",
        variables=["platform", "topic"]
    )


@pytest.fixture
def test_prompt_variables():
    """Test prompt variables"""
    return {
        "platform": "youtube_shorts",
        "topic": "artificial intelligence",
        "audience": "general",
        "tone": "casual",
        "duration": 60
    }


# ==================== LLM Mock Fixtures ====================

@pytest.fixture
def mock_vertex_ai_response():
    """Mock Vertex AI response"""
    return {
        "hook": "Did you know AI can now...?",
        "main_content": "Artificial intelligence has revolutionized...",
        "call_to_action": "Follow for more AI facts!"
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    mock = Mock()
    mock.generate.return_value = '{"hook": "Test hook", "content": "Test content"}'
    return mock


@pytest.fixture
def mock_veo_response():
    """Mock Veo video generation response"""
    return {
        "video_id": "veo_12345",
        "status": "completed",
        "output_uri": "gs://bucket/video.mp4"
    }


# ==================== Cache Fixtures ====================

@pytest.fixture
def test_cache():
    """Test cache instance"""
    from app.engines.llm_cache import LLMCache
    
    cache = LLMCache()
    yield cache
    cache.clear()


# ==================== Config Fixtures ====================

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "APP_NAME": "Story-Genius Test",
        "APP_VERSION": "1.0.0-test",
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG"
    }


# ==================== Request/Response Fixtures ====================

@pytest.fixture
def test_video_request():
    """Test video generation request"""
    return {
        "prompt": "Create a video about space exploration",
        "platform": "youtube_shorts",
        "audience": "general",
        "duration": 60
    }


@pytest.fixture
def mock_fastapi_client():
    """Mock FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.api.main import app
    
    return TestClient(app)


# ==================== Time Fixtures ====================

@pytest.fixture
def freeze_time():
    """Freeze time for testing"""
    frozen_time = datetime(2026, 1, 28, 12, 0, 0)
    
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = frozen_time
        yield frozen_time


# ==================== Async Fixtures ====================

@pytest.fixture
async def async_test_client():
    """Async test client"""
    from httpx import AsyncClient
    from app.api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ==================== Cleanup Fixtures ====================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    yield
    
    # Reset lock manager
    from app.scheduling.lock_manager import lock_manager
    lock_manager._locks.clear()
    
    # Reset cache
    from app.engines.llm_cache import llm_cache
    llm_cache.clear()


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

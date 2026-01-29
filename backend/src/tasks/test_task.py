"""
Test Task - Verify Celery is working
"""
from src.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="test_task")
def test_task(self, message: str = "Hello") -> dict:
    """
    Simple test task to verify Celery functionality.

    Args:
        message: Test message to echo

    Returns:
        Dict with task info
    """
    return {
        "task_id": self.request.id,
        "message": message,
        "status": "completed",
    }


@celery_app.task(bind=True, name="ping")
def ping(self) -> str:
    """Simple ping task."""
    return "pong"

"""
Celery Application Configuration
"""
from celery import Celery

from src.core.settings import settings

celery_app = Celery(
    "story_genius",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks.test_task"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # Soft limit 55 min
    worker_prefetch_multiplier=1,  # One task at a time
    task_acks_late=True,  # Ack after completion
    task_reject_on_worker_lost=True,
)

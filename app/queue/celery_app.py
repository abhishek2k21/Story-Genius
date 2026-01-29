"""
Celery Application Configuration
Configures Celery for async task processing with Redis broker.
"""
from celery import Celery
from kombu import Queue
import os

# Celery app instance
celery_app = Celery(
    'story_genius',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.queue.tasks.generation.*': {'queue': 'generation'},
        'app.queue.tasks.media.*': {'queue': 'media'},
        'app.queue.tasks.processing.*': {'queue': 'batch'},
    },
    
    # Queue definitions
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('generation', routing_key='generation', priority=10),
        Queue('media', routing_key='media', priority=5),
        Queue('batch', routing_key='batch', priority=3),
    ),
    
    # Time limits
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit
    
    # Concurrency
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={'master_name': 'mymaster'},
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Retry settings (default)
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'cleanup-old-results': {
            'task': 'app.queue.tasks.processing.cleanup_old_results',
            'schedule': 3600.0,  # Every hour
        },
    },
)

# Task discovery
celery_app.autodiscover_tasks([
    'app.queue.tasks.generation',
    'app.queue.tasks.media',
    'app.queue.tasks.processing',
])


if __name__ == '__main__':
    celery_app.start()

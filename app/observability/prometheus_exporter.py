"""
Prometheus Metrics Exporter
Exposes application metrics for Prometheus scraping.
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# ==================== Counters ====================

# LLM Requests
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['model', 'status']  # Labels: model name, success/failure
)

# Cache Operations
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Job Operations
jobs_created_total = Counter(
    'jobs_created_total',
    'Total jobs created',
    ['job_type']
)

jobs_completed_total = Counter(
    'jobs_completed_total',
    'Total jobs completed',
    ['job_type', 'status']  # success/failed
)

# Batch Operations
batches_created_total = Counter(
    'batches_created_total',
    'Total batches created'
)

batches_completed_total = Counter(
    'batches_completed_total',
    'Total batches completed',
    ['status']  # completed/partial/failed
)


# ==================== Gauges ====================

# Active Resources
active_jobs = Gauge(
    'active_jobs',
    'Number of currently active jobs'
)

cache_entries = Gauge(
    'cache_entries',
    'Number of entries in cache'
)

active_users = Gauge(
    'active_users',
    'Number of active users in last hour'
)

# Queue Metrics (Celery)
celery_queue_depth = Gauge(
    'celery_queue_depth',
    'Number of tasks in queue',
    ['queue']
)

celery_active_workers = Gauge(
    'celery_active_workers',
    'Number of active Celery workers'
)


# ==================== Histograms ====================

# Job Duration
job_duration_seconds = Histogram(
    'job_duration_seconds',
    'Job execution duration in seconds',
    ['job_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]  # 1s to 10min
)

# LLM Latency
llm_latency_seconds = Histogram(
    'llm_latency_seconds',
    'LLM API call latency in seconds',
    ['model'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]  # 100ms to 30s
)

# Batch Processing Time
batch_processing_seconds = Histogram(
    'batch_processing_seconds',
    'Batch processing time in seconds',
    buckets=[10, 30, 60, 120, 300, 600, 1200]  # 10s to 20min
)

# Token Usage
tokens_used = Histogram(
    'tokens_used',
    'Tokens used per LLM request',
    ['model'],
    buckets=[100, 500, 1000, 2000, 4000, 8000, 16000]
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks processed',
    ['queue', 'task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

celery_task_retries = Counter(
    'celery_task_retries_total',
    'Total task retries',
    ['task_name', 'retry_count']
)


# ==================== Helper Functions ====================

def track_llm_request(model: str, status: str = "success"):
    """Track LLM request"""
    llm_requests_total.labels(model=model, status=status).inc()


def track_cache_hit():
    """Track cache hit"""
    cache_hits_total.inc()


def track_cache_miss():
    """Track cache miss"""
    cache_misses_total.inc()


def track_job_created(job_type: str):
    """Track job creation"""
    jobs_created_total.labels(job_type=job_type).inc()
    active_jobs.inc()


def track_job_completed(job_type: str, status: str, duration: float):
    """Track job completion"""
    jobs_completed_total.labels(job_type=job_type, status=status).inc()
    job_duration_seconds.labels(job_type=job_type).observe(duration)
    active_jobs.dec()


def track_llm_latency(model: str, latency: float, tokens: Optional[int] = None):
    """Track LLM call latency and token usage"""
    llm_latency_seconds.labels(model=model).observe(latency)
    if tokens:
        tokens_used.labels(model=model).observe(tokens)


def track_batch_created():
    """Track batch creation"""
    batches_created_total.inc()


def track_batch_completed(status: str, duration: float):
    """Track batch completion"""
    batches_completed_total.labels(status=status).inc()
    batch_processing_seconds.observe(duration)


def update_cache_size(size: int):
    """Update cache size gauge"""
    cache_entries.set(size)


def update_active_users(count: int):
    """Update active users gauge"""
    active_users.set(count)


# Celery Helper Functions

def track_celery_task_start(task_name: str, queue: str = "default"):
    """Track Celery task start"""
    celery_tasks_total.labels(queue=queue, task_name=task_name, status="started").inc()


def track_celery_task_complete(task_name: str, duration: float, queue: str = "default"):
    """Track Celery task completion"""
    celery_tasks_total.labels(queue=queue, task_name=task_name, status="completed").inc()
    celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def track_celery_task_failure(task_name: str, queue: str = "default"):
    """Track Celery task failure"""
    celery_tasks_total.labels(queue=queue, task_name=task_name, status="failed").inc()


def track_celery_task_retry(task_name: str, retry_count: int):
    """Track Celery task retry"""
    celery_task_retries.labels(task_name=task_name, retry_count=str(retry_count)).inc()


def update_celery_queue_depth(queue: str, depth: int):
    """Update Celery queue depth"""
    celery_queue_depth.labels(queue=queue).set(depth)


def update_celery_workers(count: int):
    """Update active Celery workers count"""
    celery_active_workers.set(count)


# ==================== Metrics Endpoint ====================

def get_metrics() -> Response:
    """
    Generate Prometheus metrics response.
    Use as FastAPI route handler.
    """
    metrics_output = generate_latest()
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


# Log metrics initialization
logger.info("Prometheus metrics initialized")

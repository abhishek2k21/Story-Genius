"""
Health Check Endpoints
"""
from fastapi import APIRouter

from src.core.dependencies import CurrentSettings, DbSession
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(settings: CurrentSettings) -> dict:
    """Basic health check."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/status")
async def detailed_status(
    settings: CurrentSettings,
    db: DbSession,
) -> dict:
    """
    Detailed status check including all dependencies.
    """
    from sqlalchemy import text

    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown",
    }

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:50]}"
        logger.error(f"Database health check failed: {e}")

    # Redis check
    try:
        import redis.asyncio as redis

        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)[:50]}"
        logger.warning(f"Redis health check failed: {e}")

    # Celery check
    try:
        from src.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect()
        active = inspect.active()
        if active:
            checks["celery"] = f"healthy ({len(active)} workers)"
        else:
            checks["celery"] = "no workers"
    except Exception as e:
        checks["celery"] = f"unavailable: {str(e)[:50]}"
        logger.warning(f"Celery health check failed: {e}")

    # Overall status
    critical = ["api", "database"]
    all_critical_healthy = all(checks[k] == "healthy" for k in critical)
    overall = "healthy" if all_critical_healthy else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "environment": settings.environment,
        "version": settings.app_version,
    }


@router.post("/tasks/test")
async def trigger_test_task() -> dict:
    """Trigger a test Celery task."""
    from src.tasks.test_task import test_task

    result = test_task.delay("Hello from API")
    return {
        "task_id": result.id,
        "status": "queued",
    }

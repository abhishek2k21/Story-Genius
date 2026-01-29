"""
Story-Genius Backend - FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core import get_logger, settings
from src.core.exceptions import StoryGeniusError
from src.database import async_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    settings.ensure_dirs()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(StoryGeniusError)
async def story_genius_exception_handler(
    request: Request,
    exc: StoryGeniusError,
) -> JSONResponse:
    """Handle custom exceptions."""
    logger.error(f"{exc.code}: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


# Health endpoints
@app.get("/health")
async def health() -> dict:
    """Basic health check."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/api/v1/health")
async def health_v1() -> dict:
    """API v1 health check with dependencies."""
    from src.database import async_session_factory

    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        logger.error(f"Redis health check failed: {e}")

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks, "version": settings.app_version}


@app.get("/api/v1/status")
async def status() -> dict:
    """Status endpoint with Celery worker info."""
    from src.tasks.celery_app import celery_app

    try:
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}
        workers = list(active.keys())
    except Exception:
        workers = []

    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "celery_workers": workers,
    }

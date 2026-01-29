"""
Story-Genius Backend - FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core import get_logger, settings
from src.core.middleware import RequestLoggingMiddleware, setup_exception_handlers
from src.core.rate_limit import RateLimitMiddleware
from src.core.validation import InputValidationMiddleware
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

# Security Middleware (order matters: first added = last executed)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
setup_exception_handlers(app)

# API Routes
app.include_router(api_router)


# Root health check (for container/load balancer)
@app.get("/health")
async def health() -> dict:
    """Basic health check."""
    return {"status": "healthy", "version": settings.app_version}


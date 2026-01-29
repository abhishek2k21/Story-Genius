"""
API v1 Router
Main router that includes all v1 endpoints.
"""
from fastapi import APIRouter

from src.api.v1.endpoints import health, projects
from src.domains.stories.routers import router as stories_router
from src.domains.video_generation.routers import router as video_router

api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(stories_router, prefix="/stories", tags=["Stories"])
api_router.include_router(video_router, prefix="/video", tags=["Video Generation"])

"""
API v1 Router
Main router that includes all v1 endpoints.
"""
from fastapi import APIRouter

from src.api.v1.endpoints import health, projects

api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

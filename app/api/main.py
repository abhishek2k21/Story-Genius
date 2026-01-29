"""
FastAPI Application Entry Point
Creative AI Shorts & Reels Platform
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pathlib import Path

from app.api.routes import router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import get_logger
from app.core.exceptions import CustomException
from app.api.middleware import RequestContextMiddleware, GlobalExceptionMiddleware

logger = get_logger(__name__)

# Initialize FastAPI app with comprehensive metadata
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Story-Genius API

AI-powered short-form video generation platform for YouTube Shorts, Instagram Reels, and TikTok.

### Features
* 🎬 **AI Video Generation** - Create videos from text prompts
* 📊 **Batch Processing** - Generate multiple videos efficiently
* 🎨 **Multi-Platform** - Support for all major short-form platforms
* 🔒 **Secure** - JWT authentication with token refresh
* ⚡ **Rate Limited** - Fair usage with tier-based quotas

### Authentication
All endpoints require Bearer token authentication except `/auth/login` and `/auth/register`.

### Rate Limits
- **Free**: 100 requests/hour, 10 videos/month
- **Pro**: 300 requests/hour, 100 videos/month
- **Enterprise**: 1000 requests/hour, unlimited videos

### Support
For issues or questions, contact support@story-genius.ai
    """.strip(),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "videos", "description": "Video generation operations"},
        {"name": "batches", "description": "Batch processing"},
        {"name": "analytics", "description": "Analytics and reporting"},
        {"name": "health", "description": "System health checks"},
    ]
)

# Exception Handlers
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

# Middleware
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(RequestContextMiddleware)

# CORS middleware - Environment-specific allowed origins
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alt dev server
]

# Add production origins from environment
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)
# Include Week 18 Creator Routes
from app.api.creator_routes import router as creator_router
app.include_router(creator_router)

from app.api.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/v1")

# Include Auth Routes
from app.api.auth_routes import router as auth_router
app.include_router(auth_router)

# Include Video Format Routes (Week 23)
from app.api.video_routes import router as video_router
app.include_router(video_router)

# Include Batch Generation Routes (Week 24)
from app.api.batch_routes import router as batch_router
app.include_router(batch_router)

# Include Template Routes (Week 25)
from app.api.template_routes import router as template_router
app.include_router(template_router)

# Include Admin Routes (Week 26 - Reliability)
from app.api.admin_routes import router as admin_router
app.include_router(admin_router)

# Include Engine Routes (Week 27)
from app.api.engine_routes import router as engine_router
app.include_router(engine_router)

# Include Text Overlay Routes (Week 28)
from app.api.text_routes import router as text_router
app.include_router(text_router)

# Include Pacing Routes (Week 29)
from app.api.pacing_routes import router as pacing_router
app.include_router(pacing_router)

# Include Thumbnail Routes (Week 30)
from app.api.thumbnail_routes import router as thumbnail_router
app.include_router(thumbnail_router)

# Include Observability Routes (Week 31)
from app.api.observability_routes import router as observability_router
app.include_router(observability_router)

# Include Auth Routes (Week 32)
from app.api.auth_routes import router as auth_router
app.include_router(auth_router)

# Include Asset Routes (Week 33)
from app.api.asset_routes import router as asset_router
app.include_router(asset_router)

# Include Project Organization Routes (Week 34)
from app.api.project_org_routes import router as project_org_router
app.include_router(project_org_router)

# Include Variation Routes (Week 35)
from app.api.variation_routes import router as variation_router
app.include_router(variation_router)

# Include Caption Routes (Week 36)
from app.api.caption_routes import router as caption_router
app.include_router(caption_router)

# Include Schedule Routes (Week 37)
from app.api.schedule_routes import router as schedule_router
app.include_router(schedule_router)

# Include Export Routes (Week 38 - FINAL)
from app.api.export_routes import router as export_router
app.include_router(export_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")


@app.get("/")
async def root():
    """Root endpoint - serve frontend or API info."""
    # Serve frontend if available
    frontend_index = Path(__file__).parent.parent.parent / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    # Fallback to API info
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


# Serve frontend static files (production build)
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    # SPA catch-all: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for all non-API routes."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

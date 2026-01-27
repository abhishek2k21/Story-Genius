"""
FastAPI Application Entry Point
Creative AI Shorts & Reels Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.routes import router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered short-form video generation platform for YouTube Shorts, Instagram Reels, and TikTok.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "https://story-genius.vercel.app",
        "*" # Keep wildcard for development ease if needed, but above are the target ones
    ],
    allow_credentials=True,
    allow_methods=["*"],
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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")


@app.get("/")
async def root():
    """Root endpoint."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

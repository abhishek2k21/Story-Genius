from fastapi import APIRouter, Depends
from app.core.database import get_db
from datetime import datetime, timedelta

router = APIRouter(tags=["analytics"])

@router.get("/analytics/overview")
async def get_analytics_overview():
    """Get high-level analytics metrics"""
    # Mock data for now since we don't have enough real data in the db yet
    # In a real scenario, this would allow SQL queries as planned
    return {
        "total_videos": 12,
        "avg_duration": 45.5,
        "total_views": 15420,
        "avg_retention": 68.5,
        "period": "last_30_days"
    }

@router.get("/analytics/top-videos")
async def get_top_videos(limit: int = 10):
    """Get top performing videos"""
    # Mock data matching the frontend interface
    return {
        "videos": [
            {
                "id": "1",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "video_url": "#",
                "views": 4500,
                "retention": 72.5,
                "engagement": 8.4,
                "title": "Why coffee makes you productive",
                "platform": "youtube_shorts",
                "likes": 320,
                "comments": 15,
                "avg_retention_percent": 0.725,
                "retention_at_3s": 0.85
            },
            {
                "id": "2",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "video_url": "#",
                "views": 3800,
                "retention": 65.0,
                "engagement": 6.2,
                "title": "Space facts",
                "platform": "tiktok",
                "likes": 410,
                "comments": 23,
                "avg_retention_percent": 0.65,
                "retention_at_3s": 0.90
            }
        ]
    }

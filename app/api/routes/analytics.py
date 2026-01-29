"""
Analytics API Routes
Endpoints for analytics dashboard and reporting.
"""
from fastapi import APIRouter, HTTPException, Response
from typing import Optional

from app.analytics import analytics_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/metrics")
async def get_metrics(date_range: str = "30d"):
    """
    Get overall analytics metrics.
    
    Query params:
    - date_range: Time range (7d, 30d, 90d, all)
    
    Returns:
        Metrics dict
    """
    try:
        metrics = analytics_service.get_metrics(date_range)
        return metrics.to_dict()
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-videos")
async def get_top_videos(
    limit: int = 10,
    sort_by: str = "views"
):
    """
    Get top performing videos.
    
    Query params:
    - limit: Number of videos (default: 10)
    - sort_by: Sort criteria (views, likes, engagement, quality)
    
    Returns:
        List of top videos
    """
    try:
        videos = analytics_service.get_top_videos(limit, sort_by)
        return [v.to_dict() for v in videos]
    except Exception as e:
        logger.error(f"Failed to get top videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement-timeseries")
async def get_engagement_timeseries(date_range: str = "30d"):
    """
    Get engagement timeseries data.
    
    Query params:
    - date_range: Time range (7d, 30d, 90d)
    
    Returns:
        List of timeseries data points
    """
    try:
        timeseries = analytics_service.get_engagement_timeseries(date_range)
        return [{"date": ts.date, "value": ts.value} for ts in timeseries]
    except Exception as e:
        logger.error(f"Failed to get timeseries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(date_range: str = "30d"):
    """
    Get complete dashboard data.
    
    Query params:
    - date_range: Time range (7d, 30d, 90d, all)
    
    Returns:
        Complete dashboard data
    """
    try:
        dashboard = analytics_service.get_dashboard_data(date_range)
        return dashboard
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_csv():
    """
    Export analytics to CSV.
    
    Returns:
        CSV file
    """
    try:
        csv_data = analytics_service.export_to_csv()
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics.csv"
            }
        )
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/view/{video_id}")
async def track_view(video_id: str):
    """Track video view"""
    try:
        analytics_service.track_video_view(video_id)
        return {"status": "success", "video_id": video_id}
    except Exception as e:
        logger.error(f"Failed to track view: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/like/{video_id}")
async def track_like(video_id: str):
    """Track video like"""
    try:
        analytics_service.track_video_like(video_id)
        return {"status": "success", "video_id": video_id}
    except Exception as e:
        logger.error(f"Failed to track like: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/share/{video_id}")
async def track_share(video_id: str):
    """Track video share"""
    try:
        analytics_service.track_video_share(video_id)
        return {"status": "success", "video_id": video_id}
    except Exception as e:
        logger.error(f"Failed to track share: {e}")
        raise HTTPException(status_code=500, detail=str(e))

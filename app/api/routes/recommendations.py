"""
Recommendation API Routes
Endpoints for personalized recommendations and discovery.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.recommendation import hybrid_recommender
from app.recommendation.collaborative import collaborative_filter
from app.discovery import discovery_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


# Request/Response Models

class TrackInteractionRequest(BaseModel):
    user_id: str
    video_id: str
    interaction_type: str  # view, like, share, watch_complete


@router.get("")
async def get_recommendations(
    user_id: str,
    count: int = Query(20, ge=1, le=100),
    strategy: str = Query("hybrid", regex="^(collaborative|content|hybrid)$")
):
    """
    Get personalized recommendations for user.
    
    Query params:
    - user_id: User ID
    - count: Number of recommendations (1-100)
    - strategy: Recommendation strategy (collaborative, content, hybrid)
    
    Returns:
        List of recommended video IDs
    """
    try:
        recommendations = hybrid_recommender.recommend(
            user_id=user_id,
            limit=count,
            strategy=strategy
        )
        
        return {
            "user_id": user_id,
            "strategy": strategy,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar")
async def get_similar_videos(
    video_id: str,
    count: int = Query(10, ge=1, le=50)
):
    """
    Get similar videos ("more like this").
    
    Query params:
    - video_id: Source video ID
    - count: Number of similar videos (1-50)
    
    Returns:
        List of similar video IDs
    """
    try:
        similar = hybrid_recommender.recommend_similar(video_id, limit=count)
        
        return {
            "video_id": video_id,
            "similar_videos": similar,
            "count": len(similar)
        }
    except Exception as e:
        logger.error(f"Failed to get similar videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def get_popular_videos(
    count: int = Query(20, ge=1, le=100)
):
    """
    Get popular videos across all users.
    
    Query params:
    - count: Number of popular videos (1-100)
    
    Returns:
        List of popular video IDs
    """
    try:
        popular = hybrid_recommender.get_popular_videos(limit=count)
        
        return {
            "popular_videos": popular,
            "count": len(popular)
        }
    except Exception as e:
        logger.error(f"Failed to get popular videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track")
async def track_interaction(request: TrackInteractionRequest):
    """
    Track user-video interaction.
    
    Body:
    - user_id: User ID
    - video_id: Video ID
    - interaction_type: Type (view, like, share, watch_complete)
    
    Returns:
        Success status
    """
    try:
        collaborative_filter.track_interaction(
            user_id=request.user_id,
            video_id=request.video_id,
            interaction_type=request.interaction_type
        )
        
        return {
            "status": "success",
            "message": f"Tracked {request.interaction_type} for {request.video_id}"
        }
    except Exception as e:
        logger.error(f"Failed to track interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_videos(
    count: int = Query(50, ge=1, le=100)
):
    """
    Get trending videos (last 24h).
    
    Query params:
    - count: Number of trending videos (1-100)
    
    Returns:
        List of trending video IDs
    """
    try:
        trending = discovery_service.get_trending_videos(limit=count)
        
        return {
            "trending_videos": trending,
            "count": len(trending),
            "time_window": "24h"
        }
    except Exception as e:
        logger.error(f"Failed to get trending videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whats-new")
async def get_whats_new(
    count: int = Query(20, ge=1, le=100)
):
    """
    Get recently uploaded videos.
    
    Query params:
    - count: Number of recent videos (1-100)
    
    Returns:
        List of recent video IDs
    """
    try:
        recent = discovery_service.get_whats_new(limit=count)
        
        return {
            "recent_videos": recent,
            "count": len(recent)
        }
    except Exception as e:
        logger.error(f"Failed to get recent videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlist/{user_id}")
async def get_playlist(user_id: str):
    """
    Get user's saved playlist.
    
    Path params:
    - user_id: User ID
    
    Returns:
        List of video IDs in playlist
    """
    try:
        playlist = discovery_service.get_playlist(user_id)
        
        return {
            "user_id": user_id,
            "playlist": playlist,
            "count": len(playlist)
        }
    except Exception as e:
        logger.error(f"Failed to get playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlist/{user_id}/add")
async def add_to_playlist(user_id: str, video_id: str):
    """
    Add video to user's playlist.
    
    Path params:
    - user_id: User ID
    
    Query params:
    - video_id: Video ID to add
    
    Returns:
        Success status
    """
    try:
        discovery_service.add_to_playlist(user_id, video_id)
        
        return {
            "status": "success",
            "message": f"Added {video_id} to playlist"
        }
    except Exception as e:
        logger.error(f"Failed to add to playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/playlist/{user_id}/remove")
async def remove_from_playlist(user_id: str, video_id: str):
    """
    Remove video from user's playlist.
    
    Path params:
    - user_id: User ID
    
    Query params:
    - video_id: Video ID to remove
    
    Returns:
        Success status
    """
    try:
        discovery_service.remove_from_playlist(user_id, video_id)
        
        return {
            "status": "success",
            "message": f"Removed {video_id} from playlist"
        }
    except Exception as e:
        logger.error(f"Failed to remove from playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

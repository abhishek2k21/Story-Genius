"""
Advanced Analytics API Routes
Endpoints for prediction, audience insights, creator intelligence, and market intelligence.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.analytics.prediction_model import prediction_model, VideoParameters
from app.analytics.audience_insights import audience_insights
from app.analytics.creator_intelligence import creator_intelligence, CreatorMetrics
from app.analytics.market_intelligence import market_intelligence
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/advanced-analytics", tags=["advanced-analytics"])


# Request Models

class PredictionRequest(BaseModel):
    hook_quality: float
    pacing: str
    tone: str
    duration: float
    genre: str
    tag_count: int = 3
    has_music: bool = True
    has_effects: bool = True


class WatchTrackingRequest(BaseModel):
    user_id: str
    video_id: str
    watch_time: float
    completion_rate: float


# Performance Prediction Routes

@router.post("/predict-performance")
async def predict_performance(request: PredictionRequest):
    """
    Predict video performance based on generation parameters.
    
    Body:
    - hook_quality: Hook quality score (0-100)
    - pacing: Pacing (fast, medium, slow)
    - tone: Tone (humorous, serious, dramatic, educational)
    - duration: Duration in seconds
    - genre: Genre
    - tag_count: Number of tags
    - has_music: Whether video has music
    - has_effects: Whether video has effects
    
    Returns:
        Performance prediction
    """
    try:
        params = VideoParameters(
            hook_quality=request.hook_quality,
            pacing=request.pacing,
            tone=request.tone,
            duration=request.duration,
            genre=request.genre,
            tag_count=request.tag_count,
            has_music=request.has_music,
            has_effects=request.has_effects
        )
        
        prediction = prediction_model.predict(params)
        
        return {
            "predicted_views": prediction.predicted_views,
            "predicted_engagement": prediction.predicted_engagement,
            "predicted_quality": prediction.predicted_quality,
            "confidence": prediction.confidence
        }
    except Exception as e:
        logger.error(f"Failed to predict performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
async def get_feature_importance(target: str = "views"):
    """
    Get feature importance for prediction model.
    
    Query params:
    - target: Target metric (views, engagement, quality)
    
    Returns:
        Feature importance dict
    """
    try:
        importance = prediction_model.get_feature_importance(target)
        
        if not importance:
            raise HTTPException(status_code=400, detail="Model not trained")
        
        return {
            "target": target,
            "feature_importance": importance
        }
    except Exception as e:
        logger.error(f"Failed to get feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Audience Insights Routes

@router.post("/audience/track-watch")
async def track_watch(request: WatchTrackingRequest):
    """
    Track user watch event.
    
    Body:
    - user_id: User ID
    - video_id: Video ID
    - watch_time: Time watched (seconds)
    - completion_rate: Completion rate (0-100)
    
    Returns:
        Success status
    """
    try:
        audience_insights.track_watch(
            user_id=request.user_id,
            video_id=request.video_id,
            watch_time=request.watch_time,
            completion_rate=request.completion_rate
        )
        
        return {"status": "success", "message": "Watch event tracked"}
    except Exception as e:
        logger.error(f"Failed to track watch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audience/segments")
async def get_user_segments():
    """
    Get audience segmentation.
    
    Returns:
        User segments
    """
    try:
        segments = audience_insights.get_user_segments()
        
        return {
            "segments": {
                segment.value: user_ids
                for segment, user_ids in segments.items()
            },
            "total_users": sum(len(users) for users in segments.values())
        }
    except Exception as e:
        logger.error(f"Failed to get segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audience/cohort-analysis")
async def get_cohort_analysis():
    """
    Get cohort retention analysis.
    
    Returns:
        Cohort data
    """
    try:
        cohorts = audience_insights.cohort_analysis()
        
        return {
            "cohorts": [
                {
                    "month": c.cohort_month,
                    "total_users": c.total_users,
                    "retention_30d": c.retention_30d,
                    "retention_60d": c.retention_60d,
                    "retention_90d": c.retention_90d
                }
                for c in cohorts
            ],
            "total_cohorts": len(cohorts)
        }
    except Exception as e:
        logger.error(f"Failed to get cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audience/demographics")
async def get_demographics():
    """
    Get audience demographics.
    
    Returns:
        Demographics breakdown
    """
    try:
        demographics = audience_insights.get_demographics()
        return demographics
    except Exception as e:
        logger.error(f"Failed to get demographics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Creator Intelligence Routes

@router.get("/creator/analyze/{creator_id}")
async def analyze_creator(creator_id: str):
    """
    Analyze creator performance.
    
    Path params:
    - creator_id: Creator ID
    
    Returns:
        Creator analysis
    """
    try:
        analysis = creator_intelligence.analyze_creator(creator_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Creator not found")
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze creator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creator/benchmark/{creator_id}")
async def benchmark_creator(
    creator_id: str,
    genre: Optional[str] = None
):
    """
    Benchmark creator vs peers.
    
    Path params:
    - creator_id: Creator ID
    
    Query params:
    - genre: Optional genre filter for peers
    
    Returns:
        Benchmarking data
    """
    try:
        benchmark = creator_intelligence.benchmark_vs_peers(creator_id, genre)
        
        if not benchmark:
            raise HTTPException(status_code=404, detail="Creator not found")
        
        return benchmark
    except Exception as e:
        logger.error(f"Failed to benchmark creator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creator/recommendations/{creator_id}")
async def get_creator_recommendations(creator_id: str):
    """
    Get personalized recommendations for creator.
    
    Path params:
    - creator_id: Creator ID
    
    Returns:
        Creator recommendations
    """
    try:
        recommendations = creator_intelligence.get_recommendations(creator_id)
        
        return {
            "creator_id": creator_id,
            "recommended_genres": recommendations.recommended_genres,
            "recommended_topics": recommendations.recommended_topics,
            "collaboration_suggestions": recommendations.collaboration_suggestions,
            "growth_opportunities": recommendations.growth_opportunities
        }
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Market Intelligence Routes

@router.get("/market/trending-topics")
async def get_trending_topics(limit: int = 10):
    """
    Get trending topics/genres.
    
    Query params:
    - limit: Number of topics (default: 10)
    
    Returns:
        Trending topics
    """
    try:
        trending = market_intelligence.get_trending_topics(limit)
        
        return {
            "trending_topics": [
                {
                    "topic": t.topic,
                    "video_count": t.video_count,
                    "total_views": t.total_views,
                    "growth_rate": f"{t.growth_rate:+.1f}%",
                    "saturation": t.saturation_level
                }
                for t in trending
            ],
            "count": len(trending)
        }
    except Exception as e:
        logger.error(f"Failed to get trending topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/saturation/{topic}")
async def analyze_saturation(topic: str):
    """
    Analyze market saturation for a topic.
    
    Path params:
    - topic: Topic to analyze
    
    Returns:
        Saturation analysis
    """
    try:
        analysis = market_intelligence.analyze_market_saturation(topic)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze saturation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/content-gaps")
async def get_content_gaps(min_opportunity: float = 60.0):
    """
    Find content opportunities (gaps in market).
    
    Query params:
    - min_opportunity: Minimum opportunity score (default: 60.0)
    
    Returns:
        Content gaps
    """
    try:
        gaps = market_intelligence.find_content_gaps(min_opportunity)
        
        return {
            "content_gaps": [
                {
                    "topic": g.topic,
                    "demand_score": g.demand_score,
                    "supply_score": g.supply_score,
                    "opportunity_score": g.opportunity_score
                }
                for g in gaps
            ],
            "count": len(gaps)
        }
    except Exception as e:
        logger.error(f"Failed to get content gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/emerging-creators")
async def get_emerging_creators(limit: int = 10):
    """
    Get emerging creators (high growth).
    
    Query params:
    - limit: Number of creators (default: 10)
    
    Returns:
        Emerging creators
    """
    try:
        emerging = market_intelligence.get_emerging_creators(limit)
        
        return {
            "emerging_creators": [
                {"creator_id": c_id, "growth_rate": f"{rate:+.1f}%"}
                for c_id, rate in emerging
            ],
            "count": len(emerging)
        }
    except Exception as e:
        logger.error(f"Failed to get emerging creators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/report")
async def get_market_report():
    """
    Get comprehensive market intelligence report.
    
    Returns:
        Market report
    """
    try:
        report = market_intelligence.generate_market_report()
        return report
    except Exception as e:
        logger.error(f"Failed to generate market report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

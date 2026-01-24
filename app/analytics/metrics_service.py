"""
Metrics Ingestion Service
Feeds real-world performance data back into the system for learning.
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.core.database import get_db_session

logger = get_logger(__name__)


@dataclass
class VideoMetrics:
    """Real-world performance metrics for a video."""
    id: str
    job_id: str
    video_id: str  # External video ID (YouTube, etc.)
    
    # Core metrics
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Watch metrics
    avg_watch_time: float = 0.0
    avg_percentage_watched: float = 0.0
    replays: int = 0
    
    # Derived scores (calculated)
    retention_score: float = 0.0
    engagement_score: float = 0.0
    hook_effectiveness: float = 0.0
    loop_strength: float = 0.0
    
    # Metadata
    platform: str = "youtube_shorts"
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_scores(self, video_duration: int = 30):
        """Calculate derived scores from raw metrics."""
        # Retention: % watched
        if video_duration > 0:
            self.retention_score = min(1.0, self.avg_watch_time / video_duration)
        
        # Engagement: (likes + comments + shares) / views
        if self.views > 0:
            self.engagement_score = min(1.0, 
                (self.likes + self.comments * 2 + self.shares * 3) / (self.views * 0.1)
            )
        
        # Hook effectiveness: If avg watch > 3s, hook worked
        self.hook_effectiveness = 1.0 if self.avg_watch_time > 3 else self.avg_watch_time / 3
        
        # Loop strength: replays indicate good loop
        if self.views > 0:
            self.loop_strength = min(1.0, self.replays / (self.views * 0.3))


class MetricsService:
    """
    Service for ingesting and processing real-world video metrics.
    """
    
    def __init__(self):
        self._metrics_store: Dict[str, VideoMetrics] = {}
        self.db = get_db_session()
    
    def ingest_metrics(
        self,
        job_id: str,
        video_id: str,
        metrics: Dict
    ) -> VideoMetrics:
        """
        Ingest metrics from external source.
        
        Args:
            job_id: Internal job ID
            video_id: External video ID
            metrics: Raw metrics dict
            
        Returns:
            Processed VideoMetrics
        """
        metric_id = str(uuid.uuid4())
        
        video_metrics = VideoMetrics(
            id=metric_id,
            job_id=job_id,
            video_id=video_id,
            views=metrics.get("views", 0),
            likes=metrics.get("likes", 0),
            comments=metrics.get("comments", 0),
            shares=metrics.get("shares", 0),
            avg_watch_time=metrics.get("avg_watch_time", 0),
            avg_percentage_watched=metrics.get("avg_percentage_watched", 0),
            replays=metrics.get("replays", 0),
            platform=metrics.get("platform", "youtube_shorts")
        )
        
        # Calculate derived scores
        video_duration = metrics.get("video_duration", 30)
        video_metrics.calculate_scores(video_duration)
        
        # Store
        self._metrics_store[metric_id] = video_metrics
        
        logger.info(f"Ingested metrics for job {job_id[:8]}: "
                   f"views={video_metrics.views}, retention={video_metrics.retention_score:.2f}")
        
        return video_metrics
    
    def get_metrics(self, job_id: str) -> Optional[VideoMetrics]:
        """Get metrics for a job."""
        for m in self._metrics_store.values():
            if m.job_id == job_id:
                return m
        return None
    
    def get_metrics_by_video_id(self, video_id: str) -> Optional[VideoMetrics]:
        """Get metrics by external video ID."""
        for m in self._metrics_store.values():
            if m.video_id == video_id:
                return m
        return None
    
    def get_learning_feedback(self, job_id: str) -> Dict:
        """
        Get feedback for learning based on real metrics.
        
        Returns dict with what worked and what didn't.
        """
        metrics = self.get_metrics(job_id)
        if not metrics:
            return {"status": "no_metrics"}
        
        feedback = {
            "job_id": job_id,
            "overall_performance": "good" if metrics.retention_score > 0.5 else "needs_improvement",
            "hook_worked": metrics.hook_effectiveness > 0.7,
            "loop_worked": metrics.loop_strength > 0.5,
            "recommendations": []
        }
        
        if metrics.hook_effectiveness < 0.7:
            feedback["recommendations"].append("Hook needs more pattern interrupt power")
        
        if metrics.loop_strength < 0.5:
            feedback["recommendations"].append("Ending doesn't create replay desire")
        
        if metrics.retention_score < 0.5:
            feedback["recommendations"].append("Pacing may be too slow in middle sections")
        
        return feedback
    
    def get_aggregate_insights(self, limit: int = 100) -> Dict:
        """
        Get aggregate insights from all collected metrics.
        """
        metrics = list(self._metrics_store.values())[:limit]
        
        if not metrics:
            return {"status": "no_data"}
        
        total = len(metrics)
        avg_retention = sum(m.retention_score for m in metrics) / total
        avg_engagement = sum(m.engagement_score for m in metrics) / total
        avg_hook = sum(m.hook_effectiveness for m in metrics) / total
        avg_loop = sum(m.loop_strength for m in metrics) / total
        
        return {
            "total_videos_tracked": total,
            "avg_retention_score": round(avg_retention, 3),
            "avg_engagement_score": round(avg_engagement, 3),
            "avg_hook_effectiveness": round(avg_hook, 3),
            "avg_loop_strength": round(avg_loop, 3),
            "total_views": sum(m.views for m in metrics),
            "top_performers": [
                m.job_id for m in sorted(metrics, key=lambda x: x.retention_score, reverse=True)[:5]
            ]
        }
    
    def export_for_training(self) -> List[Dict]:
        """
        Export metrics data for ML training.
        """
        return [asdict(m) for m in self._metrics_store.values()]

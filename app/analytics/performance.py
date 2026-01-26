"""
Week 18 Day 5 - Performance Analytics
Show which videos performed best and why.
Creators optimize based on data, not guesses.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import random

@dataclass
class VideoPerformance:
    """Performance metrics for a generated video."""
    job_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform: str = "youtube_shorts"
    title: str = ""
    
    # Engagement
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Retention
    watch_time_seconds: int = 0
    avg_retention_percent: float = 0.0
    retention_at_3s: float = 0.0  # Critical for hook check
    
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "platform": self.platform,
            "title": self.title,
            "views": self.views,
            "likes": self.likes,
            "retention": f"{self.avg_retention_percent:.1%}",
            "retention_3s": f"{self.retention_at_3s:.1%}"
        }


class PerformanceAnalytics:
    """Service to track and analyze video performance."""
    
    def __init__(self):
        self._metrics: Dict[str, VideoPerformance] = {}
        
    def record_metrics(self, job_id: str, platform: str, **metrics) -> VideoPerformance:
        """Update or create metrics for a video."""
        perf = self._metrics.get(job_id)
        if not perf:
            perf = VideoPerformance(job_id=job_id, platform=platform)
            self._metrics[job_id] = perf
            
        # Update fields
        for key, value in metrics.items():
            if hasattr(perf, key):
                setattr(perf, key, value)
                
        perf.updated_at = datetime.now()
        return perf
        
    def get_top_performers(
        self,
        user_id: str,
        metric: str = "views",
        limit: int = 10
    ) -> List[VideoPerformance]:
        """Get best performing videos."""
        # In real app: SQL query filtering by user_id owner of job_id
        # Here we mock it
        all_perfs = list(self._metrics.values())
        
        # Sort desc
        all_perfs.sort(key=lambda x: getattr(x, metric, 0), reverse=True)
        return all_perfs[:limit]
        
    def get_insights(self, user_id: str) -> dict:
        """
        Derive insights from data.
        Returns aggregate stats and patterns.
        """
        perfs = list(self._metrics.values())
        if not perfs:
            return {"status": "no_data"}
            
        total_views = sum(p.views for p in perfs)
        avg_retention = sum(p.avg_retention_percent for p in perfs) / len(perfs)
        
        # Mock insights for now (would require analyzing content metadata vs performance)
        return {
            "total_views": total_views,
            "avg_retention": avg_retention,
            "best_duration": "45-60s", # derived from top videos
            "best_hook_type": "Question", # derived from top videos
            "best_posting_time": "18:00"
        }
        
    def mock_data_generation(self, job_ids: List[str]):
        """Generate fake data for testing."""
        for job_id in job_ids:
            views = random.randint(100, 50000)
            self.record_metrics(
                job_id=job_id,
                platform="youtube",
                title=f"Video {job_id}",
                views=views,
                likes=int(views * 0.1),
                avg_retention_percent=random.uniform(0.4, 0.9),
                retention_at_3s=random.uniform(0.6, 0.95)
            )


# Singleton
_analytics = None

def get_analytics() -> PerformanceAnalytics:
    global _analytics
    if _analytics is None:
        _analytics = PerformanceAnalytics()
    return _analytics

"""
Analytics Service
Provides analytics data for dashboard and reporting.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnalyticsMetrics:
    """Analytics metrics"""
    total_videos: int
    total_views: int
    avg_engagement: float
    avg_quality: float
    total_likes: int
    total_shares: int
    
    def to_dict(self) -> Dict:
        return {
            "total_videos": self.total_videos,
            "total_views": self.total_views,
            "avg_engagement": round(self.avg_engagement, 2),
            "avg_quality": round(self.avg_quality, 2),
            "total_likes": self.total_likes,
            "total_shares": self.total_shares
        }


@dataclass
class VideoPerformance:
    """Video performance data"""
    id: str
    title: str
    views: int
    likes: int
    shares: int
    engagement: float
    quality: float
    created_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "views": self.views,
            "likes": self.likes,
            "shares": self.shares,
            "engagement": round(self.engagement, 2),
            "quality": round(self.quality, 2),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TimeseriesData:
    """Timeseries data point"""
    date: str
    value: float


class AnalyticsService:
    """
    Analytics service for tracking and reporting metrics.
    """
    
    def __init__(self):
        # Mock data storage (in production: use database)
        self._videos: Dict[str, VideoPerformance] = {}
        self._timeseries: Dict[str, List[TimeseriesData]] = defaultdict(list)
        logger.info("AnalyticsService initialized")
    
    def track_video_view(self, video_id: str):
        """Track video view"""
        if video_id in self._videos:
            self._videos[video_id].views += 1
            logger.debug(f"Tracked view for video: {video_id}")
    
    def track_video_like(self, video_id: str):
        """Track video like"""
        if video_id in self._videos:
            self._videos[video_id].likes += 1
            logger.debug(f"Tracked like for video: {video_id}")
    
    def track_video_share(self, video_id: str):
        """Track video share"""
        if video_id in self._videos:
            self._videos[video_id].shares += 1
            logger.debug(f"Tracked share for video: {video_id}")
    
    def add_video(
        self,
        video_id: str,
        title: str,
        quality: float
    ):
        """Add video to analytics tracking"""
        video = VideoPerformance(
            id=video_id,
            title=title,
            views=0,
            likes=0,
            shares=0,
            engagement=0.0,
            quality=quality,
            created_at=datetime.utcnow()
        )
        
        self._videos[video_id] = video
        logger.info(f"Added video to analytics: {video_id}")
    
    def calculate_engagement(self, video_id: str) -> float:
        """
        Calculate engagement rate.
        Engagement = (likes + shares) / views * 100
        """
        if video_id not in self._videos:
            return 0.0
        
        video = self._videos[video_id]
        
        if video.views == 0:
            return 0.0
        
        engagement = ((video.likes + video.shares) / video.views) * 100
        video.engagement = engagement
        
        return engagement
    
    def get_metrics(
        self,
        date_range: Optional[str] = "30d"
    ) -> AnalyticsMetrics:
        """
        Get overall analytics metrics.
        
        Args:
            date_range: Time range (7d, 30d, 90d, all)
        
        Returns:
            AnalyticsMetrics
        """
        # Filter videos by date range
        cutoff_date = self._get_cutoff_date(date_range)
        
        filtered_videos = [
            v for v in self._videos.values()
            if cutoff_date is None or v.created_at >= cutoff_date
        ]
        
        if not filtered_videos:
            return AnalyticsMetrics(
                total_videos=0,
                total_views=0,
                avg_engagement=0.0,
                avg_quality=0.0,
                total_likes=0,
                total_shares=0
            )
        
        total_videos = len(filtered_videos)
        total_views = sum(v.views for v in filtered_videos)
        total_likes = sum(v.likes for v in filtered_videos)
        total_shares = sum(v.shares for v in filtered_videos)
        
        # Calculate averages
        avg_engagement = sum(
            self.calculate_engagement(v.id) for v in filtered_videos
        ) / total_videos
        
        avg_quality = sum(v.quality for v in filtered_videos) / total_videos
        
        metrics = AnalyticsMetrics(
            total_videos=total_videos,
            total_views=total_views,
            avg_engagement=avg_engagement,
            avg_quality=avg_quality,
            total_likes=total_likes,
            total_shares=total_shares
        )
        
        logger.info(
            f"Generated metrics for {date_range}: "
            f"{total_videos} videos, {total_views} views"
        )
        
        return metrics
    
    def get_top_videos(
        self,
        limit: int = 10,
        sort_by: str = "views"
    ) -> List[VideoPerformance]:
        """
        Get top performing videos.
        
        Args:
            limit: Number of videos to return
            sort_by: Sort criteria (views, likes, engagement, quality)
        
        Returns:
            List of top videos
        """
        # Update engagement for all videos
        for video_id in self._videos:
            self.calculate_engagement(video_id)
        
        # Sort videos
        videos = list(self._videos.values())
        
        if sort_by == "views":
            videos.sort(key=lambda v: v.views, reverse=True)
        elif sort_by == "likes":
            videos.sort(key=lambda v: v.likes, reverse=True)
        elif sort_by == "engagement":
            videos.sort(key=lambda v: v.engagement, reverse=True)
        elif sort_by == "quality":
            videos.sort(key=lambda v: v.quality, reverse=True)
        
        top_videos = videos[:limit]
        
        logger.info(f"Retrieved top {limit} videos sorted by {sort_by}")
        
        return top_videos
    
    def get_engagement_timeseries(
        self,
        date_range: str = "30d"
    ) -> List[TimeseriesData]:
        """
        Get engagement timeseries data.
        
        Args:
            date_range: Time range (7d, 30d, 90d)
        
        Returns:
            List of timeseries data points
        """
        days = self._parse_date_range(date_range)
        
        # Generate mock timeseries data
        # In production: aggregate from database
        timeseries = []
        
        import random
        base_engagement = 65.0
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
            
            # Simulate engagement trend (slightly increasing)
            engagement = base_engagement + (i * 0.3) + random.uniform(-5, 5)
            
            timeseries.append(TimeseriesData(
                date=date,
                value=round(engagement, 2)
            ))
        
        return timeseries
    
    def export_to_csv(self) -> str:
        """
        Export analytics data to CSV.
        
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Video ID', 'Title', 'Views', 'Likes', 'Shares',
            'Engagement %', 'Quality', 'Created At'
        ])
        
        # Data
        for video in self._videos.values():
            writer.writerow([
                video.id,
                video.title,
                video.views,
                video.likes,
                video.shares,
                round(video.engagement, 2),
                round(video.quality, 2),
                video.created_at.isoformat()
            ])
        
        csv_data = output.getvalue()
        logger.info("Exported analytics to CSV")
        
        return csv_data
    
    def _get_cutoff_date(self, date_range: Optional[str]) -> Optional[datetime]:
        """Get cutoff date for filtering"""
        if date_range == "all" or date_range is None:
            return None
        
        days = self._parse_date_range(date_range)
        return datetime.utcnow() - timedelta(days=days)
    
    def _parse_date_range(self, date_range: str) -> int:
        """Parse date range string to days"""
        if date_range.endswith('d'):
            return int(date_range[:-1])
        elif date_range.endswith('m'):
            return int(date_range[:-1]) * 30
        elif date_range.endswith('y'):
            return int(date_range[:-1]) * 365
        else:
            return 30  # Default to 30 days
    
    def get_dashboard_data(
        self,
        date_range: str = "30d"
    ) -> Dict:
        """
        Get complete dashboard data.
        
        Returns:
            Dashboard data dict
        """
        metrics = self.get_metrics(date_range)
        top_videos = self.get_top_videos(limit=10)
        engagement_timeseries = self.get_engagement_timeseries(date_range)
        
        return {
            "metrics": metrics.to_dict(),
            "top_videos": [v.to_dict() for v in top_videos],
            "engagement_timeseries": [
                {"date": ts.date, "value": ts.value}
                for ts in engagement_timeseries
            ],
            "date_range": date_range
        }


# Global instance
analytics_service = AnalyticsService()

"""
Discovery Features
Trending videos, creators, topics, and exploration features.
"""
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VideoStats:
    """Video statistics"""
    id: str
    title: str
    views: int
    likes: int
    shares: int
    created_at: datetime
    views_24h: int = 0
    likes_24h: int = 0
    shares_24h: int = 0


class TrendingAlgorithm:
    """
    Calculate trending content based on engagement and recency.
    """
    
    def __init__(self):
        self._videos: Dict[str, VideoStats] = {}
        logger.info("TrendingAlgorithm initialized")
    
    def add_video(self, video: VideoStats):
        """Add video to trending tracking"""
        self._videos[video.id] = video
    
    def calculate_trending_score(
        self,
        video: VideoStats,
        time_window: str = "24h"
    ) -> float:
        """
        Calculate trending score.
        
        Formula:
        score = (views * 1 + likes * 2 + shares * 3) / age_decay
        
        Args:
            video: Video statistics
            time_window: Time window for metrics
        
        Returns:
            Trending score
        """
        # Get metrics for time window
        if time_window == "24h":
            views = video.views_24h
            likes = video.likes_24h
            shares = video.shares_24h
        else:
            views = video.views
            likes = video.likes
            shares = video.shares
        
        # Calculate engagement score
        engagement_score = views * 1 + likes * 2 + shares * 3
        
        # Age decay (newer videos get higher scores)
        age_hours = (datetime.utcnow() - video.created_at).total_seconds() / 3600
        age_decay = 1 + (age_hours / 24)  # Decays over days
        
        # Trending score
        trending_score = engagement_score / age_decay
        
        return trending_score
    
    def get_trending_videos(
        self,
        limit: int = 50,
        time_window: str = "24h"
    ) -> List[Tuple[str, float]]:
        """
        Get trending videos.
        
        Args:
            limit: Number of trending videos
            time_window: Time window (24h, 7d, 30d)
        
        Returns:
            List of (video_id, trending_score) tuples
        """
        scored_videos = []
        
        for video in self._videos.values():
            score = self.calculate_trending_score(video, time_window)
            scored_videos.append((video.id, score))
        
        # Sort by score (descending)
        scored_videos.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(scored_videos[:limit])} trending videos ({time_window})")
        
        return scored_videos[:limit]
    
    def get_trending_topics(
        self,
        videos_by_topic: Dict[str, List[str]],
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Get trending topics/genres.
        
        Args:
            videos_by_topic: Mapping of topic to video IDs
            limit: Number of trending topics
        
        Returns:
            List of (topic, video_count) tuples
        """
        topic_scores = {}
        
        for topic, video_ids in videos_by_topic.items():
            # Count videos and sum their engagement
            total_score = sum(
                self.calculate_trending_score(self._videos[vid_id])
                for vid_id in video_ids
                if vid_id in self._videos
            )
            
            topic_scores[topic] = total_score
        
        # Sort by score
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_topics[:limit]


class DiscoveryService:
    """
    Discovery and exploration features.
    """
    
    def __init__(self):
        self.trending = TrendingAlgorithm()
        self._playlists: Dict[str, List[str]] = defaultdict(list)  # user_id -> video_ids
        logger.info("DiscoveryService initialized")
    
    def get_trending_videos(self, limit: int = 50) -> List[str]:
        """Get trending videos (last 24h)"""
        trending = self.trending.get_trending_videos(limit)
        return [video_id for video_id, _ in trending]
    
    def get_whats_new(self, limit: int = 20) -> List[str]:
        """Get recently uploaded videos"""
        all_videos = list(self.trending._videos.values())
        
        # Sort by created_at (descending)
        all_videos.sort(key=lambda v: v.created_at, reverse=True)
        
        return [v.id for v in all_videos[:limit]]
    
    def create_playlist(
        self,
        user_id: str,
        video_ids: List[str]
    ):
        """Create/update user playlist"""
        self._playlists[user_id] = video_ids
        logger.info(f"Created playlist for {user_id}: {len(video_ids)} videos")
    
    def get_playlist(self, user_id: str) -> List[str]:
        """Get user's saved playlist"""
        return self._playlists.get(user_id, [])
    
    def add_to_playlist(self, user_id: str, video_id: str):
        """Add video to user's playlist"""
        if video_id not in self._playlists[user_id]:
            self._playlists[user_id].append(video_id)
            logger.debug(f"Added {video_id} to {user_id}'s playlist")
    
    def remove_from_playlist(self, user_id: str, video_id: str):
        """Remove video from user's playlist"""
        if video_id in self._playlists[user_id]:
            self._playlists[user_id].remove(video_id)
            logger.debug(f"Removed {video_id} from {user_id}'s playlist")


# Global instance
discovery_service = DiscoveryService()

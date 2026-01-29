"""
Creator Intelligence
Performance analysis and recommendations for creators.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CreatorMetrics:
    """Creator performance metrics"""
    creator_id: str
    total_videos: int
    total_views: int
    avg_views_per_video: float
    total_engagement: float  # likes + shares
    avg_engagement_rate: float
    avg_quality_score: float
    primary_genre: str
    growth_rate: float  # month-over-month %


@dataclass
class CreatorRecommendation:
    """Recommendations for creator"""
    recommended_genres: List[str]
    recommended_topics: List[str]
    collaboration_suggestions: List[str]
    growth_opportunities: List[str]


class CreatorIntelligence:
    """
    Creator performance analysis and intelligence system.
    
    Features:
    - Creator performance tracking
    - Benchmarking vs peers
    - Niche analysis
    - Growth recommendations
    - Collaboration suggestions
    """
    
    def __init__(self):
        self._creators: Dict[str, CreatorMetrics] = {}
        self._video_performance: Dict[str, List[Dict]] = defaultdict(list)  # creator_id -> videos
        logger.info("CreatorIntelligence initialized")
    
    def add_creator(self, metrics: CreatorMetrics):
        """Add/update creator in system"""
        self._creators[metrics.creator_id] = metrics
        logger.debug(f"Added creator: {metrics.creator_id}")
    
    def track_video_performance(
        self,
        creator_id: str,
        video_data: Dict
    ):
        """
        Track video performance for a creator.
        
        Args:
            creator_id: Creator ID
            video_data: Video performance data (views, engagement, quality, genre)
        """
        self._video_performance[creator_id].append(video_data)
        logger.debug(f"Tracked video for creator: {creator_id}")
    
    def calculate_performance_percentile(
        self,
        creator_id: str
    ) -> float:
        """
        Calculate creator's performance percentile vs all creators.
        
        Returns:
            Percentile (0-100)
        """
        if creator_id not in self._creators:
            return 0.0
        
        creator = self._creators[creator_id]
        
        # Get all creators' avg views
        all_avg_views = [c.avg_views_per_video for c in self._creators.values()]
        
        if not all_avg_views:
            return 50.0
        
        # Count how many creators have lower avg views
        lower_count = sum(1 for v in all_avg_views if v < creator.avg_views_per_video)
        
        percentile = (lower_count / len(all_avg_views)) * 100
        
        return round(percentile, 1)
    
    def analyze_creator(self, creator_id: str) -> Dict:
        """
        Comprehensive creator analysis.
        
        Args:
            creator_id: Creator ID
        
        Returns:
            Analysis dict
        """
        if creator_id not in self._creators:
            return {}
        
        creator = self._creators[creator_id]
        
        # Performance percentile
        percentile = self.calculate_performance_percentile(creator_id)
        
        # Genre analysis
        videos = self._video_performance.get(creator_id, [])
        genre_performance = self._analyze_genre_performance(videos)
        
        # Growth analysis
        growth_trend = self._analyze_growth(creator_id)
        
        return {
            "creator_id": creator_id,
            "performance_percentile": percentile,
            "rank_description": self._get_rank_description(percentile),
            "total_videos": creator.total_videos,
            "total_views": creator.total_views,
            "avg_views": int(creator.avg_views_per_video),
            "avg_engagement_rate": round(creator.avg_engagement_rate, 1),
            "avg_quality": round(creator.avg_quality_score, 1),
            "primary_genre": creator.primary_genre,
            "strongest_genre": genre_performance["strongest"],
            "growth_rate": f"{creator.growth_rate:+.1f}%",
            "growth_trend": growth_trend
        }
    
    def benchmark_vs_peers(
        self,
        creator_id: str,
        genre: Optional[str] = None
    ) -> Dict:
        """
        Benchmark creator against peers.
        
        Args:
            creator_id: Creator ID
            genre: Optional genre filter for peer selection
        
        Returns:
            Benchmarking data
        """
        if creator_id not in self._creators:
            return {}
        
        creator = self._creators[creator_id]
        
        # Find peers (same genre or all)
        if genre:
            peers = [
                c for c in self._creators.values()
                if c.primary_genre == genre and c.creator_id != creator_id
            ]
        else:
            peers = [
                c for c in self._creators.values()
                if c.creator_id != creator_id
            ]
        
        if not peers:
            return {"message": "No peers found"}
        
        # Calculate peer averages
        peer_avg_views = statistics.mean(c.avg_views_per_video for c in peers)
        peer_avg_engagement = statistics.mean(c.avg_engagement_rate for c in peers)
        peer_avg_quality = statistics.mean(c.avg_quality_score for c in peers)
        
        return {
            "creator_id": creator_id,
            "peer_group": genre or "all",
            "peer_count": len(peers),
            "metrics": {
                "avg_views": {
                    "creator": int(creator.avg_views_per_video),
                    "peers": int(peer_avg_views),
                    "vs_peers": self._calculate_diff(
                        creator.avg_views_per_video, peer_avg_views
                    )
                },
                "avg_engagement": {
                    "creator": round(creator.avg_engagement_rate, 1),
                    "peers": round(peer_avg_engagement, 1),
                    "vs_peers": self._calculate_diff(
                        creator.avg_engagement_rate, peer_avg_engagement
                    )
                },
                "avg_quality": {
                    "creator": round(creator.avg_quality_score, 1),
                    "peers": round(peer_avg_quality, 1),
                    "vs_peers": self._calculate_diff(
                        creator.avg_quality_score, peer_avg_quality
                    )
                }
            }
        }
    
    def get_recommendations(self, creator_id: str) -> CreatorRecommendation:
        """
        Generate personalized recommendations for creator.
        
        Args:
            creator_id: Creator ID
        
        Returns:
            Recommendations
        """
        if creator_id not in self._creators:
            return CreatorRecommendation([], [], [], [])
        
        creator = self._creators[creator_id]
        videos = self._video_performance.get(creator_id, [])
        
        # Analyze genre performance
        genre_perf = self._analyze_genre_performance(videos)
        
        # Recommended genres (based on market trends)
        recommended_genres = [
            genre for genre in ["comedy", "educational", "vlogs"]
            if genre != creator.primary_genre
        ][:2]
        
        # Recommended topics (based on performance)
        recommended_topics = genre_perf.get("top_topics", ["tutorials", "reviews"])
        
        # Collaboration suggestions (similar creators)
        collaboration_suggestions = self._find_collaboration_partners(creator_id)
        
        # Growth opportunities
        growth_opportunities = []
        if creator.avg_quality_score < 80:
            growth_opportunities.append("Improve content quality (target: 80+)")
        if creator.avg_engagement_rate < 60:
            growth_opportunities.append("Increase engagement (add CTAs, community interaction)")
        if creator.total_videos < 50:
            growth_opportunities.append("Increase content volume (consistency is key)")
        
        return CreatorRecommendation(
            recommended_genres=recommended_genres,
            recommended_topics=recommended_topics,
            collaboration_suggestions=collaboration_suggestions,
            growth_opportunities=growth_opportunities
        )
    
    def _analyze_genre_performance(self, videos: List[Dict]) -> Dict:
        """Analyze performance by genre"""
        if not videos:
            return {"strongest": "unknown", "top_topics": []}
        
        genre_views = defaultdict(list)
        
        for video in videos:
            genre = video.get("genre", "unknown")
            views = video.get("views", 0)
            genre_views[genre].append(views)
        
        # Find strongest genre
        genre_avg_views = {
            genre: statistics.mean(views)
            for genre, views in genre_views.items()
        }
        
        strongest = max(genre_avg_views, key=genre_avg_views.get, default="unknown")
        
        return {
            "strongest": strongest,
            "top_topics": ["tutorials", "reviews"]  # Placeholder
        }
    
    def _analyze_growth(self, creator_id: str) -> str:
        """Analyze growth trend"""
        if creator_id not in self._creators:
            return "stable"
        
        creator = self._creators[creator_id]
        
        if creator.growth_rate > 10:
            return "accelerating"
        elif creator.growth_rate > 0:
            return "growing"
        elif creator.growth_rate > -10:
            return "stable"
        else:
            return "declining"
    
    def _get_rank_description(self, percentile: float) -> str:
        """Get rank description from percentile"""
        if percentile >= 90:
            return "Top 10%"
        elif percentile >= 75:
            return "Top 25%"
        elif percentile >= 50:
            return "Top 50%"
        else:
            return "Bottom 50%"
    
    def _calculate_diff(self, value: float, reference: float) -> str:
        """Calculate percentage difference"""
        if reference == 0:
            return "N/A"
        
        diff = ((value - reference) / reference) * 100
        return f"{diff:+.1f}%"
    
    def _find_collaboration_partners(self, creator_id: str) -> List[str]:
        """Find potential collaboration partners"""
        if creator_id not in self._creators:
            return []
        
        creator = self._creators[creator_id]
        
        # Find creators in similar performance range and genre
        partners = []
        
        for other_id, other in self._creators.items():
            if other_id == creator_id:
                continue
            
            # Similar genre or complementary
            if other.primary_genre == creator.primary_genre:
                # Similar performance level
                view_ratio = other.avg_views_per_video / max(creator.avg_views_per_video, 1)
                if 0.5 < view_ratio < 2.0:  # Within 2x range
                    partners.append(other_id)
        
        return partners[:3]  # Top 3 suggestions


# Global instance
creator_intelligence = CreatorIntelligence()

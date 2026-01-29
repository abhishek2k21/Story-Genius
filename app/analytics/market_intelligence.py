"""
Market Intelligence
Platform trends and competitive analysis.
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TopicTrend:
    """Topic trend data"""
    topic: str
    video_count: int
    total_views: int
    growth_rate: float  # percentage
    saturation_level: str  # low, medium, high


@dataclass
class ContentGap:
    """Content opportunity (gap in market)"""
    topic: str
    demand_score: float  # 0-100
    supply_score: float  # 0-100
    opportunity_score: float  # 0-100


class MarketIntelligence:
    """
    Market intelligence and competitive analysis system.
    
    Features:
    - Trending topics/genres tracking
    - Market saturation analysis
    - Emerging creator identification
    - Content gap detection
    """
    
    def __init__(self):
        self._topic_data: Dict[str, Dict] = {}  # topic -> {views, videos, growth}
        self._creator_growth: Dict[str, float] = {}  # creator_id -> growth_rate
        logger.info("MarketIntelligence initialized")
    
    def track_topic(
        self,
        topic: str,
        video_count: int,
        total_views: int,
        previous_views: int
    ):
        """
        Track topic performance.
        
        Args:
            topic: Topic/genre name
            video_count: Number of videos in topic
            total_views: Total views for topic
            previous_views: Views in previous period
        """
        # Calculate growth rate
        if previous_views > 0:
            growth_rate = ((total_views - previous_views) / previous_views) * 100
        else:
            growth_rate = 0.0
        
        self._topic_data[topic] = {
            "video_count": video_count,
            "total_views": total_views,
            "growth_rate": growth_rate
        }
        
        logger.debug(f"Tracked topic: {topic} (growth: {growth_rate:+.1f}%)")
    
    def get_trending_topics(self, limit: int = 10) -> List[TopicTrend]:
        """
        Get trending topics sorted by growth rate.
        
        Args:
            limit: Number of topics to return
        
        Returns:
            List of trending topics
        """
        trends = []
        
        for topic, data in self._topic_data.items():
            # Determine saturation level
            saturation = self._calculate_saturation(data["video_count"])
            
            trends.append(TopicTrend(
                topic=topic,
                video_count=data["video_count"],
                total_views=data["total_views"],
                growth_rate=data["growth_rate"],
                saturation_level=saturation
            ))
        
        # Sort by growth rate (descending)
        trends.sort(key=lambda t: t.growth_rate, reverse=True)
        
        logger.info(f"Generated {len(trends[:limit])} trending topics")
        
        return trends[:limit]
    
    def analyze_market_saturation(self, topic: str) -> Dict:
        """
        Analyze market saturation for a topic.
        
        Args:
            topic: Topic to analyze
        
        Returns:
            Saturation analysis
        """
        if topic not in self._topic_data:
            return {"error": "Topic not found"}
        
        data = self._topic_data[topic]
        video_count = data["video_count"]
        
        saturation_level = self._calculate_saturation(video_count)
        
        # Competitive intensity
        if video_count > 1000:
            competition = "high"
            recommendation = "Highly competitive. Consider niche sub-topics or unique angles."
        elif video_count > 500:
            competition = "medium"
            recommendation = "Moderately competitive. Focus on quality and differentiation."
        else:
            competition = "low"
            recommendation = "Lower competition. Good opportunity for new creators."
        
        return {
            "topic": topic,
            "video_count": video_count,
            "saturation_level": saturation_level,
            "competition": competition,
            "growth_rate": f"{data['growth_rate']:+.1f}%",
            "recommendation": recommendation
        }
    
    def find_content_gaps(self, min_opportunity: float = 60.0) -> List[ContentGap]:
        """
        Identify content opportunities (high demand, low supply).
        
        Args:
            min_opportunity: Minimum opportunity score
        
        Returns:
            List of content gaps
        """
        gaps = []
        
        for topic, data in self._topic_data.items():
            # Demand score (based on views)
            demand_score = min(100, (data["total_views"] / 1000000) * 100)
            
            # Supply score (based on video count)
            supply_score = min(100, (data["video_count"] / 1000) * 100)
            
            # Opportunity score (high demand, low supply)
            opportunity_score = (demand_score * 0.7) + ((100 - supply_score) * 0.3)
            
            if opportunity_score >= min_opportunity:
                gaps.append(ContentGap(
                    topic=topic,
                    demand_score=round(demand_score, 1),
                    supply_score=round(supply_score, 1),
                    opportunity_score=round(opportunity_score, 1)
                ))
        
        # Sort by opportunity score (descending)
        gaps.sort(key=lambda g: g.opportunity_score, reverse=True)
        
        logger.info(f"Found {len(gaps)} content gaps")
        
        return gaps
    
    def track_creator_growth(self, creator_id: str, growth_rate: float):
        """Track creator growth rate"""
        self._creator_growth[creator_id] = growth_rate
    
    def get_emerging_creators(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Find emerging creators (high growth rate).
        
        Args:
            limit: Number of creators to return
        
        Returns:
            List of (creator_id, growth_rate) tuples
        """
        # Sort by growth rate (descending)
        emerging = sorted(
            self._creator_growth.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"Identified {len(emerging[:limit])} emerging creators")
        
        return emerging[:limit]
    
    def generate_market_report(self) -> Dict:
        """
        Generate comprehensive market intelligence report.
        
        Returns:
            Market report dict
        """
        trending_topics = self.get_trending_topics(limit=10)
        content_gaps = self.find_content_gaps(min_opportunity=60.0)
        emerging_creators = self.get_emerging_creators(limit=10)
        
        # Overall market health
        avg_growth = sum(
            data["growth_rate"] for data in self._topic_data.values()
        ) / max(len(self._topic_data), 1)
        
        market_health = "growing" if avg_growth > 5 else "stable" if avg_growth > -5 else "declining"
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "market_health": market_health,
            "avg_topic_growth": f"{avg_growth:+.1f}%",
            "total_topics_tracked": len(self._topic_data),
            "trending_topics": [
                {
                    "topic": t.topic,
                    "growth": f"{t.growth_rate:+.1f}%",
                    "saturation": t.saturation_level
                }
                for t in trending_topics
            ],
            "content_opportunities": [
                {
                    "topic": g.topic,
                    "opportunity_score": g.opportunity_score,
                    "demand": g.demand_score,
                    "supply": g.supply_score
                }
                for g in content_gaps
            ],
            "emerging_creators": [
                {"creator_id": c_id, "growth": f"{rate:+.1f}%"}
                for c_id, rate in emerging_creators
            ]
        }
    
    def _calculate_saturation(self, video_count: int) -> str:
        """Calculate saturation level from video count"""
        if video_count > 1000:
            return "high"
        elif video_count > 500:
            return "medium"
        else:
            return "low"


# Global instance
market_intelligence = MarketIntelligence()

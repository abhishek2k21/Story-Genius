"""
Trend Weaver - Natural Trending Topic Integration
Integrates trending topics into content without feeling forced.
"""
from typing import List, Optional, Dict
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Trend:
    """Represents a trending topic"""
    name: str
    category: str
    region: str
    growth_rate: float  # How fast it's trending
    relevance_score: float  # 0-1, how relevant to video topic


class TrendWeaver:
    """Naturally integrates trending topics into video content"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service or self._get_default_llm()
    
    def _get_default_llm(self):
        """Get default LLM service"""
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def fetch_current_trends(
        self,
        platform: str = "youtube_shorts",
        region: str = "US",
        limit: int = 10
    ) -> List[Trend]:
        """
        Fetch current trending topics
        
        Note: This is a placeholder. In production, integrate with:
        - Google Trends API
        - YouTube Data API
        - Twitter/X Trends API
        
        Args:
            platform: Platform to get trends for
            region: Geographic region
            limit: Maximum trends to return
        
        Returns:
            List of trending topics
        """
        # TODO: Implement actual API integration
        # For now, return mock trends
        mock_trends = [
            Trend(
                name="#morningroutine",
                category="lifestyle",
                region=region,
                growth_rate=0.8,
                relevance_score=0.0  # Will calculate per topic
            ),
            Trend(
                name="coffee recipes",
                category="food",
                region=region,
                growth_rate=0.6,
                relevance_score=0.0
            ),
            Trend(
                name="AI tools",
                category="technology",
                region=region,
                growth_rate=0.9,
                relevance_score=0.0
            )
        ]
        
        logger.info(f"Fetched {len(mock_trends)} trends for {platform}/{region}")
        return mock_trends[:limit]
    
    def find_relevant_trends(
        self,
        topic: str,
        trends: List[Trend],
        min_relevance: float = 0.5
    ) -> List[Trend]:
        """
        Find trends semantically related to video topic
        
        Args:
            topic: The video topic
            trends: List of available trends
            min_relevance: Minimum relevance score (0-1)
        
        Returns:
            Filtered list of relevant trends
        """
        relevant_trends = []
        
        for trend in trends:
            # Calculate relevance using simple word overlap
            # TODO: Enhance with embeddings for better semantic matching
            relevance = self._calculate_relevance(topic, trend.name)
            trend.relevance_score = relevance
            
            if relevance >= min_relevance:
                relevant_trends.append(trend)
        
        # Sort by relevance * growth_rate
        relevant_trends.sort(
            key=lambda t: t.relevance_score * t.growth_rate,
            reverse=True
        )
        
        logger.info(
            f"Found {len(relevant_trends)} relevant trends for '{topic}' "
            f"(min relevance: {min_relevance})"
        )
        
        return relevant_trends
    
    def _calculate_relevance(self, topic: str, trend: str) -> float:
        """Simple relevance calculation using word overlap"""
        topic_words = set(topic.lower().split())
        trend_words = set(trend.lower().replace("#", "").split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for'}
        topic_words -= stop_words
        trend_words -= stop_words
        
        if not topic_words or not trend_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(topic_words & trend_words)
        union = len(topic_words | trend_words)
        
        return intersection / union if union > 0 else 0.0
    
    def should_use_trend(
        self,
        topic: str,
        trend: Trend,
        min_relevance: float = 0.5,
        min_growth: float = 0.3
    ) -> bool:
        """
        Determine if trend should be integrated
        
        Args:
            topic: Video topic
            trend: Trend to evaluate
            min_relevance: Minimum relevance threshold
            min_growth: Minimum growth rate threshold
        
        Returns:
            True if trend should be used
        """
        # Check relevance
        if trend.relevance_score < min_relevance:
            logger.debug(f"Trend '{trend.name}' not relevant enough ({trend.relevance_score:.2f})")
            return False
        
        # Check if still growing (not declining)
        if trend.growth_rate < min_growth:
            logger.debug(f"Trend '{trend.name}' not growing fast enough ({trend.growth_rate:.2f})")
            return False
        
        # Passed filters
        logger.info(f"Trend '{trend.name}' approved for integration")
        return True
    
    def weave_trend(
        self,
        narration: str,
        trend: Trend,
        position: str = "hook"
    ) -> str:
        """
        Naturally integrate trend into narration
        
        Args:
            narration: Original narration text
            trend: Trend to weave in
            position: Where to integrate ("hook", "mid", "end")
        
        Returns:
            Narration with trend naturally woven in
        """
        prompt = f"""
Rewrite this text to naturally include the trending topic "{trend.name}":

Original: "{narration}"

Position: {position} (beginning/middle/end of video)

Requirements:
- Make it feel organic, NOT forced
- Don't lose the original message
- Keep similar length
- Be conversational and natural
- If it doesn't fit naturally, return the original text

Examples of natural integration:
- "While everyone's posting their #morningroutine..."
- "Speaking of coffee recipes trending right now..."
- "With all the AI tools out there..."

Return ONLY the rewritten text.
"""
        
        try:
            woven = self.llm_service.generate_text(prompt).strip()
            
            # Sanity check: if significantly longer, might be hallucinating
            if len(woven) > len(narration) * 1.5:
                logger.warning("Woven text too long, using original")
                return narration
            
            logger.info(f"Successfully wove trend '{trend.name}' into narration")
            return woven
            
        except Exception as e:
            logger.error(f"Trend weaving failed: {e}")
            return narration  # Return original if failed
    
    def integrate_trends_into_story(
        self,
        scenes: List[Dict],
        topic: str,
        platform: str = "youtube_shorts",
        region: str = "US"
    ) -> List[Dict]:
        """
        Integrate trending topics into story scenes
        
        Args:
            scenes: List of scene dictionaries
            topic: Video topic
            platform: Platform for trends
            region: Geographic region
        
        Returns:
            Scenes with trends integrated (if appropriate)
        """
        if not scenes:
            return scenes
        
        # Fetch current trends
        trends = self.fetch_current_trends(platform, region)
        
        # Find relevant trends
        relevant = self.find_relevant_trends(topic, trends, min_relevance=0.4)
        
        if not relevant:
            logger.info("No relevant trends found")
            return scenes
        
        # Use top trend
        top_trend = relevant[0]
        
        # Check if we should use it
        if not self.should_use_trend(topic, top_trend):
            logger.info("Top trend not suitable for integration")
            return scenes
        
        # Weave into hook (first scene)
        hook_scene = scenes[0]
        original_narration = hook_scene.get("narration", "")
        
        woven_narration = self.weave_trend(
            original_narration,
            top_trend,
            position="hook"
        )
        
        hook_scene["narration"] = woven_narration
        hook_scene["trend_integrated"] = top_trend.name
        
        logger.info(f"Integrated trend '{top_trend.name}' into hook")
        
        return scenes

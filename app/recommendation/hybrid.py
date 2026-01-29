"""
Hybrid Recommendation System
Combines collaborative and content-based filtering.
"""
from typing import List, Tuple, Dict
from collections import defaultdict

from app.recommendation.collaborative import collaborative_filter, CollaborativeFiltering
from app.recommendation.content_based import content_based_filter, ContentBasedFiltering
from app.recommendation.engine import recommendation_engine, RecommendationEngine
from app.core.logging import get_logger

logger = get_logger(__name__)


class HybridRecommendationSystem:
    """
    Hybrid recommendation system combining multiple strategies.
    
    Strategies:
    - Collaborative filtering (60%)
    - Content-based filtering (40%)
    - Vector similarity (embedding-based)
    """
    
    def __init__(
        self,
        collaborative: CollaborativeFiltering,
        content_based: ContentBasedFiltering,
        engine: RecommendationEngine
    ):
        self.collaborative = collaborative
        self.content_based = content_based
        self.engine = engine
        
        # Default strategy weights
        self.weights = {
            "collaborative": 0.6,
            "content": 0.4
        }
        
        logger.info("HybridRecommendationSystem initialized")
    
    def recommend(
        self,
        user_id: str,
        limit: int = 20,
        strategy: str = "hybrid"
    ) -> List[str]:
        """
        Generate personalized recommendations.
        
        Args:
            user_id: User ID
            limit: Number of recommendations
            strategy: Strategy (collaborative, content, hybrid)
        
        Returns:
            List of recommended video IDs
        """
        if strategy == "collaborative":
            return self._collaborative_only(user_id, limit)
        
        elif strategy == "content":
            return self._content_only(user_id, limit)
        
        else:  # hybrid
            return self._hybrid(user_id, limit)
    
    def _collaborative_only(self, user_id: str, limit: int) -> List[str]:
        """Pure collaborative filtering"""
        recommendations = self.collaborative.recommend(user_id, limit)
        return [video_id for video_id, _ in recommendations]
    
    def _content_only(self, user_id: str, limit: int) -> List[str]:
        """Pure content-based filtering"""
        # Get user's liked videos (high interaction score)
        user_interactions = self.collaborative.interactions.get(user_id, {})
        
        # Get top liked videos
        liked_videos = sorted(
            user_interactions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        liked_video_ids = [video_id for video_id, _ in liked_videos]
        
        # Get content-based recommendations
        recommendations = self.content_based.recommend_for_user(
            liked_video_ids,
            limit
        )
        
        return [video_id for video_id, _ in recommendations]
    
    def _hybrid(self, user_id: str, limit: int) -> List[str]:
        """
        Hybrid strategy combining collaborative and content-based.
        
        Weights:
        - 60% collaborative filtering
        - 40% content-based filtering
        """
        # Get collaborative recommendations
        collab_recs = self.collaborative.recommend(user_id, limit=30)
        
        # Get content-based recommendations
        user_interactions = self.collaborative.interactions.get(user_id, {})
        liked_videos = sorted(
            user_interactions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        liked_video_ids = [video_id for video_id, _ in liked_videos]
        
        content_recs = self.content_based.recommend_for_user(
            liked_video_ids,
            limit=30
        )
        
        # Merge recommendations with weights
        merged_scores = defaultdict(float)
        
        # Add collaborative scores (60% weight)
        for video_id, score in collab_recs:
            merged_scores[video_id] += score * self.weights["collaborative"]
        
        # Add content-based scores (40% weight)
        for video_id, score in content_recs:
            merged_scores[video_id] += score * self.weights["content"]
        
        # Sort by merged score
        sorted_recommendations = sorted(
            merged_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(
            f"Generated {limit} hybrid recommendations for {user_id} "
            f"(collab: {len(collab_recs)}, content: {len(content_recs)})"
        )
        
        return [video_id for video_id, _ in sorted_recommendations[:limit]]
    
    def recommend_similar(self, video_id: str, limit: int = 10) -> List[str]:
        """
        Get similar videos ("more like this").
        
        Uses both content similarity and embedding similarity.
        """
        # Content-based similarity
        content_similar = self.content_based.find_similar(video_id, limit=15)
        
        # Embedding-based similarity
        embedding_similar = self.engine.find_similar(video_id, limit=15)
        
        # Merge (50/50 weight)
        merged_scores = defaultdict(float)
        
        for vid_id, score in content_similar:
            merged_scores[vid_id] += score * 0.5
        
        for vid_id, score in embedding_similar:
            merged_scores[vid_id] += score * 0.5
        
        # Sort and return
        sorted_similar = sorted(
            merged_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [video_id for video_id, _ in sorted_similar[:limit]]
    
    def get_popular_videos(self, limit: int = 20) -> List[str]:
        """Get popular videos across all users"""
        popular = self.collaborative.get_popular_videos(limit)
        return [video_id for video_id, _ in popular]


# Global instance
hybrid_recommender = HybridRecommendationSystem(
    collaborative=collaborative_filter,
    content_based=content_based_filter,
    engine=recommendation_engine
)

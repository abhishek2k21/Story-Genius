"""
Collaborative Filtering
User-based collaborative filtering for recommendations.
"""
from typing import List, Tuple, Dict, Set
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import math

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserInteraction:
    """User-video interaction"""
    user_id: str
    video_id: str
    interaction_type: str  # view, like, share, watch_complete
    weight: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CollaborativeFiltering:
    """
    Collaborative filtering recommendation system.
    Finds users with similar tastes and recommends videos they liked.
    """
    
    # Interaction weights
    WEIGHTS = {
        "view": 1.0,
        "like": 2.0,
        "share": 3.0,
        "watch_complete": 2.5,
        "watch_partial": 0.5
    }
    
    def __init__(self):
        # User-item interaction matrix: {user_id: {video_id: score}}
        self.interactions: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        
        # Interaction history
        self.history: List[UserInteraction] = []
        
        logger.info("CollaborativeFiltering initialized")
    
    def track_interaction(
        self,
        user_id: str,
        video_id: str,
        interaction_type: str
    ):
        """
        Track user-video interaction.
        
        Args:
            user_id: User ID
            video_id: Video ID
            interaction_type: Type of interaction (view, like, share, etc.)
        """
        weight = self.WEIGHTS.get(interaction_type, 1.0)
        
        # Update interaction matrix
        self.interactions[user_id][video_id] += weight
        
        # Record interaction
        interaction = UserInteraction(
            user_id=user_id,
            video_id=video_id,
            interaction_type=interaction_type,
            weight=weight
        )
        self.history.append(interaction)
        
        logger.debug(
            f"Tracked interaction: user={user_id}, video={video_id}, "
            f"type={interaction_type}, weight={weight}"
        )
    
    def calculate_user_similarity(
        self,
        user1_id: str,
        user2_id: str
    ) -> float:
        """
        Calculate similarity between two users using cosine similarity.
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
        
        Returns:
            Similarity score [0, 1]
        """
        user1_vector = self.interactions[user1_id]
        user2_vector = self.interactions[user2_id]
        
        # Find common videos
        common_videos = set(user1_vector.keys()) & set(user2_vector.keys())
        
        if not common_videos:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(
            user1_vector[video_id] * user2_vector[video_id]
            for video_id in common_videos
        )
        
        norm1 = math.sqrt(sum(score ** 2 for score in user1_vector.values()))
        norm2 = math.sqrt(sum(score ** 2 for score in user2_vector.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def find_similar_users(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find users with similar interaction patterns.
        
        Args:
            user_id: Target user ID
            limit: Number of similar users to return
        
        Returns:
            List of (user_id, similarity_score) tuples
        """
        if user_id not in self.interactions:
            logger.warning(f"User not found: {user_id}")
            return []
        
        similarities = []
        
        for other_user_id in self.interactions:
            if other_user_id == user_id:
                continue
            
            similarity = self.calculate_user_similarity(user_id, other_user_id)
            
            if similarity > 0:
                similarities.append((other_user_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(similarities[:limit])} similar users for {user_id}")
        
        return similarities[:limit]
    
    def recommend(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Generate collaborative filtering recommendations.
        
        Algorithm:
        1. Find similar users
        2. Get videos liked by similar users
        3. Weight by user similarity
        4. Exclude videos already watched
        
        Args:
            user_id: User ID
            limit: Number of recommendations
        
        Returns:
            List of (video_id, recommendation_score) tuples
        """
        # Find similar users
        similar_users = self.find_similar_users(user_id, limit=10)
        
        if not similar_users:
            logger.warning(f"No similar users found for {user_id}")
            return []
        
        # Get videos already watched by target user
        watched_videos = set(self.interactions[user_id].keys())
        
        # Collect candidate videos from similar users
        candidate_videos: Dict[str, float] = defaultdict(float)
        
        for similar_user_id, similarity in similar_users:
            for video_id, score in self.interactions[similar_user_id].items():
                if video_id not in watched_videos:
                    # Weight by user similarity and interaction score
                    candidate_videos[video_id] += score * similarity
        
        # Sort by recommendation score
        recommendations = sorted(
            candidate_videos.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(
            f"Generated {len(recommendations[:limit])} collaborative "
            f"recommendations for {user_id}"
        )
        
        return recommendations[:limit]
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user interaction statistics"""
        if user_id not in self.interactions:
            return {
                "total_interactions": 0,
                "unique_videos": 0,
                "total_score": 0.0
            }
        
        user_vector = self.interactions[user_id]
        
        return {
            "total_interactions": len(user_vector),
            "unique_videos": len(user_vector),
            "total_score": sum(user_vector.values())
        }
    
    def get_popular_videos(self, limit: int = 20) -> List[Tuple[str, float]]:
        """
        Get most popular videos across all users.
        
        Args:
            limit: Number of videos to return
        
        Returns:
            List of (video_id, popularity_score) tuples
        """
        video_scores: Dict[str, float] = defaultdict(float)
        
        # Aggregate scores across all users
        for user_vector in self.interactions.values():
            for video_id, score in user_vector.items():
                video_scores[video_id] += score
        
        # Sort by popularity
        popular = sorted(
            video_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return popular[:limit]


# Global instance
collaborative_filter = CollaborativeFiltering()

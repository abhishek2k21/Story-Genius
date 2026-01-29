"""
Content-Based Filtering
Recommends similar videos based on content features.
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VideoFeatures:
    """Video content features"""
    id: str
    genre: str
    tone: str  # humorous, serious, dramatic, educational, etc.
    pacing: str  # fast, medium, slow
    themes: List[str]
    duration: float
    quality_score: float


class ContentBasedFiltering:
    """
    Content-based recommendation system.
    Recommends videos similar to those the user has liked.
    """
    
    def __init__(self):
        self._videos: Dict[str, VideoFeatures] = {}
        logger.info("ContentBasedFiltering initialized")
    
    def add_video(self, video: VideoFeatures):
        """Add video to the system"""
        self._videos[video.id] = video
        logger.debug(f"Added video: {video.id}")
    
    def extract_features(self, video: VideoFeatures) -> Dict:
        """Extract features from video"""
        return {
            "genre": video.genre,
            "tone": video.tone,
            "pacing": video.pacing,
            "themes": set(video.themes),
            "duration": video.duration,
            "quality": video.quality_score
        }
    
    def calculate_similarity(
        self,
        video1_id: str,
        video2_id: str
    ) -> float:
        """
        Calculate content similarity between two videos.
        
        Uses weighted feature comparison:
        - Genre: 30%
        - Tone: 20%
        - Pacing: 15%
        - Themes: 25%
        - Duration: 10%
        
        Args:
            video1_id: First video ID
            video2_id: Second video ID
        
        Returns:
            Similarity score [0, 1]
        """
        video1 = self._videos.get(video1_id)
        video2 = self._videos.get(video2_id)
        
        if not video1 or not video2:
            return 0.0
        
        features1 = self.extract_features(video1)
        features2 = self.extract_features(video2)
        
        similarity = 0.0
        
        # Genre similarity (30%)
        if features1["genre"] == features2["genre"]:
            similarity += 0.3
        
        # Tone similarity (20%)
        if features1["tone"] == features2["tone"]:
            similarity += 0.2
        
        # Pacing similarity (15%)
        if features1["pacing"] == features2["pacing"]:
            similarity += 0.15
        
        # Theme overlap (25%)
        theme1 = features1["themes"]
        theme2 = features2["themes"]
        
        if theme1 and theme2:
            overlap = len(theme1 & theme2)
            union = len(theme1 | theme2)
            theme_similarity = overlap / union if union > 0 else 0
            similarity += 0.25 * theme_similarity
        
        # Duration similarity (10%)
        duration_diff = abs(features1["duration"] - features2["duration"])
        # Normalize: 0 diff = 1.0 similarity, 300s diff = 0.0 similarity
        duration_similarity = max(0, 1 - (duration_diff / 300))
        similarity += 0.1 * duration_similarity
        
        return round(similarity, 3)
    
    def find_similar(
        self,
        video_id: str,
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find videos similar to the given video ("more like this").
        
        Args:
            video_id: Source video ID
            limit: Number of similar videos to return
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of (video_id, similarity_score) tuples
        """
        if video_id not in self._videos:
            logger.warning(f"Video not found: {video_id}")
            return []
        
        similarities = []
        
        for other_video_id in self._videos:
            if other_video_id == video_id:
                continue
            
            similarity = self.calculate_similarity(video_id, other_video_id)
            
            if similarity >= min_similarity:
                similarities.append((other_video_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(
            f"Found {len(similarities[:limit])} similar videos for {video_id} "
            f"(min_sim={min_similarity})"
        )
        
        return similarities[:limit]
    
    def recommend_for_user(
        self,
        liked_video_ids: List[str],
        limit: int = 20,
        diversity_weight: float = 0.2
    ) -> List[Tuple[str, float]]:
        """
        Recommend videos based on user's liked videos.
        
        Args:
            liked_video_ids: Videos the user has liked
            limit: Number of recommendations
            diversity_weight: Weight for diversity (0-1)
        
        Returns:
            List of (video_id, recommendation_score) tuples
        """
        if not liked_video_ids:
            return []
        
        # Find similar videos for each liked video
        candidate_scores: Dict[str, float] = defaultdict(float)
        candidate_counts: Dict[str, int] = defaultdict(int)
        
        for liked_video_id in liked_video_ids:
            similar = self.find_similar(liked_video_id, limit=20)
            
            for video_id, similarity in similar:
                if video_id not in liked_video_ids:
                    candidate_scores[video_id] += similarity
                    candidate_counts[video_id] += 1
        
        # Average scores
        averaged_scores = {
            video_id: score / candidate_counts[video_id]
            for video_id, score in candidate_scores.items()
        }
        
        # Apply diversity constraint
        if diversity_weight > 0:
            averaged_scores = self._apply_diversity(
                averaged_scores,
                liked_video_ids,
                diversity_weight
            )
        
        # Sort by score
        recommendations = sorted(
            averaged_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(
            f"Generated {len(recommendations[:limit])} content-based "
            f"recommendations from {len(liked_video_ids)} liked videos"
        )
        
        return recommendations[:limit]
    
    def _apply_diversity(
        self,
        scores: Dict[str, float],
        reference_video_ids: List[str],
        diversity_weight: float
    ) -> Dict[str, float]:
        """
        Apply diversity constraint to avoid filter bubbles.
        
        Penalizes videos too similar to what user has already seen.
        """
        # Get genres of reference videos
        reference_genres = set()
        for video_id in reference_video_ids:
            if video_id in self._videos:
                reference_genres.add(self._videos[video_id].genre)
        
        # Adjust scores
        adjusted_scores = {}
        
        for video_id, score in scores.items():
            if video_id not in self._videos:
                adjusted_scores[video_id] = score
                continue
            
            video = self._videos[video_id]
            
            # Penalize if same genre as reference
            penalty = 1.0
            if video.genre in reference_genres:
                penalty = 1.0 - (diversity_weight * 0.5)
            
            adjusted_scores[video_id] = score * penalty
        
        return adjusted_scores
    
    def get_video(self, video_id: str) -> Optional[VideoFeatures]:
        """Get video features"""
        return self._videos.get(video_id)


# Global instance
content_based_filter = ContentBasedFiltering()

"""
Recommendation Engine
Handles video embeddings, similarity search, and recommendation generation.
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VideoMetadata:
    """Video metadata for recommendations"""
    id: str
    title: str
    description: str
    tags: List[str]
    genre: str
    duration: float  # seconds
    quality_score: float
    engagement: float
    created_at: str


class VideoEmbeddingGenerator:
    """Generate embeddings for videos"""
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100, stop_words='english')
        self._is_fitted = False
        logger.info("VideoEmbeddingGenerator initialized")
    
    def fit(self, videos: List[Video Metadata]):
        """Fit TF-IDF vectorizer on video corpus"""
        texts = [
            f"{v.title} {v.description} {' '.join(v.tags)}"
            for v in videos
        ]
        
        self.tfidf.fit(texts)
        self._is_fitted = True
        
        logger.info(f"Fitted TF-IDF on {len(videos)} videos")
    
    def generate_embedding(self, video: VideoMetadata) -> np.ndarray:
        """
        Generate embedding vector for a video.
        
        Combines:
        - Text embedding (TF-IDF)
        - Metadata features (duration, quality, engagement)
        
        Returns:
            Embedding vector
        """
        if not self._is_fitted:
            raise ValueError("Vectorizer not fitted. Call fit() first.")
        
        # Text embedding
        text = f"{video.title} {video.description} {' '.join(video.tags)}"
        text_embedding = self.tfidf.transform([text]).toarray()[0]
        
        # Metadata features (normalized)
        metadata_features = np.array([
            video.duration / 600,  # Normalize to [0, 1] assuming max 10 min
            video.quality_score / 100,
            video.engagement / 100
        ])
        
        # Combine
        embedding = np.concatenate([text_embedding, metadata_features])
        
        return embedding


class VectorStore:
    """Simple in-memory vector store for similarity search"""
    
    def __init__(self):
        self.embeddings: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, VideoMetadata] = {}
        logger.info("VectorStore initialized")
    
    def add(self, video_id: str, embedding: np.ndarray, metadata: VideoMetadata):
        """Add vector to store"""
        self.embeddings[video_id] = embedding
        self.metadata[video_id] = metadata
        logger.debug(f"Added vector for video: {video_id}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors using cosine similarity.
        
        Args:
            query_embedding: Query vector
            limit: Number of results
            exclude_ids: Video IDs to exclude from results
        
        Returns:
            List of (video_id, similarity_score) tuples
        """
        if not self.embeddings:
            return []
        
        exclude_ids = exclude_ids or []
        similarities = []
        
        for video_id, embedding in self.embeddings.items():
            if video_id in exclude_ids:
                continue
            
            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            similarities.append((video_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def get(self, video_id: str) -> Tuple[np.ndarray, VideoMetadata]:
        """Get embedding and metadata for a video"""
        return self.embeddings.get(video_id), self.metadata.get(video_id)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def size(self) -> int:
        """Get number of vectors in store"""
        return len(self.embeddings)


class RecommendationEngine:
    """Main recommendation engine"""
    
    def __init__(self):
        self.embedding_generator = VideoEmbeddingGenerator()
        self.vector_store = VectorStore()
        self._videos: Dict[str, VideoMetadata] = {}
        logger.info("RecommendationEngine initialized")
    
    def index_videos(self, videos: List[VideoMetadata]):
        """
        Index videos for recommendation.
        
        Args:
            videos: List of videos to index
        """
        # Fit TF-IDF
        self.embedding_generator.fit(videos)
        
        # Generate and store embeddings
        for video in videos:
            embedding = self.embedding_generator.generate_embedding(video)
            self.vector_store.add(video.id, embedding, video)
            self._videos[video.id] = video
        
        logger.info(f"Indexed {len(videos)} videos")
    
    def add_video(self, video: VideoMetadata):
        """Add a single video to the index"""
        embedding = self.embedding_generator.generate_embedding(video)
        self.vector_store.add(video.id, embedding, video)
        self._videos[video.id] = video
        
        logger.debug(f"Added video to index: {video.id}")
    
    def find_similar(
        self,
        video_id: str,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find videos similar to the given video.
        
        Args:
            video_id: Source video ID
            limit: Number of similar videos to return
        
        Returns:
            List of (video_id, similarity_score) tuples
        """
        embedding, metadata = self.vector_store.get(video_id)
        
        if embedding is None:
            logger.warning(f"Video not found in index: {video_id}")
            return []
        
        # Search for similar vectors (exclude source video)
        similar = self.vector_store.search(
            query_embedding=embedding,
            limit=limit + 1,  # +1 to account for excluding source
            exclude_ids=[video_id]
        )
        
        logger.info(f"Found {len(similar)} similar videos for {video_id}")
        
        return similar[:limit]
    
    def recommend_for_user_based_on_history(
        self,
        watched_video_ids: List[str],
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Recommend videos based on user's watch history.
        
        Args:
            watched_video_ids: List of video IDs user has watched
            limit: Number of recommendations
        
        Returns:
            List of (video_id, recommendation_score) tuples
        """
        if not watched_video_ids:
            return []
        
        # Get embeddings for watched videos
        watched_embeddings = []
        for video_id in watched_video_ids:
            embedding, _ = self.vector_store.get(video_id)
            if embedding is not None:
                watched_embeddings.append(embedding)
        
        if not watched_embeddings:
            return []
        
        # Create composite query vector (average of watched videos)
        query_embedding = np.mean(watched_embeddings, axis=0)
        
        # Search for similar videos
        recommendations = self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit + len(watched_video_ids),
            exclude_ids=watched_video_ids
        )
        
        logger.info(
            f"Generated {len(recommendations)} recommendations "
            f"based on {len(watched_video_ids)} watched videos"
        )
        
        return recommendations[:limit]
    
    def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Get video metadata"""
        return self._videos.get(video_id)


# Global instance
recommendation_engine = RecommendationEngine()

"""
Recommendation Module Initialization
"""
from app.recommendation.engine import (
    VideoMetadata,
    VideoEmbeddingGenerator,
    VectorStore,
    RecommendationEngine,
    recommendation_engine
)
from app.recommendation.collaborative import (
    UserInteraction,
    CollaborativeFiltering,
    collaborative_filter
)
from app.recommendation.content_based import (
    VideoFeatures,
    ContentBasedFiltering,
    content_based_filter
)
from app.recommendation.hybrid import (
    HybridRecommendationSystem,
    hybrid_recommender
)

__all__ = [
    'VideoMetadata',
    'VideoEmbeddingGenerator',
    'VectorStore',
    'RecommendationEngine',
    'recommendation_engine',
    'UserInteraction',
    'CollaborativeFiltering',
    'collaborative_filter',
    'VideoFeatures',
    'ContentBasedFiltering',
    'content_based_filter',
    'HybridRecommendationSystem',
    'hybrid_recommender'
]

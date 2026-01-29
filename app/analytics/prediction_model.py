"""
Performance Prediction Model
ML-based prediction of video performance.
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VideoParameters:
    """Video generation parameters"""
    hook_quality: float  # 0-100
    pacing: str  # fast, medium, slow
    tone: str  # humorous, serious, dramatic, educational
    duration: float  # seconds
    genre: str
    tag_count: int
    has_music: bool
    has_effects: bool


@dataclass
class PerformancePrediction:
    """Predicted performance metrics"""
    predicted_views: int
    predicted_engagement: float  # percentage
    predicted_quality: float  # 0-100
    confidence: float  # 0-1


class PerformancePredictionModel:
    """
    ML model to predict video performance based on generation parameters.
    
    Uses Random Forest Regression to predict:
    - Views
    - Engagement rate
    - Quality score
    """
    
    def __init__(self):
        self.models = {
            "views": RandomForestRegressor(n_estimators=100, random_state=42),
            "engagement": RandomForestRegressor(n_estimators=100, random_state=42),
            "quality": RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        self.label_encoders = {
            "pacing": LabelEncoder(),
            "tone": LabelEncoder(),
            "genre": LabelEncoder()
        }
        
        self.is_trained = False
        self.feature_importance = {}
        
        logger.info("PerformancePredictionModel initialized")
    
    def _encode_features(self, params: VideoParameters) -> np.ndarray:
        """
        Encode video parameters as feature vector.
        
        Features:
        - hook_quality (numeric)
        - pacing (encoded)
        - tone (encoded)
        - duration (numeric)
        - genre (encoded)
        - tag_count (numeric)
        - has_music (binary)
        - has_effects (binary)
        """
        features = [
            params.hook_quality,
            self.label_encoders["pacing"].transform([params.pacing])[0],
            self.label_encoders["tone"].transform([params.tone])[0],
            params.duration,
            self.label_encoders["genre"].transform([params.genre])[0],
            params.tag_count,
            1 if params.has_music else 0,
            1 if params.has_effects else 0
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(
        self,
        training_data: List[Tuple[VideoParameters, Dict]]
    ):
        """
        Train the model on historical data.
        
        Args:
            training_data: List of (parameters, actual_performance) tuples
        """
        if len(training_data) < 10:
            logger.warning("Training data too small, need at least 10 samples")
            return
        
        # Fit label encoders
        pacings = [p.pacing for p, _ in training_data]
        tones = [p.tone for p, _ in training_data]
        genres = [p.genre for p, _ in training_data]
        
        self.label_encoders["pacing"].fit(pacings)
        self.label_encoders["tone"].fit(tones)
        self.label_encoders["genre"].fit(genres)
        
        # Prepare features and targets
        X = np.array([
            self._encode_features(params).flatten()
            for params, _ in training_data
        ])
        
        y_views = np.array([perf["views"] for _, perf in training_data])
        y_engagement = np.array([perf["engagement"] for _, perf in training_data])
        y_quality = np.array([perf["quality"] for _, perf in training_data])
        
        # Train models
        logger.info(f"Training models on {len(training_data)} samples...")
        
        self.models["views"].fit(X, y_views)
        self.models["engagement"].fit(X, y_engagement)
        self.models["quality"].fit(X, y_quality)
        
        # Evaluate with cross-validation
        views_scores = cross_val_score(
            self.models["views"], X, y_views, cv=3, scoring='r2'
        )
        engagement_scores = cross_val_score(
            self.models["engagement"], X, y_engagement, cv=3, scoring='r2'
        )
        quality_scores = cross_val_score(
            self.models["quality"], X, y_quality, cv=3, scoring='r2'
        )
        
        logger.info(
            f"Model trained. R² scores: "
            f"views={views_scores.mean():.3f}, "
            f"engagement={engagement_scores.mean():.3f}, "
            f"quality={quality_scores.mean():.3f}"
        )
        
        # Store feature importance
        feature_names = [
            "hook_quality", "pacing", "tone", "duration",
            "genre", "tag_count", "has_music", "has_effects"
        ]
        
        self.feature_importance = {
            "views": dict(zip(
                feature_names,
                self.models["views"].feature_importances_
            )),
            "engagement": dict(zip(
                feature_names,
                self.models["engagement"].feature_importances_
            )),
            "quality": dict(zip(
                feature_names,
                self.models["quality"].feature_importances_
            ))
        }
        
        self.is_trained = True
    
    def predict(self, params: VideoParameters) -> PerformancePrediction:
        """
        Predict performance for given parameters.
        
        Args:
            params: Video generation parameters
        
        Returns:
            Performance prediction
        """
        if not self.is_trained:
            # Return default prediction if not trained
            logger.warning("Model not trained, returning default prediction")
            return PerformancePrediction(
                predicted_views=5000,
                predicted_engagement=65.0,
                predicted_quality=75.0,
                confidence=0.5
            )
        
        # Encode features
        X = self._encode_features(params)
        
        # Predict
        views = int(self.models["views"].predict(X)[0])
        engagement = float(self.models["engagement"].predict(X)[0])
        quality = float(self.models["quality"].predict(X)[0])
        
        # Calculate confidence (use R² scores as proxy)
        # In production, use prediction intervals
        confidence = 0.75  # Placeholder
        
        prediction = PerformancePrediction(
            predicted_views=max(0, views),
            predicted_engagement=max(0, min(100, engagement)),
            predicted_quality=max(0, min(100, quality)),
            confidence=confidence
        )
        
        logger.info(
            f"Predicted performance: views={prediction.predicted_views}, "
            f"engagement={prediction.predicted_engagement:.1f}%, "
            f"quality={prediction.predicted_quality:.1f}"
        )
        
        return prediction
    
    def get_feature_importance(self, target: str = "views") -> Dict[str, float]:
        """
        Get feature importance for a target metric.
        
        Args:
            target: Target metric (views, engagement, quality)
        
        Returns:
            Dict of feature importances
        """
        if not self.is_trained:
            return {}
        
        return self.feature_importance.get(target, {})
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                "models": self.models,
                "label_encoders": self.label_encoders,
                "feature_importance": self.feature_importance
            }, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.models = data["models"]
            self.label_encoders = data["label_encoders"]
            self.feature_importance = data["feature_importance"]
            self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")


# Global instance
prediction_model = PerformancePredictionModel()

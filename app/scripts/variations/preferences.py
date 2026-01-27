"""
User Preferences
Learn preferences from selection history.
"""
from typing import Dict, List
from datetime import datetime
from collections import Counter
import threading

from app.scripts.variations.models import (
    VariationHistory, UserPreferences, SelectionType
)


class PreferenceService:
    """Learn and apply user preferences"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history: Dict[str, List[VariationHistory]] = {}  # user_id -> history
            cls._instance._preferences: Dict[str, UserPreferences] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def record_selection(
        self,
        user_id: str,
        request_id: str,
        topic: str,
        category: str,
        variation_count: int,
        selected_index: int,
        selected_score: float,
        average_score: float,
        selection_type: SelectionType,
        hook_style: str = ""
    ) -> VariationHistory:
        """Record selection in history"""
        import uuid
        
        history = VariationHistory(
            history_id=str(uuid.uuid4()),
            user_id=user_id,
            request_id=request_id,
            topic=topic,
            category=category,
            variation_count=variation_count,
            selected_index=selected_index,
            selected_score=selected_score,
            average_score=average_score,
            selection_type=selection_type,
            hook_style=hook_style
        )
        
        if user_id not in self._history:
            self._history[user_id] = []
        
        with self._lock:
            self._history[user_id].append(history)
        
        # Update preferences
        self._update_preferences(user_id)
        
        return history
    
    def get_history(self, user_id: str, limit: int = 50) -> List[VariationHistory]:
        """Get user's selection history"""
        history = self._history.get(user_id, [])
        return sorted(history, key=lambda h: h.created_at, reverse=True)[:limit]
    
    def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences"""
        if user_id not in self._preferences:
            self._preferences[user_id] = UserPreferences(user_id=user_id)
        return self._preferences[user_id]
    
    def _update_preferences(self, user_id: str) -> None:
        """Update preferences from history"""
        history = self._history.get(user_id, [])
        
        if not history:
            return
        
        prefs = self.get_preferences(user_id)
        
        # Count hook styles
        hook_styles = [h.hook_style for h in history if h.hook_style]
        if hook_styles:
            style_counts = Counter(hook_styles)
            prefs.preferred_hook_styles = [s for s, _ in style_counts.most_common(3)]
        
        # Calculate minimum score threshold
        selected_scores = [h.selected_score for h in history]
        if selected_scores:
            prefs.minimum_score_threshold = sum(selected_scores) / len(selected_scores)
        
        # Calculate edit tendency (would need modification data)
        prefs.edit_tendency = 0.0
        
        prefs.last_updated = datetime.utcnow()
    
    def get_analytics(self, user_id: str) -> Dict:
        """Get variation analytics for user"""
        history = self._history.get(user_id, [])
        
        if not history:
            return {
                "total_variations": 0,
                "selections": 0,
                "auto_selections": 0,
                "manual_selections": 0,
                "avg_selected_score": 0,
                "improvement_from_variations": 0
            }
        
        auto = sum(1 for h in history if h.selection_type == SelectionType.AUTO)
        manual = sum(1 for h in history if h.selection_type == SelectionType.MANUAL)
        
        avg_selected = sum(h.selected_score for h in history) / len(history)
        avg_average = sum(h.average_score for h in history) / len(history)
        
        return {
            "total_variations": sum(h.variation_count for h in history),
            "selections": len(history),
            "auto_selections": auto,
            "manual_selections": manual,
            "avg_selected_score": round(avg_selected, 1),
            "avg_score_all": round(avg_average, 1),
            "improvement_from_variations": round(avg_selected - avg_average, 1),
            "preferred_hook_styles": self.get_preferences(user_id).preferred_hook_styles
        }


preference_service = PreferenceService()

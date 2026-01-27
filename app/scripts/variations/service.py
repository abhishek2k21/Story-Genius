"""
Variation Service
Main service orchestrating variation generation.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

from app.scripts.variations.models import (
    VariationRequest, ScriptVariation, VariationStrategy,
    SelectionType, create_request_id
)
from app.scripts.variations.generator import variation_generator
from app.scripts.variations.scoring import variation_scorer
from app.scripts.variations.selection import selection_service
from app.scripts.variations.preferences import preference_service


class VariationService:
    """Main variation management service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._requests: Dict[str, VariationRequest] = {}
            cls._instance._variations: Dict[str, List[ScriptVariation]] = {}  # request_id -> variations
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def generate_variations(
        self,
        user_id: str,
        topic: str,
        content_category: str,
        target_duration: int,
        platform: str,
        variation_count: int = 3,
        strategy: VariationStrategy = VariationStrategy.MIXED,
        style_hints: List[str] = None,
        avoid_phrases: List[str] = None,
        use_preferences: bool = True
    ) -> Tuple[VariationRequest, List[ScriptVariation]]:
        """Generate script variations"""
        
        # Create request
        request = VariationRequest(
            request_id=create_request_id(),
            user_id=user_id,
            topic=topic,
            content_category=content_category,
            target_duration=target_duration,
            platform=platform,
            variation_count=variation_count,
            variation_strategy=strategy,
            style_hints=style_hints or [],
            avoid_phrases=avoid_phrases or []
        )
        
        # Generate variations
        variations = variation_generator.generate_variations(request)
        
        # Score all variations
        variation_scorer.score_all(variations, target_duration)
        
        # Update request status
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        
        # Store
        with self._lock:
            self._requests[request.request_id] = request
            self._variations[request.request_id] = variations
        
        return request, variations
    
    def get_request(self, request_id: str, user_id: str) -> Optional[VariationRequest]:
        """Get variation request"""
        request = self._requests.get(request_id)
        if request and request.user_id == user_id:
            return request
        return None
    
    def get_variations(self, request_id: str, user_id: str) -> Optional[List[ScriptVariation]]:
        """Get variations for request"""
        request = self.get_request(request_id, user_id)
        if request:
            return self._variations.get(request_id, [])
        return None
    
    def get_comparison(self, request_id: str, user_id: str) -> Optional[Dict]:
        """Get comparison view of variations"""
        request = self.get_request(request_id, user_id)
        variations = self.get_variations(request_id, user_id)
        
        if not request or not variations:
            return None
        
        recommended = selection_service.auto_select(variations)
        
        return {
            "request_id": request_id,
            "variation_count": len(variations),
            "variations": [v.to_dict() for v in variations],
            "recommended_index": recommended.variation_index if recommended else None,
            "strategy_used": request.variation_strategy.value
        }
    
    def select_variation(
        self,
        request_id: str,
        user_id: str,
        variation_index: int,
        selection_type: SelectionType = SelectionType.MANUAL,
        reason: str = "",
        modifications: Dict = None
    ) -> Tuple[Optional[Dict], str]:
        """Select a variation"""
        variations = self.get_variations(request_id, user_id)
        request = self.get_request(request_id, user_id)
        
        if not variations or not request:
            return None, "Request not found"
        
        # Find variation by index
        selected = None
        for v in variations:
            if v.variation_index == variation_index:
                selected = v
                break
        
        if not selected:
            return None, "Invalid variation index"
        
        # Apply modifications if any
        if modifications:
            selected = selection_service.apply_modifications(selected, modifications)
        
        # Create selection record
        selection = selection_service.create_selection(
            request_id=request_id,
            variation=selected,
            selection_type=selection_type,
            reason=reason,
            modifications=modifications
        )
        
        # Record in history
        avg_score = sum(v.scores.total() for v in variations) / len(variations)
        preference_service.record_selection(
            user_id=user_id,
            request_id=request_id,
            topic=request.topic,
            category=request.content_category,
            variation_count=len(variations),
            selected_index=variation_index,
            selected_score=selected.scores.total(),
            average_score=avg_score,
            selection_type=selection_type,
            hook_style=""  # Could extract from hook
        )
        
        return selection.to_dict(), "Variation selected"
    
    def finalize_variation(
        self,
        request_id: str,
        user_id: str,
        variation_index: int
    ) -> Tuple[Optional[Dict], str]:
        """Finalize variation for production"""
        variations = self.get_variations(request_id, user_id)
        
        if not variations:
            return None, "Request not found"
        
        # Find variation
        selected = None
        for v in variations:
            if v.variation_index == variation_index:
                selected = v
                break
        
        if not selected:
            return None, "Invalid variation index"
        
        # Create selection and finalize
        selection = selection_service.create_selection(
            request_id=request_id,
            variation=selected,
            selection_type=SelectionType.MANUAL
        )
        
        result = selection_service.finalize_script(selection, selected)
        return result, "Script finalized"


variation_service = VariationService()

"""
Variation Selection and Finalization
Selection workflow and script finalization.
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import threading

from app.scripts.variations.models import (
    ScriptVariation, VariationSelection, SelectionType, create_variation_id
)


class SelectionService:
    """Variation selection and finalization"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._selections: Dict[str, VariationSelection] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def auto_select(self, variations: List[ScriptVariation]) -> Optional[ScriptVariation]:
        """Auto-select highest scored variation"""
        if not variations:
            return None
        
        # Sort by total score, then hook score for ties
        sorted_vars = sorted(
            variations,
            key=lambda v: (v.scores.total(), v.scores.hook_strength),
            reverse=True
        )
        
        return sorted_vars[0]
    
    def get_top_n(self, variations: List[ScriptVariation], n: int = 3) -> List[ScriptVariation]:
        """Get top N variations for hybrid selection"""
        sorted_vars = sorted(
            variations,
            key=lambda v: v.scores.total(),
            reverse=True
        )
        return sorted_vars[:n]
    
    def create_selection(
        self,
        request_id: str,
        variation: ScriptVariation,
        selection_type: SelectionType,
        reason: str = "",
        modifications: Dict = None
    ) -> VariationSelection:
        """Record selection"""
        selection = VariationSelection(
            selection_id=str(uuid.uuid4()),
            request_id=request_id,
            selected_variation_id=variation.variation_id,
            selection_type=selection_type,
            selection_reason=reason,
            modifications=modifications or {}
        )
        
        with self._lock:
            self._selections[selection.selection_id] = selection
        
        return selection
    
    def apply_modifications(
        self,
        variation: ScriptVariation,
        modifications: Dict
    ) -> ScriptVariation:
        """Apply modifications to variation"""
        modified = ScriptVariation(
            variation_id=create_variation_id(),
            request_id=variation.request_id,
            variation_index=variation.variation_index,
            hook=modifications.get("hook", variation.hook),
            body=modifications.get("body", variation.body),
            cta=modifications.get("cta", variation.cta),
            scores=variation.scores,
            rank=variation.rank,
            strengths=variation.strengths,
            weaknesses=variation.weaknesses
        )
        return modified
    
    def finalize_script(
        self,
        selection: VariationSelection,
        variation: ScriptVariation
    ) -> Dict:
        """Finalize script for production"""
        # Generate final script ID
        final_id = str(uuid.uuid4())
        selection.final_script_id = final_id
        
        # Validate completeness
        warnings = []
        if not variation.hook:
            warnings.append("Missing hook")
        if not variation.body:
            warnings.append("Missing body")
        if not variation.cta:
            warnings.append("Missing CTA")
        
        quality_score = variation.scores.total()
        ready = len(warnings) == 0 and quality_score >= 60
        
        return {
            "script_id": final_id,
            "final_script": {
                "hook": variation.hook,
                "body": variation.body,
                "cta": variation.cta,
                "full_text": variation.full_script
            },
            "quality_score": round(quality_score, 1),
            "ready_for_production": ready,
            "warnings": warnings
        }
    
    def get_selection(self, selection_id: str) -> Optional[VariationSelection]:
        """Get selection by ID"""
        return self._selections.get(selection_id)


selection_service = SelectionService()

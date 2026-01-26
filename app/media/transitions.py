"""
Scene Transition Intelligence
Selects appropriate transitions based on semantic content relationships.
"""
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


class TransitionType(str, Enum):
    """Available transition types"""
    CUT = "cut"  # Instant
    FADE = "fade"  # Crossfade
    DISSOLVE = "dissolve"  # Blend
    SLIDE = "slide"  # Directional wipe
    ZOOM = "zoom"  # Scale transition


@dataclass
class Transition:
    """Transition specification"""
    type: TransitionType
    duration: float  # seconds
    use_case: str


class TransitionEngine:
    """Intelligently selects transitions based on scene relationships"""
    
    # Transition definitions
    TRANSITIONS = {
        TransitionType.CUT: Transition(
            type=TransitionType.CUT,
            duration=0,
            use_case="same location, quick pace"
        ),
        TransitionType.FADE: Transition(
            type=TransitionType.FADE,
            duration=0.5,
            use_case="time passage, mood shift"
        ),
        TransitionType.DISSOLVE: Transition(
            type=TransitionType.DISSOLVE,
            duration=0.3,
            use_case="related concepts, smooth flow"
        ),
        TransitionType.SLIDE: Transition(
            type=TransitionType.SLIDE,
            duration=0.4,
            use_case="spatial movement, location change"
        ),
        TransitionType.ZOOM: Transition(
            type=TransitionType.ZOOM,
            duration=0.3,
            use_case="focus shift, detail emphasis"
        )
    }
    
    # Time jump indicator words
    TIME_INDICATORS = [
        "later", "meanwhile", "next", "then", "after",
        "subsequently", "following", "eventually", "soon",
        "years later", "moments later", "the next day"
    ]
    
    # Location change indicators
    LOCATION_INDICATORS = [
        "elsewhere", "at", "in", "while", "back at",
        "far away", "nearby", "across", "beyond"
    ]
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service or self._get_default_llm()
    
    def _get_default_llm(self):
        """Get default LLM service"""
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def select_transition(
        self,
        scene_a: Dict,
        scene_b: Dict,
        default: TransitionType = TransitionType.DISSOLVE
    ) -> Transition:
        """
        Select appropriate transition based on scene relationship
        
        Args:
            scene_a: Previous scene with 'narration' field
            scene_b: Next scene with 'narration' field
            default: Fallback transition type
        
        Returns:
            Transition object with type and duration
        """
        narration_a = scene_a.get("narration", "")
        narration_b = scene_b.get("narration", "")
        
        # Check for time jump
        if self.detect_time_jump(narration_b):
            logger.debug("Time jump detected → FADE")
            return self.TRANSITIONS[TransitionType.FADE]
        
        # Check for location change
        if self.detect_location_change(narration_a, narration_b):
            logger.debug("Location change detected → SLIDE")
            return self.TRANSITIONS[TransitionType.SLIDE]
        
        # Calculate semantic similarity
        similarity = self.semantic_similarity(narration_a, narration_b)
        
        # High similarity = smooth dissolve
        if similarity > 0.7:
            logger.debug(f"High similarity ({similarity:.2f}) → DISSOLVE")
            return self.TRANSITIONS[TransitionType.DISSOLVE]
        
        # Low similarity = cut
        if similarity < 0.3:
            logger.debug(f"Low similarity ({similarity:.2f}) → CUT")
            return self.TRANSITIONS[TransitionType.CUT]
        
        # Medium similarity = default
        logger.debug(f"Medium similarity ({similarity:.2f}) → {default.value.upper()}")
        return self.TRANSITIONS.get(default, self.TRANSITIONS[TransitionType.DISSOLVE])
    
    def detect_time_jump(self, text: str) -> bool:
        """
        Detect temporal transition phrases
        
        Args:
            text: Scene narration text
        
        Returns:
            True if time jump detected
        """
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.TIME_INDICATORS)
    
    def detect_location_change(self, text_a: str, text_b: str) -> bool:
        """
        Detect location change between scenes
        
        Args:
            text_a: Previous scene narration
            text_b: Next scene narration
        
        Returns:
            True if location change detected
        """
        text_b_lower = text_b.lower()
        
        # Check for explicit location indicators
        for indicator in self.LOCATION_INDICATORS:
            if indicator in text_b_lower:
                return True
        
        # TODO: Could enhance with entity extraction to compare locations
        return False
    
    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Args:
            text_a: First text
            text_b: Second text
        
        Returns:
            Similarity score 0-1 (1 = identical meaning)
        """
        # Simple word overlap heuristic
        # TODO: Could enhance with embeddings (sentence-transformers)
        
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'in', 'on', 'at'}
        words_a -= stop_words
        words_b -= stop_words
        
        if not words_a or not words_b:
            return 0.5  # Neutral similarity
        
        # Jaccard similarity
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity
    
    def apply_transitions_to_scenes(
        self,
        scenes: List[Dict]
    ) -> List[Dict]:
        """
        Apply transition selection to all scenes
        
        Args:
            scenes: List of scene dictionaries
        
        Returns:
            Scenes with 'transition' field added
        """
        if len(scenes) <= 1:
            return scenes
        
        for i in range(len(scenes) - 1):
            scene_a = scenes[i]
            scene_b = scenes[i + 1]
            
            transition = self.select_transition(scene_a, scene_b)
            
            # Add transition to current scene (transition happens at end)
            scenes[i]["transition"] = {
                "type": transition.type.value,
                "duration": transition.duration,
                "to_scene": i + 1
            }
        
        # Last scene has no transition
        scenes[-1]["transition"] = None
        
        logger.info(f"Applied transitions to {len(scenes) - 1} scene boundaries")
        return scenes

"""
Emotion Curve Enforcement
Validates that generated scenes match planned emotional trajectory.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmotionScore:
    """Result of emotion validation"""
    detected_emotion: str
    intensity: float  # 0-10
    matches_expectation: bool
    suggestion: Optional[str] = None


@dataclass
class ExpectedEmotion:
    """Expected emotion for a scene"""
    emotion: str  # curiosity, tension, wonder, joy, fear, etc.
    intensity: float  # 0-10


class EmotionEnforcer:
    """Validates and enforces emotional content in scenes"""
    
    # Emotion keywords for detection
    EMOTION_KEYWORDS = {
        "curiosity": ["wonder", "curious", "question", "mystery", "why", "how", "discover"],
        "tension": ["danger", "threat", "risk", "urgent", "critical", "warning"],
        "wonder": ["amazing", "incredible", "beautiful", "awe", "magnificent"],
        "joy": ["happy", "delight", "celebrate", "excited", "wonderful"],
        "fear": ["scary", "frightening", "terrifying", "horror", "afraid"],
        "surprise": ["shocking", "unexpected", "sudden", "reveal", "twist"],
        "sadness": ["tragic", "loss", "unfortunate", "sad", "grief"],
        "neutral": []
    }
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service or self._get_default_llm()
    
    def _get_default_llm(self):
        """Get default LLM service"""
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def validate_scene_emotion(
        self,
        scene: Dict,
        expected_emotion: str,
        expected_intensity: float
    ) -> EmotionScore:
        """
        Analyze scene narration for emotional content
        
        Args:
            scene: Scene dictionary with 'narration' field
            expected_emotion: Expected emotion type
            expected_intensity: Expected intensity (0-10)
        
        Returns:
            EmotionScore with validation results
        """
        narration = scene.get("narration", "")
        
        prompt = f"""
Analyze this text for emotional content:

"{narration}"

Expected emotion: {expected_emotion}
Expected intensity: {expected_intensity}/10

Return JSON:
{{
    "detected_emotion": "curiosity|tension|wonder|joy|fear|surprise|neutral",
    "intensity": 0-10,
    "matches_expectation": true/false,
    "suggestion": "how to adjust if not matching (or null if matching)"
}}

Be precise about the emotional tone and intensity.
"""
        
        try:
            response = self.llm_service.generate_text(prompt)
            
            # Parse JSON
            import json
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            score = EmotionScore(
                detected_emotion=data["detected_emotion"],
                intensity=float(data["intensity"]),
                matches_expectation=data["matches_expectation"],
                suggestion=data.get("suggestion")
            )
            
            logger.debug(
                f"Emotion validation: detected={score.detected_emotion} "
                f"(expected={expected_emotion}), "
                f"intensity={score.intensity}/{expected_intensity}, "
                f"match={score.matches_expectation}"
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error validating emotion: {e}")
            # Fallback to keyword matching
            return self._fallback_emotion_check(
                narration,
                expected_emotion,
                expected_intensity
            )
    
    def _fallback_emotion_check(
        self,
        narration: str,
        expected_emotion: str,
        expected_intensity: float
    ) -> EmotionScore:
        """Fallback emotion detection using keyword matching"""
        narration_lower = narration.lower()
        
        # Check for emotion keywords
        keywords = self.EMOTION_KEYWORDS.get(expected_emotion, [])
        matches = sum(1 for kw in keywords if kw in narration_lower)
        
        # Simple intensity estimation
        intensity = min(matches * 2, 10)  # Each keyword adds 2 points
        
        matches_expectation = (
            matches > 0 and
            abs(intensity - expected_intensity) < 3
        )
        
        return EmotionScore(
            detected_emotion=expected_emotion if matches > 0 else "neutral",
            intensity=intensity,
            matches_expectation=matches_expectation,
            suggestion="Add more emotional language" if not matches_expectation else None
        )
    
    def enforce_curve(
        self,
        scenes: List[Dict],
        emotion_curve: List[ExpectedEmotion]
    ) -> List[Dict]:
        """
        Validate all scenes against emotion curve
        Regenerate narration for scenes that don't match
        
        Args:
            scenes: List of scene dictionaries
            emotion_curve: List of expected emotions (one per scene)
        
        Returns:
            Scenes with validated/adjusted emotions
        """
        if len(emotion_curve) != len(scenes):
            logger.warning(
                f"Emotion curve length ({len(emotion_curve)}) "
                f"doesn't match scenes ({len(scenes)})"
            )
            return scenes
        
        adjusted_scenes = []
        
        for i, (scene, expected) in enumerate(zip(scenes, emotion_curve)):
            # Validate emotion
            score = self.validate_scene_emotion(
                scene,
                expected.emotion,
                expected.intensity
            )
            
            scene["emotion_validated"] = score.matches_expectation
            scene["detected_emotion"] = score.detected_emotion
            scene["emotion_intensity"] = score.intensity
            
            # Regenerate if doesn't match
            if not score.matches_expectation and score.suggestion:
                logger.info(
                    f"Scene {i} emotion mismatch. "
                    f"Expected {expected.emotion}/{expected.intensity}, "
                    f"got {score.detected_emotion}/{score.intensity}"
                )
                
                # Attempt regeneration
                new_narration = self.regenerate_with_emotion(
                    scene["narration"],
                    expected.emotion,
                    expected.intensity,
                    suggestion=score.suggestion
                )
                
                scene["narration"] = new_narration
                scene["emotion_regenerated"] = True
            else:
                scene["emotion_regenerated"] = False
            
            adjusted_scenes.append(scene)
        
        validated_count = sum(1 for s in adjusted_scenes if s["emotion_validated"])
        logger.info(
            f"Emotion enforcement complete: {validated_count}/{len(scenes)} scenes validated"
        )
        
        return adjusted_scenes
    
    def regenerate_with_emotion(
        self,
        original_text: str,
        target_emotion: str,
        target_intensity: float,
        suggestion: Optional[str] = None
    ) -> str:
        """
        Regenerate narration with desired emotional content
        
        Args:
            original_text: Original narration
            target_emotion: Target emotion type
            target_intensity: Target intensity (0-10)
            suggestion: Optional suggestion for improvement
        
        Returns:
            Regenerated narration
        """
        prompt = f"""
Rewrite this narration to convey {target_emotion} with intensity {target_intensity}/10:

Original: "{original_text}"

{f"Suggestion: {suggestion}" if suggestion else ""}

Requirements:
- Keep the core information/message
- Adjust language to convey {target_emotion}
- Make it feel {target_intensity}/10 in intensity
- Maintain similar length

Return ONLY the rewritten narration.
"""
        
        try:
            regenerated = self.llm_service.generate_text(prompt).strip()
            logger.info(f"Regenerated narration for {target_emotion}")
            return regenerated
            
        except Exception as e:
            logger.error(f"Regeneration failed: {e}")
            return original_text  # Return original if failed

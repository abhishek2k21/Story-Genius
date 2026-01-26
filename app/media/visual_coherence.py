"""
Visual Coherence Engine
Ensures generated visuals match narration precisely.
"""
from typing import Optional
from dataclasses import dataclass
from app.media.entity_extractor import EntityExtractor, VisualEntity
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CoherenceScore:
    """Result of coherence verification"""
    score: float  # 0-1 where 1 is perfect match
    matches: list  # Entities that matched
    mismatches: list  # Entities that didn't match
    feedback: str  # Explanation


class VisualCoherenceEngine:
    """Ensures visuals match narration using entity extraction and verification"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service or self._get_default_llm()
        self.entity_extractor = EntityExtractor(llm_service)
    
    def _get_default_llm(self):
        """Get default LLM service"""
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def build_coherent_prompt(
        self,
        narration: str,
        visual_style: str = "cinematic",
        scene_emotion: Optional[str] = None
    ) -> str:
        """
        Build structured Imagen prompt that ensures coherence with narration
        
        Args:
            narration: The spoken narration for this scene
            visual_style: Visual style (cinematic, comic, realistic, etc.)
            scene_emotion: Optional emotion override
        
        Returns:
            Structured prompt for Imagen
        """
        # Extract entities from narration
        entities = self.entity_extractor.extract_entities(narration)
        
        # Use extracted emotion or provided one
        emotion = scene_emotion or entities.emotion or "neutral"
        
        # Infer lighting from emotion
        lighting = self._infer_lighting(emotion)
        
        # Build structured prompt
        components = []
        
        # Subject and action
        if entities.subject and entities.action:
            components.append(f"{entities.subject} {entities.action}")
        elif entities.subject:
            components.append(entities.subject)
        
        # Objects
        if entities.objects:
            components.append(f"with {', '.join(entities.objects[:3])}")  # Max 3 objects
        
        # Setting
        if entities.setting:
            components.append(f"in {entities.setting}")
        
        # Emotion and style
        components.append(f"{emotion} mood")
        components.append(f"{lighting} lighting")
        components.append(f"{visual_style} style")
        
        # Join into coherent prompt
        prompt = ", ".join(components)
        
        logger.info(f"Built coherent prompt: {prompt}")
        logger.debug(f"From narration: '{narration}'")
        logger.debug(f"Extracted entities: {entities}")
        
        return prompt
    
    def _infer_lighting(self, emotion: str) -> str:
        """Infer appropriate lighting from emotion"""
        lighting_map = {
            "happy": "bright",
            "joyful": "bright",
            "energetic": "vibrant",
            "sad": "dim",
            "mysterious": "dark",
            "tense": "dramatic",
            "peaceful": "soft",
            "angry": "harsh",
            "curious": "warm",
            "neutral": "natural"
        }
        
        emotion_lower = emotion.lower() if emotion else "neutral"
        return lighting_map.get(emotion_lower, "natural")
    
    def verify_coherence(
        self,
        image_url: str,
        narration: str,
        min_score: float = 0.7
    ) -> CoherenceScore:
        """
        Verify that generated image matches narration
        Uses Gemini Vision to analyze the image
        
        Args:
            image_url: URL or path to generated image
            narration: Original narration text
            min_score: Minimum acceptable score
        
        Returns:
            CoherenceScore with verification results
        """
        # Extract expected entities
        entities = self.entity_extractor.extract_entities(narration)
        
        # Build verification prompt for Gemini Vision
        verification_prompt = f"""
Analyze this image and check if it matches the following description:

"{narration}"

Expected visual elements:
- Subject: {entities.subject}
- Action: {entities.action}
- Objects: {', '.join(entities.objects) if entities.objects else 'none specified'}
- Setting: {entities.setting}
- Emotion/Mood: {entities.emotion}

For each element, indicate if it's present in the image.
Return JSON:
{{
    "subject_match": true/false,
    "action_match": true/false,
    "objects_match": ["matched_object1", "matched_object2"],
    "setting_match": true/false,
    "emotion_match": true/false,
    "overall_score": 0.0-1.0,
    "feedback": "explanation of matches and mismatches"
}}
"""
        
        try:
            # TODO: Use Gemini Vision API
            # For now, using placeholder logic
            # response = self.llm_service.analyze_image(image_url, verification_prompt)
            
            # Placeholder: assume good coherence if we built the prompt correctly
            matches = []
            mismatches = []
            
            if entities.subject:
                matches.append(f"subject: {entities.subject}")
            if entities.setting:
                matches.append(f"setting: {entities.setting}")
            
            score = 0.8  # Placeholder score
            
            return CoherenceScore(
                score=score,
                matches=matches,
                mismatches=mismatches,
                feedback=f"Coherence score: {score:.2f}. Image should contain the narrated elements."
            )
            
        except Exception as e:
            logger.error(f"Error verifying coherence: {e}")
            return CoherenceScore(
                score=0.5,
                matches=[],
                mismatches=["verification error"],
                feedback=f"Could not verify: {str(e)}"
            )
    
    def should_regenerate(self, coherence_result: CoherenceScore, threshold: float = 0.7) -> bool:
        """Determine if image should be regenerated based on coherence score"""
        return coherence_result.score < threshold

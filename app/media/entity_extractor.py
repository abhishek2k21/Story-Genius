"""
Entity Extractor for Visual Coherence
Extracts visual entities from narration using NER and semantic analysis.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VisualEntity:
    """Represents a visual entity extracted from narration"""
    subject: Optional[str] = None
    action: Optional[str] = None
    objects: List[str] = None
    setting: Optional[str] = None 
    emotion: Optional[str] = None
    
    def __post_init__(self):
        if self.objects is None:
            self.objects = []


class EntityExtractor:
    """Extracts visual entities from narration text"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service or self._get_default_llm()
    
    def _get_default_llm(self):
        """Get default LLM service"""
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def extract_entities(self, narration: str) -> VisualEntity:
        """
        Extract visual entities from narration
        
        Returns entities needed for image generation:
        - Subject (main character/object)
        - Action (what's happening)
        - Objects (props, items mentioned)
        - Setting (location, environment)
        - Emotion (mood, feeling)
        """
        prompt = f"""
Analyze this narration and extract visual elements for image generation:

"{narration}"

Return a JSON object with these fields:
{{
    "subject": "main character or object (e.g., 'Einstein', 'coffee cup', 'mountain')",
    "action": "the action being performed (e.g., 'writing', 'exploding', 'glowing')",
    "objects": ["list", "of", "props", "or", "items"],
    "setting": "the location/environment (e.g., 'office', 'forest', 'space')",
    "emotion": "the mood/feeling (e.g., 'happy', 'tense', 'mysterious')"
}}

Be specific and detailed. Include all visual elements mentioned.
"""
        
        try:
            response = self.llm_service.generate_text(prompt)
            
            # Parse JSON response
            import json
            # Extract JSON from response (might have markdown formatting)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            entity = VisualEntity(
                subject=data.get("subject"),
                action=data.get("action"),
                objects=data.get("objects", []),
                setting=data.get("setting"),
                emotion=data.get("emotion")
            )
            
            logger.debug(f"Extracted entities from '{narration[:50]}...': {entity}")
            return entity
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            # Return basic fallback
            return VisualEntity(
                subject="person",
                setting="neutral background"
            )

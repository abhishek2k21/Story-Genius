"""
Week 18 Day 1 - Preview Service
Generate lightweight preview before full video render.
Creators see script + storyboard before committing time & money.
"""
import time
import json
from typing import Optional, Dict
from google import genai
from google.genai import types

from app.preview.models import (
    Preview, ScenePreview, PreviewResult, PreviewWarning, PreviewStatus
)
from app.core.contract import GenerationContract, create_contract
from app.core.logging import get_logger

logger = get_logger(__name__)


class PreviewService:
    """
    Generate video preview before full render.
    Returns script + scene descriptions in <5 seconds.
    """
    
    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("PreviewService initialized")
        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")
            self.client = None
    
    def generate_preview(
        self,
        topic: str,
        audience_baseline: str = "general_adult",
        tone: str = "neutral",
        language: str = "en",
        num_scenes: int = 5,
        brand_kit_id: Optional[str] = None
    ) -> PreviewResult:
        """
        Generate lightweight preview.
        
        Args:
            topic: Content topic/idea
            audience_baseline: "general_adult", "kids", "expert"
            tone: "neutral", "sharp", "bold", "playful"
            language: Language code
            num_scenes: Number of scenes (3-12)
            brand_kit_id: Optional brand kit to apply
            
        Returns:
            PreviewResult with preview and warnings
        """
        start_time = time.time()
        warnings = []
        
        logger.info(f"Generating preview for: {topic[:50]}...")
        
        # Create preview object
        preview = Preview(
            topic=topic,
            audience_baseline=audience_baseline,
            tone=tone,
            language=language,
            brand_kit_id=brand_kit_id
        )
        
        # Score idea first using Path 1 (quick check)
        depth_score, hook_score = self._quick_score(topic, audience_baseline)
        preview.depth_score = depth_score
        preview.hook_score = hook_score
        
        # Add warnings if scores are low
        if depth_score < 0.5:
            warnings.append(PreviewWarning(
                type="low_depth",
                message=f"Idea depth score is low ({depth_score:.0%}). Consider strengthening the concept.",
                severity="warning"
            ))
        
        if hook_score < 60:
            warnings.append(PreviewWarning(
                type="low_hook",
                message=f"Hook potential is low ({hook_score}%). Consider a more attention-grabbing angle.",
                severity="warning"
            ))
        
        # Generate script preview
        scenes = self._generate_script_preview(topic, audience_baseline, tone, language, num_scenes)
        preview.scenes = scenes
        
        # Determine content mode
        if audience_baseline == "kids":
            preview.content_mode = "story"
        else:
            preview.content_mode = "commentary"
        
        # Update estimates
        preview.update_estimates()
        preview.status = PreviewStatus.READY
        
        # Duration warning
        if preview.estimated_duration > 90:
            warnings.append(PreviewWarning(
                type="long_duration",
                message=f"Video will be {preview.estimated_duration:.0f}s. Consider shortening for better retention.",
                severity="info"
            ))
        
        generation_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Preview generated in {generation_time}ms | {len(scenes)} scenes | {preview.estimated_cost:.3f} USD")
        
        return PreviewResult(
            preview=preview,
            warnings=warnings,
            generation_time_ms=generation_time
        )
    
    def _quick_score(self, topic: str, audience_baseline: str) -> tuple:
        """Quick scoring without full Path 1 analysis."""
        if not self.client:
            return 0.7, 70  # Mock scores
        
        try:
            prompt = f"""
            Rate this content idea for {audience_baseline} audience:
            "{topic}"
            
            Return JSON only:
            {{"depth_score": 0.0-1.0, "hook_score": 0-100}}
            
            depth_score: How thoughtful/valuable is this idea?
            hook_score: How likely is this to grab attention in first 3 seconds?
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=100,
                )
            )
            
            text = response.text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(text[json_start:json_end])
                return data.get("depth_score", 0.7), data.get("hook_score", 70)
            
        except Exception as e:
            logger.warning(f"Quick score failed: {e}")
        
        return 0.7, 70
    
    def _generate_script_preview(
        self,
        topic: str,
        audience_baseline: str,
        tone: str,
        language: str,
        num_scenes: int
    ) -> list:
        """Generate script and scene descriptions."""
        
        if not self.client:
            return self._mock_scenes(topic, num_scenes)
        
        try:
            # Tone-specific instructions
            tone_instructions = {
                "neutral": "Confident and concise. Assume intelligence.",
                "sharp": "Incisive and cutting. No fluff.",
                "bold": "Provocative and assertive. Take strong positions.",
                "playful": "Witty and light. Still intelligent."
            }
            
            prompt = f"""
            Create a video script preview.
            
            TOPIC: {topic}
            AUDIENCE: {audience_baseline}
            TONE: {tone} - {tone_instructions.get(tone, "")}
            LANGUAGE: Generate directly in {language}
            SCENES: {num_scenes}
            
            For each scene provide:
            - script: Narrator text (max 15 words, ~5-7 seconds)
            - visual: Detailed visual description
            - tone: The tone of this specific scene
            - duration: Estimated seconds (5-8)
            
            Return JSON array only:
            [
                {{"script": "...", "visual": "...", "tone": "...", "duration": 5}},
                ...
            ]
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            
            text = response.text
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                data = json.loads(text[json_start:json_end])
                
                scenes = []
                for i, item in enumerate(data):
                    scenes.append(ScenePreview(
                        id=i + 1,
                        script=item.get("script", ""),
                        visual_description=item.get("visual", ""),
                        estimated_duration=item.get("duration", 5),
                        tone=item.get("tone", tone)
                    ))
                return scenes
                
        except Exception as e:
            logger.error(f"Script preview failed: {e}")
        
        return self._mock_scenes(topic, num_scenes)
    
    def _mock_scenes(self, topic: str, num_scenes: int) -> list:
        """Generate mock scenes for testing."""
        mock_scripts = [
            f"Let's talk about {topic}.",
            "Here's what nobody tells you.",
            "The data is clear on this.",
            "But here's the twist.",
            "And that's the key insight."
        ]
        
        scenes = []
        for i in range(min(num_scenes, len(mock_scripts))):
            scenes.append(ScenePreview(
                id=i + 1,
                script=mock_scripts[i],
                visual_description=f"Scene {i+1}: Visual related to {topic}",
                estimated_duration=5,
                tone="neutral"
            ))
        
        return scenes


# Singleton
_service = None

def get_preview_service() -> PreviewService:
    global _service
    if _service is None:
        _service = PreviewService()
    return _service


def generate_preview(
    topic: str,
    audience_baseline: str = "general_adult",
    tone: str = "neutral",
    language: str = "en",
    num_scenes: int = 5,
    brand_kit_id: Optional[str] = None
) -> Dict:
    """
    Quick function to generate preview.
    
    Returns:
        Preview result as dict
    """
    service = get_preview_service()
    result = service.generate_preview(
        topic, audience_baseline, tone, language, num_scenes, brand_kit_id
    )
    return result.to_dict()

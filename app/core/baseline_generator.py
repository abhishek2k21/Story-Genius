"""
Week 16 - Baseline Script Generator
Generates scripts with adult defaults and anti-over-explanation rules.
"""
import json
from typing import Dict, Optional
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.baseline import (
    SimpleConfig, AudienceBaseline, Tone,
    KILL_OVER_EXPLANATION_RULES
)
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScriptOutput:
    """Generated script output."""
    script: str
    segments: list
    content_mode: str
    duration: float
    language: str
    baseline: str
    tone: str


class BaselineScriptGenerator:
    """
    Script generator with adult defaults.
    Enforces anti-over-explanation rules.
    """
    
    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("BaselineScriptGenerator initialized")
        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")
            self.client = None
    
    def generate(self, config: SimpleConfig, refined_idea: Optional[str] = None) -> ScriptOutput:
        """
        Generate script based on config.
        
        Args:
            config: SimpleConfig with baseline and tone
            refined_idea: Optional Path 1 refined idea (uses config.topic if not provided)
            
        Returns:
            ScriptOutput with full script
        """
        topic = refined_idea or config.topic
        content_mode = config.get_content_mode()
        
        logger.info(f"Generating {content_mode} script | baseline={config.audience_baseline} | tone={config.tone}")
        
        prompt = self._build_prompt(config, topic)
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=2048,
                    )
                )
                return self._parse_response(response.text, config)
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return self._mock_output(config)
        else:
            return self._mock_output(config)
    
    def _build_prompt(self, config: SimpleConfig, topic: str) -> str:
        """Build the complete generation prompt."""
        
        # Core task
        prompt = f"""
GENERATE A {config.duration_seconds}-SECOND SCRIPT

TOPIC: {topic}

{config.get_generation_rules()}
"""
        
        # Content mode specific
        content_mode = config.get_content_mode()
        
        if content_mode == "story":
            prompt += """
STRUCTURE: Story with characters, plot, conflict, resolution.
Include moral or lesson appropriate for children.
"""
        else:
            prompt += """
STRUCTURE: Commentary/Explainer (NOT a story)
- Strong hook in first 3 seconds
- Make your point clearly
- Support with evidence or insight
- End with memorable takeaway (NOT a moral)
- NO plot, NO characters, NO narrative arc
"""
        
        # Anti-over-explanation (critical for adult content)
        if config.is_adult():
            prompt += f"""
{KILL_OVER_EXPLANATION_RULES}
"""
        
        # Output format
        prompt += """
OUTPUT FORMAT (JSON):
{
    "script": "The complete script as one string",
    "segments": [
        {"text": "Segment text", "duration": 5, "tone": "segment tone"},
        ...
    ]
}

Make it {duration} seconds total.
"""
        
        return prompt.replace("{duration}", str(config.duration_seconds))
    
    def _parse_response(self, response_text: str, config: SimpleConfig) -> ScriptOutput:
        """Parse LLM response."""
        try:
            # Extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("No JSON found")
            
            script = data.get("script", "")
            segments = data.get("segments", [])
            total_duration = sum(s.get("duration", 5) for s in segments)
            
            return ScriptOutput(
                script=script,
                segments=segments,
                content_mode=config.get_content_mode(),
                duration=total_duration,
                language=config.language,
                baseline=config.audience_baseline,
                tone=config.tone
            )
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._mock_output(config)
    
    def _mock_output(self, config: SimpleConfig) -> ScriptOutput:
        """Generate mock output for testing."""
        
        if config.audience_baseline == AudienceBaseline.KIDS.value:
            script = "Once upon a time, there was a curious little robot who wanted to learn..."
            segments = [
                {"text": "Once upon a time...", "duration": 5, "tone": "warm"},
                {"text": "The robot discovered something amazing.", "duration": 5, "tone": "wonder"},
                {"text": "And learned an important lesson about friendship.", "duration": 5, "tone": "meaningful"},
            ]
        elif config.tone == Tone.BOLD.value:
            script = "Here's the truth nobody wants to admit. Everything you've been told is backwards."
            segments = [
                {"text": "Here's the truth nobody wants to admit.", "duration": 4, "tone": "provocative"},
                {"text": "Everything you've been told is backwards.", "duration": 4, "tone": "bold"},
                {"text": "Let me show you why.", "duration": 4, "tone": "confident"},
            ]
        elif config.tone == Tone.SHARP.value:
            script = "Cut the fluff. Here's what actually matters. Most people miss this."
            segments = [
                {"text": "Cut the fluff.", "duration": 3, "tone": "sharp"},
                {"text": "Here's what actually matters.", "duration": 4, "tone": "direct"},
                {"text": "Most people miss this.", "duration": 3, "tone": "incisive"},
            ]
        else:  # NEUTRAL
            script = "There's something interesting about how we approach this. The data tells a clear story."
            segments = [
                {"text": "There's something interesting about this.", "duration": 4, "tone": "confident"},
                {"text": "The data tells a clear story.", "duration": 4, "tone": "neutral"},
                {"text": "Here's the takeaway.", "duration": 3, "tone": "conclusive"},
            ]
        
        return ScriptOutput(
            script=script,
            segments=segments,
            content_mode=config.get_content_mode(),
            duration=sum(s["duration"] for s in segments),
            language=config.language,
            baseline=config.audience_baseline,
            tone=config.tone
        )


# Singleton
_generator = None

def get_baseline_generator() -> BaselineScriptGenerator:
    global _generator
    if _generator is None:
        _generator = BaselineScriptGenerator()
    return _generator


def generate_baseline_script(
    topic: str,
    baseline: str = "general_adult",
    tone: str = "neutral",
    language: str = "en",
    duration: int = 30
) -> Dict:
    """
    Quick script generation with adult defaults.
    
    Args:
        topic: Content topic
        baseline: "general_adult" (default), "kids", "expert"
        tone: "neutral", "sharp", "bold", "playful"
        language: Language code
        duration: Duration in seconds
        
    Returns:
        Script output as dict
    """
    config = SimpleConfig(
        topic=topic,
        audience_baseline=AudienceBaseline(baseline),
        tone=Tone(tone),
        language=language,
        duration_seconds=duration
    )
    
    generator = get_baseline_generator()
    output = generator.generate(config)
    
    return {
        "script": output.script,
        "segments": output.segments,
        "content_mode": output.content_mode,
        "duration": output.duration,
        "baseline": output.baseline,
        "tone": output.tone,
        "language": output.language
    }

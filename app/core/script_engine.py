"""
Week 15 - Script Engine
Direct script generation that bypasses story engine for non-story content.
Supports commentary, explainer, and comedy modes.
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.global_mode import (
    GenerationConfig, ContentMode, Intent, AdultPersona, AudienceProfile
)
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScriptSegment:
    """A segment of the generated script."""
    text: str
    duration_seconds: float
    visual_direction: str
    tone: str


@dataclass
class GeneratedScript:
    """Complete generated script."""
    segments: List[ScriptSegment]
    total_duration: float
    language: str
    mode: str
    persona: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "segments": [
                {
                    "text": s.text,
                    "duration_seconds": s.duration_seconds,
                    "visual_direction": s.visual_direction,
                    "tone": s.tone
                }
                for s in self.segments
            ],
            "total_duration": self.total_duration,
            "language": self.language,
            "mode": self.mode,
            "persona": self.persona
        }
    
    def get_full_script(self) -> str:
        return "\n\n".join(s.text for s in self.segments)


class ScriptEngine:
    """
    Direct script generation without story structure.
    For commentary, explainer, and comedy content.
    """
    
    # Persona-specific prompts
    PERSONA_PROMPTS = {
        AdultPersona.DRY_COMEDIAN.value: """
You are a DRY COMEDIAN. Your style:
- Sarcasm is your native language
- NO morals, NO lessons, NO preaching
- Punchlines > plot setup
- Deadpan delivery, subtle humor
- Assume the audience is smart
- Reference current culture
""",
        AdultPersona.SHARP_ANALYST.value: """
You are a SHARP ANALYST. Your style:
- Structure: Claim → Evidence → Takeaway
- NO fictional characters, NO narratives
- Emotions only when data-justified
- Cold, precise, incisive
- Challenge mainstream views
- Back everything with logic
""",
        AdultPersona.STREET_EXPLAINER.value: """
You are a STREET EXPLAINER. Your style:
- Casual, conversational language
- Cultural references specific to region
- Assume viewer is ALREADY smart
- No explaining basics - get to insights
- Use slang appropriately
- Make complex things feel obvious
"""
    }
    
    MODE_PROMPTS = {
        ContentMode.COMMENTARY.value: """
CONTENT MODE: COMMENTARY
- This is opinion/analysis, NOT a story
- Structure: Hook → Point → Support → Conclusion
- Be direct and opinionated
- End with a clear position, NOT a moral
- ❌ NO "once upon a time", NO characters, NO plot
""",
        ContentMode.EXPLAINER.value: """
CONTENT MODE: EXPLAINER
- Clear, concise explanation
- Structure: What → Why → How → So What
- No fluff, no unnecessary setup
- Assume audience is curious but not dumb
- ❌ NO storytelling, NO fictional scenarios
""",
        ContentMode.COMEDY.value: """
CONTENT MODE: COMEDY
- Jokes, timing, punchlines
- Subvert expectations
- Setup → Misdirection → Payoff
- Dark humor is fine for adults
- ❌ NO morals, NO lessons
""",
        ContentMode.STORY.value: """
CONTENT MODE: STORY
- Narrative arc with character and plot
- Hook → Rising action → Climax → Resolution
- Appropriate for target age group
- Clear moral/lesson for kids
"""
    }
    
    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("ScriptEngine initialized")
        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")
            self.client = None
    
    def generate_script(self, config: GenerationConfig, refined_idea: str) -> GeneratedScript:
        """
        Generate script based on configuration.
        
        Args:
            config: Complete generation configuration
            refined_idea: The Path 1 refined idea
            
        Returns:
            GeneratedScript with segments
        """
        logger.info(f"Generating {config.content_mode} script for {config.audience.maturity} audience")
        
        prompt = self._build_prompt(config, refined_idea)
        
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
                logger.error(f"Script generation failed: {e}")
                return self._mock_script(config, refined_idea)
        else:
            return self._mock_script(config, refined_idea)
    
    def _build_prompt(self, config: GenerationConfig, refined_idea: str) -> str:
        """Build the complete generation prompt."""
        sections = []
        
        # Core instructions
        sections.append(f"""
GENERATE A {config.duration_seconds}-SECOND SCRIPT

TOPIC: {refined_idea}
""")
        
        # Generation instructions from config
        sections.append(config.get_generation_instructions())
        
        # Mode-specific prompt
        mode_prompt = self.MODE_PROMPTS.get(config.content_mode, "")
        if mode_prompt:
            sections.append(mode_prompt)
        
        # Persona-specific prompt
        if config.persona:
            persona_prompt = self.PERSONA_PROMPTS.get(config.persona, "")
            if persona_prompt:
                sections.append(persona_prompt)
        
        # Language enforcement
        sections.append(f"""
⚠️ CRITICAL LANGUAGE RULE:
Generate the script DIRECTLY in {config.audience.language}.
Do NOT write in English and translate.
Think in {config.audience.language}. Write in {config.audience.language}.
Use idioms and expressions native to {config.audience.cultural_context} culture.
""")
        
        # Output format
        sections.append("""
OUTPUT FORMAT (JSON):
[
    {
        "text": "The script text for this segment",
        "duration_seconds": 5,
        "visual_direction": "Visual description for this segment",
        "tone": "The emotional tone (sarcastic, deadpan, energetic, etc)"
    },
    ...
]

Generate enough segments to fill the target duration.
Each segment should be 3-8 seconds.
""")
        
        return "\n".join(sections)
    
    def _parse_response(self, response_text: str, config: GenerationConfig) -> GeneratedScript:
        """Parse LLM response into GeneratedScript."""
        try:
            # Extract JSON
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("No JSON array found")
            
            segments = [
                ScriptSegment(
                    text=item.get("text", ""),
                    duration_seconds=item.get("duration_seconds", 5),
                    visual_direction=item.get("visual_direction", ""),
                    tone=item.get("tone", "neutral")
                )
                for item in data
            ]
            
            total_duration = sum(s.duration_seconds for s in segments)
            
            return GeneratedScript(
                segments=segments,
                total_duration=total_duration,
                language=config.audience.language,
                mode=config.content_mode,
                persona=config.persona
            )
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return self._mock_script(config, "Parse error fallback")
    
    def _mock_script(self, config: GenerationConfig, idea: str) -> GeneratedScript:
        """Generate mock script for testing."""
        if config.content_mode == ContentMode.COMEDY.value:
            segments = [
                ScriptSegment("You know what's funny about this?", 3, "Speaker looking at camera", "setup"),
                ScriptSegment("Everyone's doing it wrong.", 3, "Slow zoom in", "deadpan"),
                ScriptSegment("Here's what actually works...", 4, "Quick montage", "revelation"),
                ScriptSegment("And that's why I gave up.", 3, "Speaker shrugging", "punchline"),
            ]
        elif config.content_mode == ContentMode.COMMENTARY.value:
            segments = [
                ScriptSegment("Hot take: this is getting out of control.", 4, "Bold text overlay", "provocative"),
                ScriptSegment("The data shows one thing, the narrative shows another.", 5, "Charts and graphs", "analytical"),
                ScriptSegment("Here's what nobody wants to admit.", 4, "Close-up", "direct"),
                ScriptSegment("Make up your own mind.", 3, "Fade to black", "conclusive"),
            ]
        else:
            segments = [
                ScriptSegment("Let me break this down.", 3, "Speaker gesturing", "casual"),
                ScriptSegment("Most explanations overcomplicate this.", 4, "Simple diagram", "clear"),
                ScriptSegment("The core insight is this.", 5, "Key point highlight", "focused"),
                ScriptSegment("Now you know more than 90% of people.", 3, "Confident nod", "empowering"),
            ]
        
        return GeneratedScript(
            segments=segments,
            total_duration=sum(s.duration_seconds for s in segments),
            language=config.audience.language,
            mode=config.content_mode,
            persona=config.persona
        )


# Singleton
_engine = None

def get_script_engine() -> ScriptEngine:
    global _engine
    if _engine is None:
        _engine = ScriptEngine()
    return _engine


def generate_direct_script(config: GenerationConfig, refined_idea: str) -> Dict:
    """
    Generate script directly (bypassing story engine).
    
    Args:
        config: Generation configuration
        refined_idea: Path 1 refined idea
        
    Returns:
        Generated script as dict
    """
    engine = get_script_engine()
    script = engine.generate_script(config, refined_idea)
    return script.to_dict()

"""
Week 16 - Simplified Audience Baseline
Adult-grade content by DEFAULT without complex audience targeting.
Remove kid assumptions. Assert intelligence baseline.
"""
from typing import Optional
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field


class AudienceBaseline(str, Enum):
    """Simple audience baseline - NOT targeting, just removing kid assumptions."""
    GENERAL_ADULT = "general_adult"  # Default - intelligent viewer, no spoon-feeding
    KIDS = "kids"                     # Fairy-tales, simple language, morals
    EXPERT = "expert"                 # Deep knowledge assumed, jargon allowed


class Tone(str, Enum):
    """Simple tone control without persona explosion."""
    NEUTRAL = "neutral"   # Confident, concise, adult (NOT childish)
    SHARP = "sharp"       # Incisive, cutting, no fluff
    BOLD = "bold"         # Provocative, assertive, controversial
    PLAYFUL = "playful"   # Light, witty, fun (still adult)


class SimpleConfig(BaseModel):
    """
    Simplified configuration for Week 16.
    Produces adult-grade content WITHOUT full audience selection.
    """
    # Core required fields
    topic: str = Field(..., min_length=3, description="Content topic/idea")
    
    # Baseline - defaults to adult
    audience_baseline: AudienceBaseline = Field(
        default=AudienceBaseline.GENERAL_ADULT,
        description="Audience baseline (default: general_adult)"
    )
    
    # Tone - defaults to neutral (adult neutral, not childish)
    tone: Tone = Field(
        default=Tone.NEUTRAL,
        description="Content tone"
    )
    
    # Language - for native generation
    language: str = Field(
        default="en",
        description="Language code for DIRECT generation (not translation)"
    )
    
    # Duration
    duration_seconds: int = Field(
        default=30,
        ge=15,
        le=180
    )
    
    class Config:
        use_enum_values = True
    
    def get_content_mode(self) -> str:
        """Auto-determine content mode based on baseline."""
        if self.audience_baseline == AudienceBaseline.KIDS.value:
            return "story"
        else:
            # Adults get commentary or explainer, NOT story
            return "commentary"
    
    def is_adult(self) -> bool:
        return self.audience_baseline in [
            AudienceBaseline.GENERAL_ADULT.value,
            AudienceBaseline.EXPERT.value
        ]
    
    def get_generation_rules(self) -> str:
        """Get hard rules for generation based on baseline."""
        rules = []
        
        if self.is_adult():
            rules.append("""
⚠️ ADULT BASELINE RULES (MANDATORY):
- Assume viewer is INTELLIGENT
- Skip basic explanations
- NO fairy-tale stories
- NO morals or lessons at the end
- NO teaching or lecturing tone
- NO summarizing what you just said
- NO defining common words
- Be DIRECT and CONFIDENT
""")
        else:
            # Kids mode
            rules.append("""
🧒 KIDS MODE RULES:
- Use story structure with characters
- Simple, clear language
- Explain concepts gently
- Include moral or lesson
- Engaging and magical tone
""")
        
        # Tone-specific rules
        if self.tone == Tone.SHARP.value:
            rules.append("""
TONE: SHARP
- Be incisive and cutting
- No fluff, no padding
- Challenge weak ideas
- Get to the point fast
""")
        elif self.tone == Tone.BOLD.value:
            rules.append("""
TONE: BOLD
- Make strong claims
- Be provocative where appropriate
- Don't hedge everything
- Take a clear position
""")
        elif self.tone == Tone.PLAYFUL.value:
            rules.append("""
TONE: PLAYFUL
- Witty and light
- Still intelligent, not childish
- Clever wordplay allowed
- Have fun with it
""")
        else:  # NEUTRAL
            rules.append("""
TONE: NEUTRAL (adult neutral, NOT childish)
- Confident and concise
- Clear without over-explaining
- Professional but not stiff
- Assume intelligence
""")
        
        # Language rule
        rules.append(f"""
LANGUAGE: {self.language}
Generate DIRECTLY in {self.language}.
Think in {self.language}. Write in {self.language}.
Do NOT write in English and translate.
Use native idioms and expressions.
""")
        
        return "\n".join(rules)


# Anti-patterns to remove from generation
KILL_OVER_EXPLANATION_RULES = """
❌ DO NOT (these make content feel childish):
- Explain obvious things
- Define common words
- Say "let me explain..."
- Summarize at the end with "so in conclusion..."
- Give moral lessons ("and that's why we should...")
- Use filler phrases ("you know", "basically", "actually")
- Repeat points you just made
- Treat viewer like they don't know anything
"""


@dataclass 
class BaselineThresholds:
    """Path 1 thresholds based on audience baseline."""
    auto_accept: float
    auto_reject: float
    allow_ambiguity: bool
    allow_assumptions: bool
    allow_controversy: bool
    
    @classmethod
    def for_baseline(cls, baseline: AudienceBaseline) -> 'BaselineThresholds':
        """Get thresholds appropriate for baseline."""
        if baseline == AudienceBaseline.GENERAL_ADULT.value:
            return cls(
                auto_accept=0.65,
                auto_reject=0.25,
                allow_ambiguity=True,
                allow_assumptions=True,
                allow_controversy=True
            )
        elif baseline == AudienceBaseline.EXPERT.value:
            return cls(
                auto_accept=0.60,
                auto_reject=0.20,
                allow_ambiguity=True,
                allow_assumptions=True,
                allow_controversy=True
            )
        else:  # KIDS
            return cls(
                auto_accept=0.80,
                auto_reject=0.45,
                allow_ambiguity=False,
                allow_assumptions=False,
                allow_controversy=False
            )


def create_simple_config(
    topic: str,
    audience_baseline: str = "general_adult",
    tone: str = "neutral",
    language: str = "en",
    duration_seconds: int = 30
) -> SimpleConfig:
    """
    Create a simple config with adult defaults.
    
    Args:
        topic: Content topic
        audience_baseline: "general_adult" (default), "kids", or "expert"
        tone: "neutral" (default), "sharp", "bold", or "playful"
        language: Language code (default "en")
        duration_seconds: Duration (default 30)
        
    Returns:
        SimpleConfig ready for generation
    """
    return SimpleConfig(
        topic=topic,
        audience_baseline=AudienceBaseline(audience_baseline),
        tone=Tone(tone),
        language=language,
        duration_seconds=duration_seconds
    )

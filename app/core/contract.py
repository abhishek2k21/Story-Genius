"""
Week 17 - Generation Contract
The ONE source of truth for all generation.
Every model, tool, pipeline must obey this contract.
"""
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


class AudienceBaseline(str, Enum):
    """Audience baseline - simple, not complex targeting."""
    GENERAL_ADULT = "general_adult"  # Default - intelligent viewer
    KIDS = "kids"                     # Fairy-tales, morals
    EXPERT = "expert"                 # Deep knowledge assumed


class Intent(str, Enum):
    """Content intent."""
    AUTO = "auto"         # System decides based on context
    ENTERTAIN = "entertain"
    EDUCATE = "educate"
    PERSUADE = "persuade"
    PROVOKE = "provoke"
    INSPIRE = "inspire"


class ContentMode(str, Enum):
    """Content structure mode."""
    AUTO = "auto"              # System decides (NOT story for adults)
    STORY = "story"            # Narrative arc (kids, fiction)
    COMMENTARY = "commentary"  # Opinion, analysis (adults)
    EXPLAINER = "explainer"    # How-to, facts


class Tone(str, Enum):
    """Content tone."""
    NEUTRAL = "neutral"   # Confident, concise, adult
    SHARP = "sharp"       # Incisive, no fluff
    BOLD = "bold"         # Provocative, assertive
    PLAYFUL = "playful"   # Witty, light


class QualityMode(str, Enum):
    """Quality vs speed tradeoff."""
    FAST = "fast"         # Quick generation, acceptable quality
    BALANCED = "balanced" # Default - good quality, reasonable speed
    PREMIUM = "premium"   # Best quality, slower


class GenerationContract(BaseModel):
    """
    THE ONE CONTRACT.
    Every generation must follow this.
    No random defaults. Source of truth.
    """
    # Required
    idea: str = Field(..., min_length=3, description="The content idea")
    
    # Defaults that assert authority
    audience_baseline: AudienceBaseline = Field(
        default=AudienceBaseline.GENERAL_ADULT,
        description="Audience baseline (default: adult)"
    )
    intent: Intent = Field(
        default=Intent.AUTO,
        description="Content intent (default: auto-determined)"
    )
    content_mode: ContentMode = Field(
        default=ContentMode.AUTO,
        description="Content mode (default: auto - NOT story for adults)"
    )
    tone: Tone = Field(
        default=Tone.NEUTRAL,
        description="Content tone (default: neutral = confident, not childish)"
    )
    language: str = Field(
        default="auto",
        description="Language code or 'auto' for English"
    )
    quality_mode: QualityMode = Field(
        default=QualityMode.BALANCED,
        description="Quality vs speed tradeoff"
    )
    
    # Optional overrides
    duration_seconds: int = Field(default=30, ge=15, le=180)
    
    class Config:
        use_enum_values = True
    
    def resolve_language(self) -> str:
        """Resolve 'auto' to default language."""
        return "en" if self.language == "auto" else self.language
    
    def resolve_content_mode(self) -> str:
        """
        Resolve 'auto' content mode.
        Day 2 Rule: NOT story for adults.
        """
        if self.content_mode != ContentMode.AUTO.value:
            return self.content_mode
        
        # Auto logic
        if self.audience_baseline == AudienceBaseline.KIDS.value:
            return ContentMode.STORY.value
        elif self.intent == Intent.EDUCATE.value and self.audience_baseline == AudienceBaseline.KIDS.value:
            return ContentMode.STORY.value
        else:
            # Adults get commentary/explainer, NOT story
            return ContentMode.COMMENTARY.value
    
    def resolve_intent(self) -> str:
        """Resolve 'auto' intent."""
        if self.intent != Intent.AUTO.value:
            return self.intent
        
        # Default to entertain for adults, educate for kids
        if self.audience_baseline == AudienceBaseline.KIDS.value:
            return Intent.EDUCATE.value
        else:
            return Intent.ENTERTAIN.value
    
    def is_adult(self) -> bool:
        return self.audience_baseline in [
            AudienceBaseline.GENERAL_ADULT.value,
            AudienceBaseline.EXPERT.value
        ]
    
    def get_tone_rules(self) -> str:
        """Day 3: Tone Authority rules."""
        if self.is_adult():
            return """
TONE AUTHORITY (MANDATORY FOR ADULT CONTENT):
- Assume viewer is INTELLIGENT
- Skip basic explanations
- Do NOT moralize
- Do NOT summarize
- Be DIRECT and CONFIDENT
- Kid content explains. Adult content assumes.
"""
        else:
            return """
KIDS TONE RULES:
- Explain concepts simply
- Use story structure
- Include gentle moral
- Warm and engaging
"""
    
    def get_language_rule(self) -> str:
        """Day 5: Language First Rule."""
        lang = self.resolve_language()
        return f"""
LANGUAGE FIRST RULE (CRITICAL):
Generate script DIRECTLY in {lang}.
Never: English → Translate
Think in {lang}. Write in {lang}.
Translated thinking feels fake.
Native thinking feels confident.
"""
    
    def to_generation_prompt(self) -> str:
        """Get full generation prompt based on contract."""
        resolved_mode = self.resolve_content_mode()
        resolved_intent = self.resolve_intent()
        resolved_lang = self.resolve_language()
        
        prompt = f"""
GENERATION CONTRACT
===================
Idea: {self.idea}
Audience: {self.audience_baseline}
Intent: {resolved_intent}
Content Mode: {resolved_mode}
Tone: {self.tone}
Language: {resolved_lang}
Duration: {self.duration_seconds}s

{self.get_tone_rules()}

{self.get_language_rule()}
"""
        
        # Add mode-specific rules
        if resolved_mode == ContentMode.STORY.value:
            prompt += """
MODE: STORY
- Narrative arc with characters
- Plot with conflict and resolution
- Appropriate for target audience
"""
        else:
            prompt += """
MODE: COMMENTARY/EXPLAINER (NOT STORY)
- Strong hook in first 3 seconds
- Make point clearly
- NO plot, NO characters, NO narrative arc
- End with takeaway (NOT moral)
"""
        
        return prompt


# Locked defaults (Day 7)
LOCKED_DEFAULTS = {
    "audience_baseline": "general_adult",
    "content_mode": "auto",
    "tone": "neutral",
    "language": "auto",
    "quality_mode": "balanced"
}


def create_contract(
    idea: str,
    audience_baseline: str = "general_adult",
    intent: str = "auto",
    content_mode: str = "auto",
    tone: str = "neutral",
    language: str = "auto",
    quality_mode: str = "balanced",
    duration_seconds: int = 30
) -> GenerationContract:
    """
    Create a generation contract.
    Uses locked defaults that assert authority.
    """
    return GenerationContract(
        idea=idea,
        audience_baseline=AudienceBaseline(audience_baseline),
        intent=Intent(intent),
        content_mode=ContentMode(content_mode),
        tone=Tone(tone),
        language=language,
        quality_mode=QualityMode(quality_mode),
        duration_seconds=duration_seconds
    )


def validate_contract(contract_dict: dict) -> GenerationContract:
    """Validate and create contract from dict."""
    if "idea" not in contract_dict:
        raise ValueError("Contract requires 'idea' field")
    return GenerationContract(**contract_dict)

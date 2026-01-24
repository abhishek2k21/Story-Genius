"""
Week 15 - Global Mode Configuration
Mandatory audience profiles, intent locks, content modes, and personas.
NO DEFAULTS. NO FALLBACKS. NO GUESSING.
"""
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field, validator


class AgeGroup(str, Enum):
    """Target age groups."""
    KIDS = "kids"           # 5-12
    TEENS = "teens"         # 13-17
    YOUNG_ADULT = "18-35"   # 18-35
    ADULT = "35-55"         # 35-55
    MATURE = "55+"          # 55+


class Maturity(str, Enum):
    """Content maturity level."""
    KIDS = "kids"
    TEEN = "teen"
    ADULT = "adult"


class Region(str, Enum):
    """Target region."""
    US = "US"
    UK = "UK"
    INDIA = "India"
    GLOBAL = "global"
    LATAM = "LATAM"
    EUROPE = "Europe"
    ASIA = "Asia"
    MENA = "MENA"


class AttentionStyle(str, Enum):
    """How the audience consumes content."""
    FAST = "fast"           # TikTok/Reels style
    MEDIUM = "medium"       # YouTube Shorts
    SLOW = "slow"           # Long-form attention


class Intent(str, Enum):
    """Why we're creating this content."""
    ENTERTAIN = "entertain"   # Comedy, fun, engagement
    EDUCATE = "educate"       # Teaching, facts, learning
    PERSUADE = "persuade"     # Selling, convincing
    PROVOKE = "provoke"       # Commentary, hot takes, controversy
    INSPIRE = "inspire"       # Motivation, emotion, aspiration


class ContentMode(str, Enum):
    """Content structure mode."""
    STORY = "story"           # Narrative arc (kids, fiction)
    COMMENTARY = "commentary" # Opinion, analysis (adults)
    EXPLAINER = "explainer"   # How-to, facts (all ages)
    COMEDY = "comedy"         # Jokes, humor (adult)


class AdultPersona(str, Enum):
    """Adult content personas - NO STORIES."""
    DRY_COMEDIAN = "dry_comedian"       # Sarcasm, no morals, punchlines > plot
    SHARP_ANALYST = "sharp_analyst"     # Claim → evidence → takeaway, no emotions
    STREET_EXPLAINER = "street_explainer"  # Casual, cultural refs, smart audience


class AudienceProfile(BaseModel):
    """
    MANDATORY audience profile. No defaults. No fallbacks.
    """
    age_group: AgeGroup = Field(..., description="Target age group")
    region: Region = Field(..., description="Target region/market")
    language: str = Field(..., min_length=2, max_length=10, description="Language code (en, hi, es, etc)")
    maturity: Maturity = Field(..., description="Content maturity level")
    cultural_context: str = Field(..., description="Cultural context (western, indian, global, etc)")
    attention_style: AttentionStyle = Field(..., description="How audience consumes content")

    class Config:
        use_enum_values = True

    def is_adult(self) -> bool:
        return self.maturity == Maturity.ADULT.value or self.maturity == "adult"
    
    def is_kids(self) -> bool:
        return self.maturity == Maturity.KIDS.value or self.maturity == "kids"
    
    def allows_cultural_references(self) -> bool:
        return self.region != Region.GLOBAL.value


class GenerationConfig(BaseModel):
    """
    Complete generation configuration. ALL FIELDS REQUIRED.
    """
    audience: AudienceProfile = Field(..., description="MANDATORY audience profile")
    intent: Intent = Field(..., description="Why are we creating this?")
    content_mode: ContentMode = Field(..., description="Content structure")
    persona: Optional[AdultPersona] = Field(None, description="Adult persona (required for adult content)")
    
    # Content specifics
    topic: str = Field(..., min_length=5, description="The content topic/idea")
    duration_seconds: int = Field(30, ge=15, le=180, description="Target duration")
    
    class Config:
        use_enum_values = True
    
    @validator('persona', always=True)
    def require_persona_for_adults(cls, v, values):
        """Adult content MUST have a persona."""
        audience = values.get('audience')
        content_mode = values.get('content_mode')
        
        if audience and audience.is_adult() and content_mode != ContentMode.STORY.value:
            if v is None:
                raise ValueError("Adult non-story content REQUIRES a persona. Choose: dry_comedian, sharp_analyst, or street_explainer")
        return v
    
    @validator('content_mode', always=True)
    def validate_content_mode(cls, v, values):
        """Kids should use story mode, adults usually not."""
        audience = values.get('audience')
        if audience and audience.is_kids() and v != ContentMode.STORY.value:
            # Allow but warn - kids can have explainers too
            pass
        return v
    
    def get_generation_instructions(self) -> str:
        """Generate specific instructions based on config."""
        instructions = []
        
        # Audience-specific
        instructions.append(f"AUDIENCE: {self.audience.age_group}, {self.audience.region}, {self.audience.maturity} maturity")
        instructions.append(f"LANGUAGE: Generate DIRECTLY in {self.audience.language} - do NOT translate from English")
        instructions.append(f"CULTURAL CONTEXT: {self.audience.cultural_context}")
        
        # Intent-specific
        if self.intent == Intent.ENTERTAIN.value:
            instructions.append("INTENT: Entertain - prioritize humor, engagement, fun. No lectures.")
        elif self.intent == Intent.EDUCATE.value:
            instructions.append("INTENT: Educate - deliver knowledge, but match audience level. " +
                              ("Simple and magical for kids." if self.audience.is_kids() else "Assume intelligence. No basics."))
        elif self.intent == Intent.PROVOKE.value:
            instructions.append("INTENT: Provoke - hot takes allowed. Controversy is fine. Challenge assumptions.")
        elif self.intent == Intent.INSPIRE.value:
            instructions.append("INTENT: Inspire - emotional, aspirational, genuine. Not preachy.")
        elif self.intent == Intent.PERSUADE.value:
            instructions.append("INTENT: Persuade - make a case. Evidence matters. Clear CTA.")
        
        # Content mode
        if self.content_mode == ContentMode.STORY.value:
            instructions.append("MODE: Story - narrative arc, characters, plot. Good for kids.")
        elif self.content_mode == ContentMode.COMMENTARY.value:
            instructions.append("MODE: Commentary - opinion, analysis, no plot. Claim → evidence → conclusion.")
        elif self.content_mode == ContentMode.EXPLAINER.value:
            instructions.append("MODE: Explainer - facts, how-to, clear structure. No fluff.")
        elif self.content_mode == ContentMode.COMEDY.value:
            instructions.append("MODE: Comedy - jokes, timing, punchlines. Subvert expectations.")
        
        # Persona for adults
        if self.persona:
            if self.persona == AdultPersona.DRY_COMEDIAN.value:
                instructions.append("PERSONA: Dry Comedian - sarcasm allowed, NO morals, punchlines > plot, deadpan delivery")
            elif self.persona == AdultPersona.SHARP_ANALYST.value:
                instructions.append("PERSONA: Sharp Analyst - claim → evidence → takeaway, NO characters, NO emotions unless justified")
            elif self.persona == AdultPersona.STREET_EXPLAINER.value:
                instructions.append("PERSONA: Street Explainer - casual language, cultural references, assume viewer is SMART")
        
        # Hard rules for adults
        if self.audience.is_adult() and self.content_mode != ContentMode.STORY.value:
            instructions.append("\n⚠️ ADULT RULES:")
            instructions.append("❌ NO story arcs or 'once upon a time' structure")
            instructions.append("❌ NO explaining basics - assume intelligence")
            instructions.append("❌ NO lessons or morals at the end")
            instructions.append("✅ BE opinionated, direct, confident")
        
        return "\n".join(instructions)


# Pre-built profiles for common use cases
PRESET_PROFILES = {
    "kids_india": AudienceProfile(
        age_group=AgeGroup.KIDS,
        region=Region.INDIA,
        language="hi",
        maturity=Maturity.KIDS,
        cultural_context="indian",
        attention_style=AttentionStyle.MEDIUM
    ),
    "adult_us": AudienceProfile(
        age_group=AgeGroup.YOUNG_ADULT,
        region=Region.US,
        language="en",
        maturity=Maturity.ADULT,
        cultural_context="western",
        attention_style=AttentionStyle.FAST
    ),
    "genz_global": AudienceProfile(
        age_group=AgeGroup.TEENS,
        region=Region.GLOBAL,
        language="en",
        maturity=Maturity.ADULT,
        cultural_context="internet",
        attention_style=AttentionStyle.FAST
    ),
    "adult_india": AudienceProfile(
        age_group=AgeGroup.YOUNG_ADULT,
        region=Region.INDIA,
        language="hi",
        maturity=Maturity.ADULT,
        cultural_context="indian",
        attention_style=AttentionStyle.FAST
    ),
}


def validate_generation_config(config: dict) -> GenerationConfig:
    """
    Validate and create a GenerationConfig from dict.
    Raises ValueError if any required field is missing.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated GenerationConfig
        
    Raises:
        ValueError: If required fields are missing
    """
    # Check for required top-level fields
    required = ['audience', 'intent', 'content_mode', 'topic']
    missing = [f for f in required if f not in config]
    
    if missing:
        raise ValueError(f"GENERATION REJECTED: Missing required fields: {missing}. "
                        "No defaults. No fallbacks. No guessing.")
    
    # Check audience has all required fields
    if isinstance(config['audience'], dict):
        audience_required = ['age_group', 'region', 'language', 'maturity', 'cultural_context', 'attention_style']
        audience_missing = [f for f in audience_required if f not in config['audience']]
        if audience_missing:
            raise ValueError(f"GENERATION REJECTED: Audience profile missing: {audience_missing}. "
                            "You MUST define your audience completely.")
    
    return GenerationConfig(**config)

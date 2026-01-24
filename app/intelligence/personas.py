"""
Persona System
Defines brand-like personas for consistent content generation.
Each persona controls tone, vocabulary, pacing, and voice.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List

from app.core.logging import get_logger

logger = get_logger(__name__)


class EnergyLevel(str, Enum):
    """Narration energy levels."""
    CALM = "calm"
    MODERATE = "moderate"
    HIGH = "high"
    INTENSE = "intense"


class VocabularyLevel(str, Enum):
    """Vocabulary complexity levels."""
    SIMPLE = "simple"       # Ages 5-8
    MODERATE = "moderate"   # Ages 9-14
    ADVANCED = "advanced"   # Ages 15+


class SentenceLength(str, Enum):
    """Preferred sentence length."""
    SHORT = "short"         # 3-6 words per sentence
    MEDIUM = "medium"       # 7-12 words per sentence
    LONG = "long"           # 13+ words per sentence


@dataclass
class Persona:
    """
    A brand-like persona that defines content style.
    """
    id: str
    name: str
    description: str
    
    # Voice characteristics
    sentence_length: SentenceLength
    energy_level: EnergyLevel
    vocabulary: VocabularyLevel
    
    # TTS configuration
    voice_id: str
    speaking_rate: float = 1.0  # 0.8 = slower, 1.2 = faster
    
    # Prompt modifiers
    tone_keywords: List[str] = field(default_factory=list)
    avoid_words: List[str] = field(default_factory=list)
    
    # Visual style
    visual_style_prefix: str = ""
    
    def get_prompt_modifier(self) -> str:
        """Generate prompt modifier based on persona."""
        modifiers = []
        
        # Sentence length
        if self.sentence_length == SentenceLength.SHORT:
            modifiers.append("Use very short, punchy sentences (3-6 words max).")
        elif self.sentence_length == SentenceLength.LONG:
            modifiers.append("Use flowing, descriptive sentences.")
        
        # Energy
        if self.energy_level == EnergyLevel.CALM:
            modifiers.append("Keep a calm, soothing tone.")
        elif self.energy_level == EnergyLevel.HIGH:
            modifiers.append("Be energetic and exciting!")
        elif self.energy_level == EnergyLevel.INTENSE:
            modifiers.append("Maximum energy! Fast pace!")
        
        # Vocabulary
        if self.vocabulary == VocabularyLevel.SIMPLE:
            modifiers.append("Use simple words a 6-year-old would understand.")
        elif self.vocabulary == VocabularyLevel.ADVANCED:
            modifiers.append("Use sophisticated vocabulary.")
        
        # Tone keywords
        if self.tone_keywords:
            modifiers.append(f"Tone: {', '.join(self.tone_keywords)}")
        
        return " ".join(modifiers)


# ============== PERSONA DEFINITIONS ==============

PERSONAS: Dict[str, Persona] = {
    "curious_kid": Persona(
        id="curious_kid",
        name="Curious Kid",
        description="Wonder-filled, question-asking, excited about discovery",
        sentence_length=SentenceLength.SHORT,
        energy_level=EnergyLevel.HIGH,
        vocabulary=VocabularyLevel.SIMPLE,
        voice_id="en-US-AnaNeural",
        speaking_rate=1.1,
        tone_keywords=["wonder", "excitement", "playful", "curious"],
        avoid_words=["actually", "basically", "obviously"],
        visual_style_prefix="Colorful, cartoon-style, bright and cheerful"
    ),
    
    "fast_explainer": Persona(
        id="fast_explainer",
        name="Fast Explainer",
        description="Quick facts, punchy delivery, no fluff",
        sentence_length=SentenceLength.SHORT,
        energy_level=EnergyLevel.INTENSE,
        vocabulary=VocabularyLevel.MODERATE,
        voice_id="en-US-GuyNeural",
        speaking_rate=1.3,
        tone_keywords=["direct", "punchy", "factual", "rapid"],
        avoid_words=["um", "so", "like"],
        visual_style_prefix="Dynamic, fast cuts, bold text overlays"
    ),
    
    "storyteller": Persona(
        id="storyteller",
        name="Storyteller",
        description="Narrative-driven, emotional, immersive",
        sentence_length=SentenceLength.MEDIUM,
        energy_level=EnergyLevel.MODERATE,
        vocabulary=VocabularyLevel.MODERATE,
        voice_id="en-GB-RyanNeural",
        speaking_rate=0.95,
        tone_keywords=["narrative", "emotional", "immersive", "dramatic"],
        avoid_words=[],
        visual_style_prefix="Cinematic, atmospheric, story-focused"
    ),
    
    "hype_master": Persona(
        id="hype_master",
        name="Hype Master",
        description="Maximum energy, motivational, alpha vibes",
        sentence_length=SentenceLength.SHORT,
        energy_level=EnergyLevel.INTENSE,
        vocabulary=VocabularyLevel.MODERATE,
        voice_id="en-US-ChristopherNeural",
        speaking_rate=1.2,
        tone_keywords=["powerful", "motivational", "urgent", "commanding"],
        avoid_words=["maybe", "perhaps", "could"],
        visual_style_prefix="High contrast, luxury aesthetic, bold"
    ),
    
    "gentle_guide": Persona(
        id="gentle_guide",
        name="Gentle Guide",
        description="Calm, reassuring, educational but soft",
        sentence_length=SentenceLength.MEDIUM,
        energy_level=EnergyLevel.CALM,
        vocabulary=VocabularyLevel.SIMPLE,
        voice_id="en-US-MichelleNeural",
        speaking_rate=0.9,
        tone_keywords=["calm", "reassuring", "gentle", "warm"],
        avoid_words=["scary", "dangerous", "terrible"],
        visual_style_prefix="Soft lighting, pastel colors, peaceful"
    )
}


class PersonaService:
    """
    Service for selecting and applying personas to content.
    """
    
    # Audience → Persona mapping
    AUDIENCE_PERSONA_MAP = {
        "kids_india": "curious_kid",
        "kids": "curious_kid",
        "children": "curious_kid",
        "genz": "fast_explainer",
        "genz_us": "fast_explainer",
        "facts": "fast_explainer",
        "educational": "fast_explainer",
        "motivation": "hype_master",
        "success": "hype_master",
        "bedtime": "gentle_guide",
        "relaxation": "gentle_guide",
        "story": "storyteller",
        "narrative": "storyteller"
    }
    
    # Genre → Persona mapping
    GENRE_PERSONA_MAP = {
        "kids": "curious_kid",
        "thriller": "storyteller",
        "scifi": "fast_explainer",
        "nature": "storyteller",
        "history": "storyteller",
        "motivation": "hype_master",
        "bedtime": "gentle_guide",
        "comedy": "fast_explainer",
        "noir": "storyteller",
        "romance": "gentle_guide"
    }
    
    @classmethod
    def get_persona(cls, persona_id: str) -> Optional[Persona]:
        """Get persona by ID."""
        return PERSONAS.get(persona_id)
    
    @classmethod
    def select_persona(
        cls,
        audience: str = None,
        genre: str = None,
        persona_id: str = None
    ) -> Persona:
        """
        Select appropriate persona based on audience and genre.
        
        Args:
            audience: Target audience (e.g., "kids_india")
            genre: Content genre (e.g., "kids", "thriller")
            persona_id: Explicit persona ID override
            
        Returns:
            Selected Persona
        """
        # Explicit override
        if persona_id and persona_id in PERSONAS:
            logger.info(f"Using explicit persona: {persona_id}")
            return PERSONAS[persona_id]
        
        # Try audience mapping
        if audience:
            audience_key = audience.lower().replace("-", "_")
            if audience_key in cls.AUDIENCE_PERSONA_MAP:
                persona_id = cls.AUDIENCE_PERSONA_MAP[audience_key]
                logger.info(f"Selected persona '{persona_id}' for audience '{audience}'")
                return PERSONAS[persona_id]
        
        # Try genre mapping
        if genre:
            genre_key = genre.lower()
            if genre_key in cls.GENRE_PERSONA_MAP:
                persona_id = cls.GENRE_PERSONA_MAP[genre_key]
                logger.info(f"Selected persona '{persona_id}' for genre '{genre}'")
                return PERSONAS[persona_id]
        
        # Default
        logger.info("Using default persona: curious_kid")
        return PERSONAS["curious_kid"]
    
    @classmethod
    def list_personas(cls) -> List[str]:
        """List all available persona IDs."""
        return list(PERSONAS.keys())
    
    @classmethod
    def get_persona_summary(cls, persona: Persona) -> str:
        """Get a short summary of persona characteristics."""
        return f"{persona.name}: {persona.energy_level.value} energy, {persona.vocabulary.value} vocab, {persona.sentence_length.value} sentences"

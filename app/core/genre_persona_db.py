"""
Genre and Persona Database
Expanded database of 20+ genres and personas for content creation.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Genre:
    """Genre definition"""
    id: str
    name: str
    pacing_min: float  # beats per minute
    pacing_max: float
    pacing_optimal: float
    tone_profile: List[str]  # formal, casual, playful, serious
    emotion_trajectory: List[str]  # typical emotion flow
    story_beats_pattern: str  # typical story structure
    description: str


@dataclass
class Persona:
    """Persona definition"""
    id: str
    name: str
    voice_markers: List[str]  # linguistic markers
    tone_range: List[str]  # formal/casual spectrum
    vocabulary_style: str  # simple, technical, creative
    speaking_style: str  # descriptive
    typical_genres: List[str]  # genres this persona fits
    description: str


# Genre Database (20+ genres)
GENRE_DATABASE: Dict[str, Genre] = {
    "action": Genre(
        id="action",
        name="Action",
        pacing_min=5.0,
        pacing_max=7.0,
        pacing_optimal=6.0,
        tone_profile=["intense", "dynamic", "urgent"],
        emotion_trajectory=["anticipation", "excitement", "fear", "triumph"],
        story_beats_pattern="fast-escalation",
        description="High-energy content with rapid pacing and intense moments"
    ),
    "adventure": Genre(
        id="adventure",
        name="Adventure",
        pacing_min=4.0,
        pacing_max=6.0,
        pacing_optimal=5.0,
        tone_profile=["exciting", "curious", "optimistic"],
        emotion_trajectory=["curiosity", "anticipation", "wonder", "satisfaction"],
        story_beats_pattern="journey-structure",
        description="Exploratory content with discovery and progression"
    ),
    "comedy": Genre(
        id="comedy",
        name="Comedy",
        pacing_min=4.0,
        pacing_max=8.0,
        pacing_optimal=6.0,
        tone_profile=["humorous", "lighthearted", "playful"],
        emotion_trajectory=["amusement", "surprise", "joy", "delight"],
        story_beats_pattern="setup-punchline",
        description="Humorous content designed to entertain and amuse"
    ),
    "drama": Genre(
        id="drama",
        name="Drama",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["emotional", "serious", "contemplative"],
        emotion_trajectory=["tension", "conflict", "climax", "resolution"],
        story_beats_pattern="character-arc",
        description="Emotionally engaging content with character depth"
    ),
    "horror": Genre(
        id="horror",
        name="Horror",
        pacing_min=2.0,
        pacing_max=4.0,
        pacing_optimal=3.0,
        tone_profile=["dark", "suspenseful", "ominous"],
        emotion_trajectory=["unease", "anticipation", "fear", "shock"],
        story_beats_pattern="slow-burn",
        description="Suspenseful content building dread and fear"
    ),
    "thriller": Genre(
        id="thriller",
        name="Thriller",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["tense", "mysterious", "gripping"],
        emotion_trajectory=["curiosity", "suspense", "anxiety", "relief"],
        story_beats_pattern="mystery-reveal",
        description="Suspenseful content with twists and tension"
    ),
    "romance": Genre(
        id="romance",
        name="Romance",
        pacing_min=2.0,
        pacing_max=4.0,
        pacing_optimal=3.0,
        tone_profile=["warm", "intimate", "emotional"],
        emotion_trajectory=["attraction", "longing", "joy", "fulfillment"],
        story_beats_pattern="relationship-arc",
        description="Emotionally resonant content about relationships"
    ),
    "scifi": Genre(
        id="scifi",
        name="Science Fiction",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["speculative", "innovative", "thought-provoking"],
        emotion_trajectory=["wonder", "curiosity", "discovery", "insight"],
        story_beats_pattern="concept-exploration",
        description="Imaginative content exploring futuristic concepts"
    ),
    "fantasy": Genre(
        id="fantasy",
        name="Fantasy",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["magical", "epic", "imaginative"],
        emotion_trajectory=["wonder", "adventure", "triumph", "awe"],
        story_beats_pattern="hero-journey",
        description="Magical content with fantastical elements"
    ),
    "mystery": Genre(
        id="mystery",
        name="Mystery",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["intriguing", "puzzling", "clever"],
        emotion_trajectory=["curiosity", "confusion", "realization", "satisfaction"],
        story_beats_pattern="clue-revelation",
        description="Investigative content with puzzles to solve"
    ),
    "documentary": Genre(
        id="documentary",
        name="Documentary",
        pacing_min=2.0,
        pacing_max=4.0,
        pacing_optimal=3.0,
        tone_profile=["informative", "factual", "objective"],
        emotion_trajectory=["interest", "understanding", "insight", "enlightenment"],
        story_beats_pattern="informational-flow",
        description="Educational content presenting real-world information"
    ),
    "educational": Genre(
        id="educational",
        name="Educational",
        pacing_min=2.0,
        pacing_max=3.0,
        pacing_optimal=2.5,
        tone_profile=["instructive", "clear", "helpful"],
        emotion_trajectory=["curiosity", "understanding", "confidence", "mastery"],
        story_beats_pattern="learning-progression",
        description="Teaching content designed to educate and inform"
    ),
    # Additional genres
    "motivational": Genre(
        id="motivational",
        name="Motivational",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["inspiring", "uplifting", "empowering"],
        emotion_trajectory=["recognition", "aspiration", "determination", "empowerment"],
        story_beats_pattern="inspiration-action",
        description="Inspiring content to motivate and encourage"
    ),
    "inspirational": Genre(
        id="inspirational",
        name="Inspirational",
        pacing_min=2.5,
        pacing_max=4.0,
        pacing_optimal=3.0,
        tone_profile=["heartwarming", "uplifting", "positive"],
        emotion_trajectory=["connection", "hope", "joy", "inspiration"],
        story_beats_pattern="transformation-story",
        description="Uplifting content that inspires positive emotions"
    ),
    "lifestyle": Genre(
        id="lifestyle",
        name="Lifestyle",
        pacing_min=2.0,
        pacing_max=4.0,
        pacing_optimal=3.0,
        tone_profile=["casual", "relatable", "friendly"],
        emotion_trajectory=["interest", "aspiration", "satisfaction", "joy"],
        story_beats_pattern="showcase-tips",
        description="Content about daily life, habits, and trends"
    ),
    "tutorial": Genre(
        id="tutorial",
        name="Tutorial",
        pacing_min=2.0,
        pacing_max=3.0,
        pacing_optimal=2.5,
        tone_profile=["instructional", "clear", "step-by-step"],
        emotion_trajectory=["interest", "understanding", "accomplishment", "confidence"],
        story_beats_pattern="step-by-step",
        description="How-to content with clear instructions"
    ),
    "review": Genre(
        id="review",
        name="Review",
        pacing_min=3.0,
        pacing_max=5.0,
        pacing_optimal=4.0,
        tone_profile=["analytical", "honest", "informative"],
        emotion_trajectory=["curiosity", "evaluation", "opinion", "recommendation"],
        story_beats_pattern="assessment-verdict",
        description="Evaluative content assessing products or experiences"
    ),
    "vlog": Genre(
        id="vlog",
        name="Vlog",
        pacing_min=3.0,
        pacing_max=6.0,
        pacing_optimal=4.5,
        tone_profile=["personal", "casual", "authentic"],
        emotion_trajectory=["connection", "interest", "empathy", "engagement"],
        story_beats_pattern="daily-narrative",
        description="Personal content sharing daily experiences"
    ),
    "gaming": Genre(
        id="gaming",
        name="Gaming",
        pacing_min=4.0,
        pacing_max=7.0,
        pacing_optimal=5.5,
        tone_profile=["energetic", "entertaining", "competitive"],
        emotion_trajectory=["excitement", "tension", "triumph", "fun"],
        story_beats_pattern="gameplay-highlights",
        description="Gaming content with commentary and highlights"
    ),
    "technology": Genre(
        id="technology",
        name="Technology",
        pacing_min=2.5,
        pacing_max=4.5,
        pacing_optimal=3.5,
        tone_profile=["technical", "informative", "innovative"],
        emotion_trajectory=["curiosity", "understanding", "excitement", "insight"],
        story_beats_pattern="feature-analysis",
        description="Tech content explaining products and innovations"
    )
}


# Persona Database (20+ personas)
PERSONA_DATABASE: Dict[str, Persona] = {
    "influencer": Persona(
        id="influencer",
        name="Influencer",
        voice_markers=["you guys", "literally", "obsessed", "amazing"],
        tone_range=["casual", "enthusiastic", "personal"],
        vocabulary_style="trendy",
        speaking_style="Direct address, high energy, personal connection",
        typical_genres=["lifestyle", "vlog", "review"],
        description="Social media personality building personal brand"
    ),
    "educator": Persona(
        id="educator",
        name="Educator",
        voice_markers=["let's learn", "important to note", "remember", "concept"],
        tone_range=["informative", "clear", "patient"],
        vocabulary_style="academic",
        speaking_style="Clear explanations, structured presentation",
        typical_genres=["educational", "tutorial", "documentary"],
        description="Teacher-like personality focused on learning"
    ),
    "entertainer": Persona(
        id="entertainer",
        name="Entertainer",
        voice_markers=["check this out", "wait for it", "no way", "hilarious"],
        tone_range=["playful", "energetic", "fun"],
        vocabulary_style="casual",
        speaking_style="High energy, engaging, humorous",
        typical_genres=["comedy", "vlog", "gaming"],
        description="Performer focused on entertainment value"
    ),
    "storyteller": Persona(
        id="storyteller",
        name="Storyteller",
        voice_markers=["once upon", "imagine", "let me tell you", "the truth is"],
        tone_range=["narrative", "engaging", "emotional"],
        vocabulary_style="descriptive",
        speaking_style="Narrative flow, emotional connection",
        typical_genres=["drama", "adventure", "inspirational"],
        description="Narrative-focused content creator"
    ),
    "motivator": Persona(
        id="motivator",
        name="Motivator",
        voice_markers=["you can", "believe in yourself", "take action", "unstoppable"],
        tone_range=["inspiring", "empowering", "positive"],
        vocabulary_style="uplifting",
        speaking_style="Direct, empowering, action-oriented",
        typical_genres=["motivational", "inspirational", "lifestyle"],
        description="Inspirational speaker driving action"
    ),
    "expert": Persona(
        id="expert",
        name="Expert",
        voice_markers=["in my experience", "technically", "the key is", "fundamentally"],
        tone_range=["authoritative", "knowledgeable", "professional"],
        vocabulary_style="technical",
        speaking_style="Authoritative, detailed, credible",
        typical_genres=["tutorial", "technology", "documentary"],
        description="Subject matter expert sharing knowledge"
    ),
    "comedian": Persona(
        id="comedian",
        name="Comedian",
        voice_markers=["get this", "you know what's funny", "seriously though", "joke"],
        tone_range=["humorous", "witty", "sarcastic"],
        vocabulary_style="comedic",
        speaking_style="Comedic timing, punchlines, observational",
        typical_genres=["comedy", "entertainment", "vlog"],
        description="Humor-focused personality"
    ),
    "reviewer": Persona(
        id="reviewer",
        name="Reviewer",
        voice_markers=["my thoughts", "honestly", "pros and cons", "verdict"],
        tone_range=["analytical", "honest", "balanced"],
        vocabulary_style="evaluative",
        speaking_style="Balanced, analytical, opinion-focused",
        typical_genres=["review", "technology", "lifestyle"],
        description="Critical evaluator of products/experiences"
    ),
    "vlogger": Persona(
        id="vlogger",
        name="Vlogger",
        voice_markers=["good morning", "so today", "let me show you", "my life"],
        tone_range=["personal", "authentic", "relatable"],
        vocabulary_style="conversational",
        speaking_style="Personal diary style, authentic, casual",
        typical_genres=["vlog", "lifestyle", "daily"],
        description="Personal life documenter"
    ),
    "analyst": Persona(
        id="analyst",
        name="Analyst",
        voice_markers=["data shows", "analysis reveals", "evidence suggests", "conclusion"],
        tone_range=["analytical", "objective", "methodical"],
        vocabulary_style="academic",
        speaking_style="Data-driven, logical, systematic",
        typical_genres=["documentary", "technology", "review"],
        description="Data and analysis focused"
    ),
    # Additional personas
    "host": Persona(
        id="host",
        name="Host",
        voice_markers=["welcome back", "today on", "joining us", "thanks for watching"],
        tone_range=["professional", "welcoming", "structured"],
        vocabulary_style="broadcast",
        speaking_style="Professional hosting, structured segments",
        typical_genres=["documentary", "educational", "review"],
        description="Professional show host"
    ),
    "narrator": Persona(
        id="narrator",
        name="Narrator",
        voice_markers=["and so", "meanwhile", "as it turned out", "the story goes"],
        tone_range=["descriptive", "objective", "storytelling"],
        vocabulary_style="literary",
        speaking_style="Third-person narrative, descriptive",
        typical_genres=["documentary", "drama", "adventure"],
        description="Third-person storyteller"
    ),
    "guru": Persona(
        id="guru",
        name="Guru",
        voice_markers=["the secret is", "master this", "transform your", "unlock"],
        tone_range=["authoritative", "mystical", "wise"],
        vocabulary_style="transformative",
        speaking_style="Wisdom-sharing, transformative language",
        typical_genres=["motivational", "lifestyle", "educational"],
        description="Wisdom and transformation guide"
    ),
    "buddy": Persona(
        id="buddy",
        name="Buddy",
        voice_markers=["hey friend", "let's do this", "you and me", "together"],
        tone_range=["friendly", "supportive", "collaborative"],
        vocabulary_style="casual",
        speaking_style="Friend-to-friend, supportive, inclusive",
        typical_genres=["tutorial", "vlog", "gaming"],
        description="Friendly companion style"
    ),
    "professional": Persona(
        id="professional",
        name="Professional",
        voice_markers=["good day", "furthermore", "in conclusion", "professionally"],
        tone_range=["formal", "polished", "corporate"],
        vocabulary_style="business",
        speaking_style="Corporate, professional, polished",
        typical_genres=["business", "technology", "documentary"],
        description="Corporate professional"
    ),
    "rebel": Persona(
        id="rebel",
        name="Rebel",
        voice_markers=["screw that", "break the rules", "different", "unconventional"],
        tone_range=["edgy", "controversial", "bold"],
        vocabulary_style="provocative",
        speaking_style="Contrarian, bold, challenging norms",
        typical_genres=["comedy", "opinion", "lifestyle"],
        description="Rule-breaker, contrarian voice"
    ),
    "scientist": Persona(
        id="scientist",
        name="Scientist",
        voice_markers=["experiment", "hypothesis", "research shows", "scientifically"],
        tone_range=["scientific", "methodical", "curious"],
        vocabulary_style="scientific",
        speaking_style="Research-based, methodical, evidence-driven",
        typical_genres=["educational", "documentary", "technology"],
        description="Scientific method advocate"
    ),
    "artist": Persona(
        id="artist",
        name="Artist",
        voice_markers=["creative", "vision", "expression", "beauty"],
        tone_range=["creative", "expressive", "aesthetic"],
        vocabulary_style="artistic",
        speaking_style="Creative expression, aesthetic focus",
        typical_genres=["tutorial", "lifestyle", "inspirational"],
        description="Creative artistic voice"
    ),
    "gamer": Persona(
        id="gamer",
        name="Gamer",
        voice_markers=["let's go", "gg", "clutch", "epic win"],
        tone_range=["competitive", "energetic", "excited"],
        vocabulary_style="gaming",
        speaking_style="Gaming culture, competitive, energetic",
        typical_genres=["gaming", "entertainment", "tutorial"],
        description="Gaming culture enthusiast"
    ),
    "minimalist": Persona(
        id="minimalist",
        name="Minimalist",
        voice_markers=["simple", "essential", "less is more", "declutter"],
        tone_range=["calm", "intentional", "focused"],
        vocabulary_style="simple",
        speaking_style="Minimal, essential, focused",
        typical_genres=["lifestyle", "tutorial", "inspirational"],
        description="Simplicity advocate"
    )
}


def get_genre(genre_id: str) -> Optional[Genre]:
    """Get genre by ID"""
    return GENRE_DATABASE.get(genre_id.lower())


def get_persona(persona_id: str) -> Optional[Persona]:
    """Get persona by ID"""
    return PERSONA_DATABASE.get(persona_id.lower())


def list_genres() -> List[Genre]:
    """List all genres"""
    return list(GENRE_DATABASE.values())


def list_personas() -> List[Persona]:
    """List all personas"""
    return list(PERSONA_DATABASE.values())


def match_persona_to_genre(genre_id: str) -> List[Persona]:
    """Find personas that match a genre"""
    matching = []
    for persona in PERSONA_DATABASE.values():
        if genre_id.lower() in persona.typical_genres:
            matching.append(persona)
    return matching

"""
Emotion Curve Engine
Defines emotion timelines for pacing control and scene-emotion binding.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class Emotion(str, Enum):
    """Core emotions for short-form content pacing."""
    CURIOSITY = "curiosity"
    TENSION = "tension"
    SURPRISE = "surprise"
    JOY = "joy"
    FEAR = "fear"
    WONDER = "wonder"
    SHOCK = "shock"
    RELIEF = "relief"
    EXCITEMENT = "excitement"
    MYSTERY = "mystery"
    LOOP = "loop"  # Special: creates replay desire


@dataclass
class EmotionPoint:
    """A single point on the emotion timeline."""
    second: int
    emotion: Emotion
    intensity: float = 0.8  # 0.0 to 1.0
    
    
@dataclass
class EmotionCurve:
    """
    An emotion timeline for a video.
    Defines how emotions flow throughout the content.
    """
    id: str
    name: str
    description: str
    timeline: List[EmotionPoint]
    
    # Suitable for these contexts
    genres: List[str] = field(default_factory=list)
    audiences: List[str] = field(default_factory=list)
    
    def get_emotion_at(self, second: int) -> Optional[EmotionPoint]:
        """Get the emotion at a specific second."""
        # Find the point at or just before this second
        for i, point in enumerate(self.timeline):
            if point.second == second:
                return point
            if point.second > second and i > 0:
                return self.timeline[i - 1]
        return self.timeline[-1] if self.timeline else None
    
    def get_emotion_for_scene(self, start_sec: int, end_sec: int) -> Emotion:
        """Get the dominant emotion for a scene timespan."""
        point = self.get_emotion_at(start_sec)
        return point.emotion if point else Emotion.CURIOSITY
    
    def to_prompt_guidance(self) -> str:
        """Convert curve to prompt guidance string."""
        segments = []
        for point in self.timeline:
            segments.append(f"At {point.second}s: {point.emotion.value} (intensity: {point.intensity})")
        return " → ".join(segments)


# ============== EMOTION CURVE DEFINITIONS ==============

EMOTION_CURVES: Dict[str, EmotionCurve] = {
    "curiosity_loop": EmotionCurve(
        id="curiosity_loop",
        name="Curiosity → Surprise → Loop",
        description="Standard viral hook pattern: question, answer, cliffhanger",
        timeline=[
            EmotionPoint(second=0, emotion=Emotion.CURIOSITY, intensity=1.0),
            EmotionPoint(second=5, emotion=Emotion.TENSION, intensity=0.7),
            EmotionPoint(second=15, emotion=Emotion.SURPRISE, intensity=0.9),
            EmotionPoint(second=25, emotion=Emotion.LOOP, intensity=1.0)
        ],
        genres=["kids", "facts", "educational", "nature"],
        audiences=["kids_india", "genz_us", "general"]
    ),
    
    "shock_twist": EmotionCurve(
        id="shock_twist",
        name="Shock → Explain → Twist → Loop",
        description="Opens with shock, explains, then twists expectation",
        timeline=[
            EmotionPoint(second=0, emotion=Emotion.SHOCK, intensity=1.0),
            EmotionPoint(second=3, emotion=Emotion.CURIOSITY, intensity=0.8),
            EmotionPoint(second=15, emotion=Emotion.TENSION, intensity=0.7),
            EmotionPoint(second=22, emotion=Emotion.SURPRISE, intensity=0.9),
            EmotionPoint(second=28, emotion=Emotion.LOOP, intensity=1.0)
        ],
        genres=["thriller", "horror", "mystery", "noir"],
        audiences=["genz_us", "adults"]
    ),
    
    "wonder_journey": EmotionCurve(
        id="wonder_journey",
        name="Wonder → Joy → Wonder",
        description="Magical, discovery-based journey for kids",
        timeline=[
            EmotionPoint(second=0, emotion=Emotion.WONDER, intensity=0.9),
            EmotionPoint(second=8, emotion=Emotion.JOY, intensity=0.8),
            EmotionPoint(second=16, emotion=Emotion.EXCITEMENT, intensity=0.9),
            EmotionPoint(second=24, emotion=Emotion.WONDER, intensity=1.0),
            EmotionPoint(second=30, emotion=Emotion.LOOP, intensity=0.8)
        ],
        genres=["kids", "bedtime", "fantasy"],
        audiences=["kids_india", "kids", "children"]
    ),
    
    "tension_release": EmotionCurve(
        id="tension_release",
        name="Build → Peak → Release → Hook",
        description="Classic storytelling arc compressed for shorts",
        timeline=[
            EmotionPoint(second=0, emotion=Emotion.CURIOSITY, intensity=0.7),
            EmotionPoint(second=5, emotion=Emotion.TENSION, intensity=0.6),
            EmotionPoint(second=12, emotion=Emotion.TENSION, intensity=0.9),
            EmotionPoint(second=20, emotion=Emotion.RELIEF, intensity=0.8),
            EmotionPoint(second=28, emotion=Emotion.LOOP, intensity=1.0)
        ],
        genres=["thriller", "story", "drama"],
        audiences=["general", "adults"]
    ),
    
    "hype_train": EmotionCurve(
        id="hype_train",
        name="Excitement → Peak → Call to Action",
        description="High energy throughout for motivation content",
        timeline=[
            EmotionPoint(second=0, emotion=Emotion.EXCITEMENT, intensity=0.9),
            EmotionPoint(second=10, emotion=Emotion.EXCITEMENT, intensity=1.0),
            EmotionPoint(second=20, emotion=Emotion.JOY, intensity=0.9),
            EmotionPoint(second=28, emotion=Emotion.LOOP, intensity=1.0)
        ],
        genres=["motivation", "success", "fitness"],
        audiences=["genz_us", "adults"]
    )
}


class EmotionCurveService:
    """
    Service for selecting and applying emotion curves.
    """
    
    @classmethod
    def get_curve(cls, curve_id: str) -> Optional[EmotionCurve]:
        """Get curve by ID."""
        return EMOTION_CURVES.get(curve_id)
    
    @classmethod
    def select_curve(
        cls,
        genre: str = None,
        audience: str = None,
        curve_id: str = None
    ) -> EmotionCurve:
        """
        Select appropriate emotion curve.
        
        Args:
            genre: Content genre
            audience: Target audience
            curve_id: Explicit curve ID override
            
        Returns:
            Selected EmotionCurve
        """
        # Explicit override
        if curve_id and curve_id in EMOTION_CURVES:
            logger.info(f"Using explicit curve: {curve_id}")
            return EMOTION_CURVES[curve_id]
        
        # Find best match
        best_match = None
        best_score = 0
        
        for curve in EMOTION_CURVES.values():
            score = 0
            
            if genre and genre.lower() in [g.lower() for g in curve.genres]:
                score += 2
            
            if audience and audience.lower() in [a.lower() for a in curve.audiences]:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = curve
        
        if best_match:
            logger.info(f"Selected curve '{best_match.id}' (score={best_score})")
            return best_match
        
        # Default
        logger.info("Using default curve: curiosity_loop")
        return EMOTION_CURVES["curiosity_loop"]
    
    @classmethod
    def get_scene_emotions(
        cls,
        curve: EmotionCurve,
        num_scenes: int,
        total_duration: int
    ) -> List[Emotion]:
        """
        Get emotion assignment for each scene.
        
        Args:
            curve: The emotion curve to use
            num_scenes: Number of scenes
            total_duration: Total video duration in seconds
            
        Returns:
            List of emotions, one per scene
        """
        scene_duration = total_duration // num_scenes
        emotions = []
        
        for i in range(num_scenes):
            scene_start = i * scene_duration
            emotion = curve.get_emotion_for_scene(scene_start, scene_start + scene_duration)
            emotions.append(emotion)
        
        return emotions
    
    @classmethod
    def list_curves(cls) -> List[str]:
        """List all available curve IDs."""
        return list(EMOTION_CURVES.keys())
    
    @classmethod
    def get_emotion_prompt_modifier(cls, emotion: Emotion) -> str:
        """Get prompt modifier for a specific emotion."""
        modifiers = {
            Emotion.CURIOSITY: "Create a sense of wonder and intrigue. Make the viewer ask 'what happens next?'",
            Emotion.TENSION: "Build suspense and anticipation. Keep viewers on edge.",
            Emotion.SURPRISE: "Deliver an unexpected revelation or twist.",
            Emotion.JOY: "Create happiness and positive energy.",
            Emotion.FEAR: "Build dread and unease (age-appropriate).",
            Emotion.WONDER: "Inspire awe and amazement.",
            Emotion.SHOCK: "Start with something jarring that grabs attention.",
            Emotion.RELIEF: "Provide a satisfying resolution or payoff.",
            Emotion.EXCITEMENT: "Maximum energy and enthusiasm!",
            Emotion.MYSTERY: "Hint at secrets yet to be revealed.",
            Emotion.LOOP: "End in a way that makes viewers want to watch again - question, cliffhanger, or callback to start."
        }
        return modifiers.get(emotion, "")

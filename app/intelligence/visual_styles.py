"""
Visual Style Engine
Defines brand-level visual styles for consistent, recognizable output.
Each style controls color palette, lighting, camera, and composition.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class LightingType(str, Enum):
    """Lighting mood types."""
    BRIGHT = "bright"
    SOFT = "soft"
    DRAMATIC = "dramatic"
    MOODY = "moody"
    NATURAL = "natural"
    NEON = "neon"


class CameraDistance(str, Enum):
    """Camera framing distance."""
    EXTREME_CLOSE = "extreme close-up"
    CLOSE = "close-up"
    MEDIUM = "medium shot"
    WIDE = "wide shot"
    EXTREME_WIDE = "extreme wide shot"


class CompositionStyle(str, Enum):
    """Visual composition rules."""
    CENTERED = "centered composition"
    RULE_OF_THIRDS = "rule of thirds"
    SYMMETRICAL = "symmetrical"
    DYNAMIC = "dynamic diagonal"
    MINIMAL = "minimal negative space"


@dataclass
class VisualStyle:
    """
    A complete visual style definition for brand-level consistency.
    """
    id: str
    name: str
    description: str
    
    # Color
    color_palette: List[str]
    primary_color: str
    accent_color: str
    
    # Lighting
    lighting: LightingType
    lighting_notes: str = ""
    
    # Camera
    default_camera: CameraDistance
    camera_movement: str = "static"
    
    # Composition
    composition: CompositionStyle
    
    # Style prompt fragments
    style_keywords: List[str] = field(default_factory=list)
    negative_prompts: List[str] = field(default_factory=list)
    
    # Art style references
    art_style: str = "digital illustration"
    reference_artists: List[str] = field(default_factory=list)
    
    def to_prompt_prefix(self) -> str:
        """Generate prompt prefix for image generation."""
        elements = [
            self.art_style,
            f"{self.primary_color} and {self.accent_color} color scheme",
            f"{self.lighting.value} lighting",
            self.composition.value,
            self.default_camera.value,
        ]
        elements.extend(self.style_keywords)
        
        return ", ".join(elements)
    
    def to_negative_prompt(self) -> str:
        """Generate negative prompt to avoid unwanted elements."""
        defaults = ["blurry", "low quality", "watermark", "text overlay"]
        return ", ".join(defaults + self.negative_prompts)


# ============== VISUAL STYLE DEFINITIONS ==============

VISUAL_STYLES: Dict[str, VisualStyle] = {
    "bright_kids_cartoon": VisualStyle(
        id="bright_kids_cartoon",
        name="Bright Kids Cartoon",
        description="Vibrant, colorful, friendly cartoon style for children's content",
        color_palette=["#FFD93D", "#6BCB77", "#4D96FF", "#FF6B6B"],
        primary_color="bright yellow",
        accent_color="sky blue",
        lighting=LightingType.BRIGHT,
        lighting_notes="High-key, no shadows, cheerful",
        default_camera=CameraDistance.MEDIUM,
        camera_movement="gentle zoom",
        composition=CompositionStyle.CENTERED,
        style_keywords=[
            "cartoon style",
            "rounded shapes",
            "expressive characters",
            "vibrant colors",
            "child-friendly",
            "playful"
        ],
        negative_prompts=["scary", "dark", "realistic", "horror", "violence"],
        art_style="Pixar-style 3D cartoon",
        reference_artists=["Disney", "Pixar", "DreamWorks"]
    ),
    
    "cinematic_dark": VisualStyle(
        id="cinematic_dark",
        name="Cinematic Dark",
        description="Moody, dramatic, film-noir inspired visuals for storytelling",
        color_palette=["#1A1A2E", "#16213E", "#0F3460", "#E94560"],
        primary_color="deep blue",
        accent_color="crimson red",
        lighting=LightingType.DRAMATIC,
        lighting_notes="High contrast, rim lighting, shadows",
        default_camera=CameraDistance.CLOSE,
        camera_movement="slow dolly",
        composition=CompositionStyle.RULE_OF_THIRDS,
        style_keywords=[
            "cinematic",
            "film noir",
            "dramatic shadows",
            "atmospheric",
            "moody",
            "high contrast"
        ],
        negative_prompts=["cartoon", "bright", "cheerful", "flat lighting"],
        art_style="cinematic photography",
        reference_artists=["Roger Deakins", "Christopher Nolan", "David Fincher"]
    ),
    
    "minimal_facts": VisualStyle(
        id="minimal_facts",
        name="Minimal Facts",
        description="Clean, modern, infographic-style for educational content",
        color_palette=["#FFFFFF", "#F5F5F5", "#2196F3", "#FF5722"],
        primary_color="white",
        accent_color="blue",
        lighting=LightingType.SOFT,
        lighting_notes="Even, studio lighting, no harsh shadows",
        default_camera=CameraDistance.MEDIUM,
        camera_movement="static",
        composition=CompositionStyle.MINIMAL,
        style_keywords=[
            "minimalist",
            "clean",
            "modern",
            "flat design",
            "infographic",
            "simple shapes",
            "white background"
        ],
        negative_prompts=["cluttered", "busy", "realistic texture", "complex"],
        art_style="flat vector illustration",
        reference_artists=["Kurzgesagt", "TED-Ed"]
    ),
    
    "mythological_epic": VisualStyle(
        id="mythological_epic",
        name="Mythological Epic",
        description="Grand, majestic visuals for mythology and folklore content",
        color_palette=["#FFD700", "#8B4513", "#4A0E0E", "#1A1A1A"],
        primary_color="gold",
        accent_color="deep maroon",
        lighting=LightingType.DRAMATIC,
        lighting_notes="Golden hour, divine rays, epic atmosphere",
        default_camera=CameraDistance.WIDE,
        camera_movement="epic crane",
        composition=CompositionStyle.SYMMETRICAL,
        style_keywords=[
            "epic",
            "majestic",
            "ancient",
            "mythological",
            "divine lighting",
            "golden atmosphere",
            "grand scale"
        ],
        negative_prompts=["modern", "casual", "cartoon", "simple"],
        art_style="digital painting, concept art",
        reference_artists=["Greg Rutkowski", "Alphonse Mucha", "Frank Frazetta"]
    ),
    
    "neon_genz": VisualStyle(
        id="neon_genz",
        name="Neon Gen-Z",
        description="Bold, vibrant, social media native aesthetic",
        color_palette=["#FF006E", "#8338EC", "#3A86FF", "#FFBE0B"],
        primary_color="hot pink",
        accent_color="electric purple",
        lighting=LightingType.NEON,
        lighting_notes="Neon glow, RGB lighting, cyberpunk vibes",
        default_camera=CameraDistance.CLOSE,
        camera_movement="dynamic",
        composition=CompositionStyle.DYNAMIC,
        style_keywords=[
            "neon",
            "vibrant",
            "bold",
            "trendy",
            "y2k aesthetic",
            "gradient",
            "glowing"
        ],
        negative_prompts=["muted", "vintage", "old-fashioned", "dull"],
        art_style="digital art, 3D render",
        reference_artists=["Beeple", "Android Jones"]
    )
}


# ============== PERSONA → VISUAL STYLE MAPPING ==============

PERSONA_STYLE_MAP: Dict[str, str] = {
    "curious_kid": "bright_kids_cartoon",
    "fast_explainer": "minimal_facts",
    "storyteller": "cinematic_dark",
    "hype_master": "neon_genz",
    "gentle_guide": "bright_kids_cartoon"
}

# Genre → Visual Style fallback mapping
GENRE_STYLE_MAP: Dict[str, str] = {
    "kids": "bright_kids_cartoon",
    "bedtime": "bright_kids_cartoon",
    "facts": "minimal_facts",
    "educational": "minimal_facts",
    "thriller": "cinematic_dark",
    "noir": "cinematic_dark",
    "horror": "cinematic_dark",
    "mythology": "mythological_epic",
    "history": "mythological_epic",
    "motivation": "neon_genz",
    "success": "neon_genz"
}


class VisualStyleService:
    """
    Service for selecting and applying visual styles.
    """
    
    @classmethod
    def get_style(cls, style_id: str) -> Optional[VisualStyle]:
        """Get style by ID."""
        return VISUAL_STYLES.get(style_id)
    
    @classmethod
    def get_style_for_persona(cls, persona_id: str) -> VisualStyle:
        """Get visual style bound to a persona."""
        style_id = PERSONA_STYLE_MAP.get(persona_id, "bright_kids_cartoon")
        style = VISUAL_STYLES.get(style_id)
        
        if style:
            logger.info(f"Visual style '{style.name}' for persona '{persona_id}'")
            return style
        
        return VISUAL_STYLES["bright_kids_cartoon"]
    
    @classmethod
    def get_style_for_genre(cls, genre: str) -> VisualStyle:
        """Get visual style for a genre (fallback)."""
        style_id = GENRE_STYLE_MAP.get(genre.lower(), "minimal_facts")
        return VISUAL_STYLES.get(style_id, VISUAL_STYLES["minimal_facts"])
    
    @classmethod
    def select_style(
        cls,
        persona_id: str = None,
        genre: str = None,
        style_id: str = None
    ) -> VisualStyle:
        """
        Select visual style with priority: explicit > persona > genre > default.
        """
        # Explicit override
        if style_id and style_id in VISUAL_STYLES:
            logger.info(f"Using explicit style: {style_id}")
            return VISUAL_STYLES[style_id]
        
        # Persona mapping
        if persona_id:
            return cls.get_style_for_persona(persona_id)
        
        # Genre fallback
        if genre:
            return cls.get_style_for_genre(genre)
        
        # Default
        logger.info("Using default style: minimal_facts")
        return VISUAL_STYLES["minimal_facts"]
    
    @classmethod
    def enhance_prompt(cls, base_prompt: str, style: VisualStyle) -> str:
        """Enhance a visual prompt with style attributes."""
        prefix = style.to_prompt_prefix()
        return f"{prefix}, {base_prompt}"
    
    @classmethod
    def list_styles(cls) -> List[str]:
        """List all available style IDs."""
        return list(VISUAL_STYLES.keys())

"""
Thumbnail Style Presets
Style definitions for thumbnail text and composition.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class ThumbStylePreset(str, Enum):
    BOLD_SHADOW = "bold_shadow"
    BOXED = "boxed"
    OUTLINED = "outlined"
    GRADIENT_BOX = "gradient_box"
    MINIMAL = "minimal"


class TextPosition(str, Enum):
    TOP_CENTER = "top_center"
    BOTTOM_CENTER = "bottom_center"
    LEFT_THIRD = "left_third"
    RIGHT_THIRD = "right_third"
    CENTER = "center"


@dataclass
class ThumbStyle:
    """Thumbnail text style configuration"""
    name: str
    font_family: str = "Impact"
    font_size: int = 72
    font_weight: str = "bold"
    text_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: int = 3
    background_color: str = None
    background_padding: int = 15
    shadow: bool = True
    shadow_color: str = "#000000AA"
    shadow_offset: tuple = (4, 4)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "text_color": self.text_color,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "background_color": self.background_color,
            "shadow": self.shadow
        }


# Built-in style presets
THUMB_STYLES: Dict[ThumbStylePreset, ThumbStyle] = {
    ThumbStylePreset.BOLD_SHADOW: ThumbStyle(
        name="bold_shadow",
        font_family="Impact",
        font_size=80,
        stroke_width=4,
        shadow=True,
        shadow_offset=(5, 5)
    ),
    ThumbStylePreset.BOXED: ThumbStyle(
        name="boxed",
        font_family="Arial Black",
        font_size=72,
        stroke_width=0,
        background_color="#000000DD",
        background_padding=20,
        shadow=False
    ),
    ThumbStylePreset.OUTLINED: ThumbStyle(
        name="outlined",
        font_family="Impact",
        font_size=80,
        stroke_width=6,
        stroke_color="#000000",
        shadow=False
    ),
    ThumbStylePreset.GRADIENT_BOX: ThumbStyle(
        name="gradient_box",
        font_family="Arial Black",
        font_size=72,
        stroke_width=2,
        background_color="gradient:#FF6B6B:#4ECDC4",
        background_padding=25,
        shadow=True
    ),
    ThumbStylePreset.MINIMAL: ThumbStyle(
        name="minimal",
        font_family="Helvetica",
        font_size=48,
        font_weight="medium",
        stroke_width=1,
        shadow=True,
        shadow_offset=(2, 2)
    )
}


def get_style(preset: str) -> ThumbStyle:
    """Get style by preset name"""
    try:
        p = ThumbStylePreset(preset)
        return THUMB_STYLES.get(p, THUMB_STYLES[ThumbStylePreset.BOLD_SHADOW])
    except ValueError:
        return THUMB_STYLES[ThumbStylePreset.BOLD_SHADOW]


def list_styles() -> Dict:
    """List all style presets"""
    return {"styles": [s.to_dict() for s in THUMB_STYLES.values()]}


# Power words for CTR optimization
POWER_WORDS = [
    "SECRET", "HIDDEN", "TRUTH", "REVEALED",
    "SHOCKING", "INSANE", "UNBELIEVABLE", "CRAZY",
    "EASY", "SIMPLE", "QUICK", "FAST",
    "FREE", "NEW", "PROVEN", "BEST",
    "ULTIMATE", "AMAZING", "GENIUS", "HACK"
]


def optimize_text(text: str, max_words: int = 7) -> str:
    """Optimize text for thumbnail use"""
    words = text.split()
    
    # Remove filler words
    fillers = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or", "but"}
    words = [w for w in words if w.lower() not in fillers]
    
    # Truncate to max words
    words = words[:max_words]
    
    # Capitalize key words
    result = []
    for word in words:
        if word.upper() in POWER_WORDS:
            result.append(word.upper())
        else:
            result.append(word)
    
    return " ".join(result)

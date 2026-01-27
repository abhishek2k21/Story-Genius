"""
Text Style Presets
Style definitions and parameters for text overlays.
"""
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class StylePreset(str, Enum):
    CLEAN = "clean"
    BOXED = "boxed"
    OUTLINED = "outlined"
    GRADIENT = "gradient"
    MINIMAL = "minimal"


@dataclass
class TextStyle:
    """Complete text style configuration"""
    name: str
    font_family: str = "Inter"
    font_size: int = 48  # 0 = auto
    font_weight: str = "bold"
    text_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: int = 2
    background_color: Optional[str] = None  # hex with alpha
    background_padding: int = 10
    text_align: str = "center"
    line_height: float = 1.2
    shadow: bool = True
    shadow_color: str = "#00000080"
    shadow_offset: int = 2
    
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
            "background_padding": self.background_padding,
            "text_align": self.text_align,
            "line_height": self.line_height,
            "shadow": self.shadow
        }


# Built-in style presets
STYLE_PRESETS: Dict[StylePreset, TextStyle] = {
    StylePreset.CLEAN: TextStyle(
        name="clean",
        font_weight="bold",
        stroke_width=0,
        background_color=None,
        shadow=True
    ),
    StylePreset.BOXED: TextStyle(
        name="boxed",
        font_weight="bold",
        stroke_width=0,
        background_color="#000000BB",
        background_padding=15,
        shadow=False
    ),
    StylePreset.OUTLINED: TextStyle(
        name="outlined",
        font_weight="bold",
        stroke_width=3,
        stroke_color="#000000",
        background_color=None,
        shadow=False
    ),
    StylePreset.GRADIENT: TextStyle(
        name="gradient",
        font_weight="bold",
        stroke_width=2,
        background_color="linear-gradient(#667eea, #764ba2)",
        background_padding=20,
        shadow=True
    ),
    StylePreset.MINIMAL: TextStyle(
        name="minimal",
        font_weight="medium",
        font_size=36,
        stroke_width=1,
        background_color=None,
        shadow=False
    )
}


def get_style(preset: str) -> TextStyle:
    """Get style by preset name"""
    try:
        p = StylePreset(preset)
        return STYLE_PRESETS.get(p, STYLE_PRESETS[StylePreset.BOXED])
    except ValueError:
        return STYLE_PRESETS[StylePreset.BOXED]


def list_styles() -> Dict:
    """List all style presets"""
    return {
        "presets": [s.to_dict() for s in STYLE_PRESETS.values()]
    }


def create_custom_style(
    base_preset: str = "boxed",
    **overrides
) -> TextStyle:
    """Create custom style from preset with overrides"""
    base = get_style(base_preset)
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(base, key):
            setattr(base, key, value)
    
    base.name = "custom"
    return base


@dataclass
class WordHighlight:
    """Word highlighting configuration"""
    enabled: bool = False
    highlight_color: str = "#FFDD00"
    highlight_style: str = "background"  # background, underline, scale
    sync_with_audio: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "color": self.highlight_color,
            "style": self.highlight_style,
            "sync": self.sync_with_audio
        }

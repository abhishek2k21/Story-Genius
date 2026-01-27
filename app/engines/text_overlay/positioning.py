"""
Safe Zone Positioning
Platform-specific safe zones and text positioning for overlays.
"""
from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class Platform(str, Enum):
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    YOUTUBE_LONG = "youtube_long"
    INSTAGRAM_POST = "instagram_post"


class TextPosition(str, Enum):
    TOP_SAFE = "top_safe"
    CENTER = "center"
    LOWER_THIRD = "lower_third"
    BOTTOM_SAFE = "bottom_safe"


@dataclass
class SafeZone:
    """Platform-specific safe zone margins"""
    platform: Platform
    top_margin: int  # pixels at 1080p
    bottom_margin: int
    left_margin: int
    right_margin: int
    
    # Standard resolution for calculations
    base_width: int = 1080
    base_height: int = 1920
    
    @property
    def safe_width(self) -> int:
        return self.base_width - self.left_margin - self.right_margin
    
    @property
    def safe_height(self) -> int:
        return self.base_height - self.top_margin - self.bottom_margin
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform.value,
            "margins": {
                "top": self.top_margin,
                "bottom": self.bottom_margin,
                "left": self.left_margin,
                "right": self.right_margin
            },
            "base_resolution": f"{self.base_width}x{self.base_height}",
            "safe_area": f"{self.safe_width}x{self.safe_height}"
        }
    
    def scale_to_resolution(self, width: int, height: int) -> Dict:
        """Scale margins to different resolution"""
        width_scale = width / self.base_width
        height_scale = height / self.base_height
        
        return {
            "top": int(self.top_margin * height_scale),
            "bottom": int(self.bottom_margin * height_scale),
            "left": int(self.left_margin * width_scale),
            "right": int(self.right_margin * width_scale)
        }


# Platform-specific safe zones (at 1080x1920 base)
SAFE_ZONES: Dict[Platform, SafeZone] = {
    Platform.YOUTUBE_SHORTS: SafeZone(
        platform=Platform.YOUTUBE_SHORTS,
        top_margin=150,
        bottom_margin=180,
        left_margin=40,
        right_margin=40
    ),
    Platform.INSTAGRAM_REELS: SafeZone(
        platform=Platform.INSTAGRAM_REELS,
        top_margin=120,
        bottom_margin=250,
        left_margin=40,
        right_margin=40
    ),
    Platform.TIKTOK: SafeZone(
        platform=Platform.TIKTOK,
        top_margin=100,
        bottom_margin=150,
        left_margin=40,
        right_margin=40
    ),
    Platform.YOUTUBE_LONG: SafeZone(
        platform=Platform.YOUTUBE_LONG,
        top_margin=60,
        bottom_margin=80,
        left_margin=100,
        right_margin=100,
        base_width=1920,
        base_height=1080
    ),
    Platform.INSTAGRAM_POST: SafeZone(
        platform=Platform.INSTAGRAM_POST,
        top_margin=80,
        bottom_margin=80,
        left_margin=40,
        right_margin=40,
        base_width=1080,
        base_height=1080
    )
}


def get_safe_zone(platform: str) -> SafeZone:
    """Get safe zone for platform"""
    try:
        p = Platform(platform)
        return SAFE_ZONES.get(p, SAFE_ZONES[Platform.YOUTUBE_SHORTS])
    except ValueError:
        return SAFE_ZONES[Platform.YOUTUBE_SHORTS]


def list_safe_zones() -> Dict:
    """List all platform safe zones"""
    return {
        "platforms": [sz.to_dict() for sz in SAFE_ZONES.values()]
    }


@dataclass
class PositionCoordinates:
    """Calculated position coordinates"""
    x: int
    y: int
    width: int
    height: int
    align: str = "center"
    
    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "align": self.align
        }


def calculate_position(
    platform: str,
    position: TextPosition,
    width: int = 1080,
    height: int = 1920,
    text_height: int = 100
) -> PositionCoordinates:
    """Calculate pixel coordinates for text position"""
    safe_zone = get_safe_zone(platform)
    margins = safe_zone.scale_to_resolution(width, height)
    
    # Available area
    available_width = width - margins["left"] - margins["right"]
    available_height = height - margins["top"] - margins["bottom"]
    
    # X position (centered)
    x = margins["left"]
    
    # Y position based on preference
    if position == TextPosition.TOP_SAFE:
        y = margins["top"] + 20
    elif position == TextPosition.CENTER:
        y = margins["top"] + (available_height - text_height) // 2
    elif position == TextPosition.LOWER_THIRD:
        y = height - margins["bottom"] - text_height - (available_height // 4)
    elif position == TextPosition.BOTTOM_SAFE:
        y = height - margins["bottom"] - text_height - 20
    else:
        y = height - margins["bottom"] - text_height - (available_height // 4)
    
    return PositionCoordinates(
        x=x,
        y=y,
        width=available_width,
        height=text_height,
        align="center"
    )


def calculate_max_font_size(
    text: str,
    available_width: int,
    max_size: int = 72,
    min_size: int = 24
) -> int:
    """Calculate maximum font size for readability"""
    # Approximate: 0.6 * font_size per character
    char_count = len(text)
    if char_count == 0:
        return max_size
    
    # Estimate chars that fit at max size
    chars_per_line = available_width / (max_size * 0.6)
    
    if char_count <= chars_per_line:
        return max_size
    
    # Scale down
    scale = chars_per_line / char_count
    calculated = int(max_size * scale)
    
    return max(min_size, min(max_size, calculated))

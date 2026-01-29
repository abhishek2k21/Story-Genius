"""
Text Overlay Utilities
MoviePy text compositing for captions and titles.
"""
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field


class TextStyle(str, Enum):
    """Text styling presets."""
    STANDARD = "standard"
    BOLD = "bold"
    OUTLINE = "outline"
    SHADOW = "shadow"
    HIGHLIGHTED = "highlighted"
    GRADIENT = "gradient"


class TextPosition(str, Enum):
    """Text position on video."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    CUSTOM = "custom"


class TextConfig(BaseModel):
    """Configuration for text overlay."""
    text: str
    position: TextPosition = TextPosition.BOTTOM
    custom_position: Optional[Tuple[int, int]] = None
    font_size: int = Field(48, ge=12, le=120)
    font_family: str = "Arial-Bold"
    font_color: str = "#FFFFFF"
    bg_color: Optional[str] = None
    bg_opacity: float = Field(0.6, ge=0.0, le=1.0)
    stroke_color: Optional[str] = "#000000"
    stroke_width: int = Field(2, ge=0, le=10)
    start_time: float = 0.0
    end_time: Optional[float] = None
    fade_in: float = 0.3
    fade_out: float = 0.3
    margin_x: int = 50
    margin_y: int = 50


def get_position_coords(
    position: TextPosition,
    video_size: Tuple[int, int],
    custom: Optional[Tuple[int, int]] = None,
    margin_y: int = 50,
) -> str:
    """
    Get MoviePy position coordinates.

    Args:
        position: Text position enum
        video_size: (width, height) of video
        custom: Custom (x, y) coordinates
        margin_y: Vertical margin in pixels

    Returns:
        Position string for MoviePy
    """
    width, height = video_size

    if position == TextPosition.CUSTOM and custom:
        return custom

    if position == TextPosition.TOP:
        return ("center", margin_y)
    elif position == TextPosition.CENTER:
        return "center"
    else:  # BOTTOM
        return ("center", height - margin_y)


def add_text_overlay(
    video_path: str,
    output_path: str,
    config: TextConfig,
) -> str:
    """
    Add text overlay to video.

    Args:
        video_path: Input video path
        output_path: Output video path
        config: Text configuration

    Returns:
        Output video path
    """
    from moviepy import CompositeVideoClip, TextClip, VideoFileClip

    video = VideoFileClip(video_path)

    # Create text clip
    text_clip = TextClip(
        text=config.text,
        font_size=config.font_size,
        color=config.font_color,
        font=config.font_family,
        stroke_color=config.stroke_color if config.stroke_width > 0 else None,
        stroke_width=config.stroke_width,
    )

    # Set duration
    duration = config.end_time or video.duration
    text_clip = text_clip.with_duration(duration - config.start_time)
    text_clip = text_clip.with_start(config.start_time)

    # Set position
    pos = get_position_coords(
        config.position,
        video.size,
        config.custom_position,
        config.margin_y,
    )
    text_clip = text_clip.with_position(pos)

    # Add fade effects
    if config.fade_in > 0:
        text_clip = text_clip.crossfadein(config.fade_in)
    if config.fade_out > 0:
        text_clip = text_clip.crossfadeout(config.fade_out)

    # Composite
    final = CompositeVideoClip([video, text_clip])
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    video.close()
    text_clip.close()
    final.close()

    return output_path


def add_caption_overlay(
    video_path: str,
    output_path: str,
    captions: list[dict],
    style: TextStyle = TextStyle.STANDARD,
    font_size: int = 36,
) -> str:
    """
    Add multiple timed captions to video.

    Args:
        video_path: Input video path
        output_path: Output video path
        captions: List of {text, start_time, end_time}
        style: Caption style preset
        font_size: Font size

    Returns:
        Output video path
    """
    from moviepy import CompositeVideoClip, TextClip, VideoFileClip

    video = VideoFileClip(video_path)

    # Style configurations
    style_config = {
        TextStyle.STANDARD: {"color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 1},
        TextStyle.BOLD: {"color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 3},
        TextStyle.OUTLINE: {"color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 4},
        TextStyle.SHADOW: {"color": "#FFFFFF", "stroke_color": "#333333", "stroke_width": 2},
        TextStyle.HIGHLIGHTED: {"color": "#000000", "stroke_color": None, "stroke_width": 0},
    }

    cfg = style_config.get(style, style_config[TextStyle.STANDARD])

    # Create caption clips
    text_clips = [video]

    for caption in captions:
        text_clip = TextClip(
            text=caption["text"],
            font_size=font_size,
            color=cfg["color"],
            font="Arial-Bold",
            stroke_color=cfg["stroke_color"],
            stroke_width=cfg["stroke_width"],
        )

        duration = caption["end_time"] - caption["start_time"]
        text_clip = text_clip.with_duration(duration)
        text_clip = text_clip.with_start(caption["start_time"])
        text_clip = text_clip.with_position(("center", video.h - 80))

        text_clips.append(text_clip)

    # Composite all clips
    final = CompositeVideoClip(text_clips)
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    # Cleanup
    for clip in text_clips:
        clip.close()
    final.close()

    return output_path

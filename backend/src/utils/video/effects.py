"""
Video Effects Utilities
Fade, zoom, pan, and transition effects using MoviePy.
"""
from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel, Field


class EffectType(str, Enum):
    """Types of video effects."""
    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    FADE_BLACK = "fade_black"
    CROSSFADE = "crossfade"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    KEN_BURNS = "ken_burns"
    BLUR_IN = "blur_in"
    SLOW_MOTION = "slow_motion"


class EffectConfig(BaseModel):
    """Configuration for a video effect."""
    effect_type: EffectType
    duration: float = Field(0.5, ge=0.1, le=5.0)
    intensity: float = Field(1.0, ge=0.1, le=2.0)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


def apply_effect(
    video_path: str,
    output_path: str,
    effect: EffectConfig,
) -> str:
    """
    Apply effect to video.

    Args:
        video_path: Input video path
        output_path: Output video path
        effect: Effect configuration

    Returns:
        Output video path
    """
    from moviepy import VideoFileClip

    video = VideoFileClip(video_path)

    if effect.effect_type == EffectType.FADE_IN:
        video = video.crossfadein(effect.duration)

    elif effect.effect_type == EffectType.FADE_OUT:
        video = video.crossfadeout(effect.duration)

    elif effect.effect_type == EffectType.FADE_BLACK:
        video = video.fadein(effect.duration).fadeout(effect.duration)

    elif effect.effect_type == EffectType.ZOOM_IN:
        video = apply_zoom(video, zoom_in=True, duration=effect.duration)

    elif effect.effect_type == EffectType.ZOOM_OUT:
        video = apply_zoom(video, zoom_in=False, duration=effect.duration)

    elif effect.effect_type == EffectType.KEN_BURNS:
        video = apply_ken_burns(video, effect.duration)

    elif effect.effect_type == EffectType.SLOW_MOTION:
        video = video.with_effects([video.fx.MultiplySpeed(0.5)])

    # Write output
    video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    video.close()
    return output_path


def apply_zoom(
    clip,
    zoom_in: bool = True,
    duration: Optional[float] = None,
    zoom_factor: float = 1.2,
):
    """
    Apply zoom effect to clip.

    Args:
        clip: MoviePy video clip
        zoom_in: True for zoom in, False for zoom out
        duration: Effect duration (defaults to full clip)
        zoom_factor: Maximum zoom level

    Returns:
        Modified clip
    """
    duration = duration or clip.duration

    def zoom_effect(get_frame, t):
        import numpy as np
        from PIL import Image

        frame = get_frame(t)
        h, w = frame.shape[:2]

        # Calculate zoom for current time
        progress = min(t / duration, 1.0)
        if zoom_in:
            current_zoom = 1 + (zoom_factor - 1) * progress
        else:
            current_zoom = zoom_factor - (zoom_factor - 1) * progress

        # Calculate crop dimensions
        new_w = int(w / current_zoom)
        new_h = int(h / current_zoom)
        x = (w - new_w) // 2
        y = (h - new_h) // 2

        # Crop and resize
        img = Image.fromarray(frame)
        cropped = img.crop((x, y, x + new_w, y + new_h))
        resized = cropped.resize((w, h), Image.Resampling.LANCZOS)

        return np.array(resized)

    return clip.transform(zoom_effect)


def apply_ken_burns(
    clip,
    duration: Optional[float] = None,
    start_zoom: float = 1.0,
    end_zoom: float = 1.2,
    pan_direction: str = "right",
):
    """
    Apply Ken Burns effect (slow zoom + pan).

    Args:
        clip: MoviePy video clip
        duration: Effect duration
        start_zoom: Starting zoom level
        end_zoom: Ending zoom level
        pan_direction: "left", "right", "up", "down"

    Returns:
        Modified clip
    """
    duration = duration or clip.duration

    def ken_burns_effect(get_frame, t):
        import numpy as np
        from PIL import Image

        frame = get_frame(t)
        h, w = frame.shape[:2]

        # Calculate current zoom
        progress = min(t / duration, 1.0)
        current_zoom = start_zoom + (end_zoom - start_zoom) * progress

        # Calculate crop dimensions
        new_w = int(w / current_zoom)
        new_h = int(h / current_zoom)

        # Calculate pan offset
        max_pan = (w - new_w) // 2
        if pan_direction == "right":
            pan_x = int(max_pan * progress)
        elif pan_direction == "left":
            pan_x = int(max_pan * (1 - progress))
        else:
            pan_x = max_pan // 2

        max_pan_y = (h - new_h) // 2
        if pan_direction == "down":
            pan_y = int(max_pan_y * progress)
        elif pan_direction == "up":
            pan_y = int(max_pan_y * (1 - progress))
        else:
            pan_y = max_pan_y // 2

        # Crop and resize
        img = Image.fromarray(frame)
        cropped = img.crop((pan_x, pan_y, pan_x + new_w, pan_y + new_h))
        resized = cropped.resize((w, h), Image.Resampling.LANCZOS)

        return np.array(resized)

    return clip.transform(ken_burns_effect)


def create_transition(
    clip1,
    clip2,
    transition_type: EffectType,
    duration: float = 0.5,
):
    """
    Create transition between two clips.

    Args:
        clip1: First clip
        clip2: Second clip
        transition_type: Type of transition
        duration: Transition duration

    Returns:
        Composited clip
    """
    from moviepy import CompositeVideoClip

    if transition_type == EffectType.CROSSFADE:
        clip1 = clip1.crossfadeout(duration)
        clip2 = clip2.crossfadein(duration).with_start(clip1.duration - duration)
        return CompositeVideoClip([clip1, clip2])

    elif transition_type == EffectType.FADE_BLACK:
        clip1 = clip1.fadeout(duration)
        clip2 = clip2.fadein(duration).with_start(clip1.duration)
        return CompositeVideoClip([clip1, clip2])

    else:
        # No transition
        clip2 = clip2.with_start(clip1.duration)
        return CompositeVideoClip([clip1, clip2])

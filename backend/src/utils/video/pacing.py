"""
Video Pacing Utilities
Timing, transitions, and scene duration calculations.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TransitionType(str, Enum):
    """Types of transitions between scenes."""
    NONE = "none"
    CROSSFADE = "crossfade"
    FADE_BLACK = "fade_black"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"


class PacingProfile(str, Enum):
    """Pacing profiles for different video styles."""
    SLOW = "slow"           # Documentary style, 8-12s per scene
    MEDIUM = "medium"       # Standard, 5-8s per scene
    FAST = "fast"           # Social media, 3-5s per scene
    DYNAMIC = "dynamic"     # Varies based on content


class SceneTiming(BaseModel):
    """Timing configuration for a scene."""
    scene_order: int
    duration_seconds: float
    transition_in: TransitionType = TransitionType.NONE
    transition_out: TransitionType = TransitionType.CROSSFADE
    transition_duration: float = 0.5
    intro_pause: float = 0.0
    outro_pause: float = 0.0


class PacingConfig(BaseModel):
    """Overall pacing configuration."""
    profile: PacingProfile = PacingProfile.MEDIUM
    target_duration: Optional[float] = None
    min_scene_duration: float = 3.0
    max_scene_duration: float = 12.0
    default_transition: TransitionType = TransitionType.CROSSFADE
    transition_duration: float = 0.5


def calculate_pacing(
    narration_lengths: list[int],
    config: Optional[PacingConfig] = None,
) -> list[SceneTiming]:
    """
    Calculate scene timings based on narration word counts.

    Args:
        narration_lengths: Word counts for each scene
        config: Pacing configuration

    Returns:
        List of scene timing configurations
    """
    config = config or PacingConfig()

    # Words per minute based on profile
    wpm_map = {
        PacingProfile.SLOW: 100,
        PacingProfile.MEDIUM: 140,
        PacingProfile.FAST: 180,
        PacingProfile.DYNAMIC: 140,
    }
    wpm = wpm_map[config.profile]

    timings = []
    total_duration = 0.0

    for i, word_count in enumerate(narration_lengths):
        # Calculate duration from word count
        duration = (word_count / wpm) * 60

        # Apply min/max constraints
        duration = max(config.min_scene_duration, min(config.max_scene_duration, duration))

        # Add buffer for visual pacing
        duration *= 1.15  # 15% buffer for pauses

        timing = SceneTiming(
            scene_order=i,
            duration_seconds=round(duration, 1),
            transition_in=TransitionType.NONE if i == 0 else config.default_transition,
            transition_out=TransitionType.NONE if i == len(narration_lengths) - 1 else config.default_transition,
            transition_duration=config.transition_duration,
        )
        timings.append(timing)
        total_duration += duration

    # Scale if target duration specified
    if config.target_duration and total_duration > 0:
        scale = config.target_duration / total_duration
        for timing in timings:
            timing.duration_seconds = round(timing.duration_seconds * scale, 1)
            timing.duration_seconds = max(
                config.min_scene_duration,
                min(config.max_scene_duration, timing.duration_seconds),
            )

    return timings


def get_scene_timestamps(timings: list[SceneTiming]) -> list[tuple[float, float]]:
    """
    Get start/end timestamps for each scene.

    Args:
        timings: Scene timing configurations

    Returns:
        List of (start_time, end_time) tuples
    """
    timestamps = []
    current_time = 0.0

    for timing in timings:
        start = current_time
        end = start + timing.duration_seconds
        timestamps.append((round(start, 2), round(end, 2)))
        current_time = end

    return timestamps


def calculate_total_duration(timings: list[SceneTiming]) -> float:
    """Calculate total video duration from timings."""
    return sum(t.duration_seconds for t in timings)

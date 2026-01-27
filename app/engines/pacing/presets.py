"""
Pacing Presets
Pre-configured pacing profiles for different content styles.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class PacingIntensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DYNAMIC = "dynamic"


class BumpPattern(str, Enum):
    STEADY = "steady"      # Even distribution
    WAVE = "wave"          # Alternating high/low
    BUILDING = "building"  # Increasing intensity
    CLIMAX = "climax"      # Build to peak then release


class BumpType(str, Enum):
    SCENE_CHANGE = "scene_change"
    ZOOM_SHIFT = "zoom_shift"
    TEXT_EMPHASIS = "text_emphasis"
    AUDIO_STING = "audio_sting"
    MOTION_CHANGE = "motion_change"
    REVEAL = "reveal"
    QUESTION = "question"


@dataclass
class PacingPreset:
    """Pre-configured pacing profile"""
    name: str
    description: str
    min_interval: float
    max_interval: float
    intensity: PacingIntensity
    pattern: BumpPattern
    allowed_bump_types: List[BumpType]
    hook_duration: float = 2.5
    cta_duration: float = 3.5
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "interval": {"min": self.min_interval, "max": self.max_interval},
            "intensity": self.intensity.value,
            "pattern": self.pattern.value,
            "bump_types": [b.value for b in self.allowed_bump_types],
            "hook_duration": self.hook_duration,
            "cta_duration": self.cta_duration
        }


# Built-in presets
PACING_PRESETS: Dict[str, PacingPreset] = {
    "relaxed": PacingPreset(
        name="relaxed",
        description="Slow pace for educational content",
        min_interval=7.0,
        max_interval=10.0,
        intensity=PacingIntensity.LOW,
        pattern=BumpPattern.STEADY,
        allowed_bump_types=[BumpType.SCENE_CHANGE, BumpType.ZOOM_SHIFT]
    ),
    "standard": PacingPreset(
        name="standard",
        description="Balanced pace for most content",
        min_interval=5.0,
        max_interval=7.0,
        intensity=PacingIntensity.MEDIUM,
        pattern=BumpPattern.WAVE,
        allowed_bump_types=[BumpType.SCENE_CHANGE, BumpType.ZOOM_SHIFT, BumpType.TEXT_EMPHASIS]
    ),
    "energetic": PacingPreset(
        name="energetic",
        description="Fast pace for entertainment",
        min_interval=4.0,
        max_interval=5.0,
        intensity=PacingIntensity.HIGH,
        pattern=BumpPattern.BUILDING,
        allowed_bump_types=[BumpType.SCENE_CHANGE, BumpType.ZOOM_SHIFT, BumpType.MOTION_CHANGE, BumpType.REVEAL]
    ),
    "dynamic": PacingPreset(
        name="dynamic",
        description="Variable pace building to climax",
        min_interval=4.0,
        max_interval=8.0,
        intensity=PacingIntensity.DYNAMIC,
        pattern=BumpPattern.CLIMAX,
        allowed_bump_types=list(BumpType)
    ),
    "minimal": PacingPreset(
        name="minimal",
        description="Minimal changes for calm content",
        min_interval=8.0,
        max_interval=12.0,
        intensity=PacingIntensity.LOW,
        pattern=BumpPattern.STEADY,
        allowed_bump_types=[BumpType.SCENE_CHANGE]
    )
}


def get_preset(name: str) -> PacingPreset:
    """Get preset by name"""
    return PACING_PRESETS.get(name, PACING_PRESETS["standard"])


def list_presets() -> Dict:
    """List all presets"""
    return {"presets": [p.to_dict() for p in PACING_PRESETS.values()]}


def get_optimal_interval(duration: int) -> Dict:
    """Get optimal bump interval for video duration"""
    if duration <= 15:
        return {"min": 4, "max": 5, "bumps": 2}
    elif duration <= 30:
        return {"min": 5, "max": 6, "bumps": 4}
    elif duration <= 45:
        return {"min": 5, "max": 7, "bumps": 6}
    elif duration <= 60:
        return {"min": 6, "max": 8, "bumps": 8}
    else:
        return {"min": 6, "max": 10, "bumps": int(duration / 7)}

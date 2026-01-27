"""
Text Animation System
Animation definitions for text overlay transitions.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class AnimationType(str, Enum):
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    POP_IN = "pop_in"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    TYPEWRITER = "typewriter"
    NONE = "none"


@dataclass
class Animation:
    """Animation configuration"""
    type: AnimationType
    duration: float  # seconds
    easing: str = "ease-out"
    delay: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "duration": self.duration,
            "easing": self.easing,
            "delay": self.delay
        }


# Animation presets
ANIMATIONS: Dict[AnimationType, Animation] = {
    AnimationType.FADE_IN: Animation(
        type=AnimationType.FADE_IN,
        duration=0.15,
        easing="ease-out"
    ),
    AnimationType.FADE_OUT: Animation(
        type=AnimationType.FADE_OUT,
        duration=0.15,
        easing="ease-in"
    ),
    AnimationType.POP_IN: Animation(
        type=AnimationType.POP_IN,
        duration=0.2,
        easing="ease-out-back"
    ),
    AnimationType.SLIDE_UP: Animation(
        type=AnimationType.SLIDE_UP,
        duration=0.2,
        easing="ease-out"
    ),
    AnimationType.SLIDE_DOWN: Animation(
        type=AnimationType.SLIDE_DOWN,
        duration=0.2,
        easing="ease-out"
    ),
    AnimationType.TYPEWRITER: Animation(
        type=AnimationType.TYPEWRITER,
        duration=0.5,  # Variable based on text length
        easing="linear"
    ),
    AnimationType.NONE: Animation(
        type=AnimationType.NONE,
        duration=0,
        easing="linear"
    )
}


def get_animation(anim_type: str) -> Animation:
    """Get animation by type"""
    try:
        t = AnimationType(anim_type)
        return ANIMATIONS.get(t, ANIMATIONS[AnimationType.FADE_IN])
    except ValueError:
        return ANIMATIONS[AnimationType.FADE_IN]


def list_animations() -> Dict:
    """List all animation types"""
    return {
        "animations": [a.to_dict() for a in ANIMATIONS.values()]
    }


@dataclass
class AnimationKeyframe:
    """Single keyframe in animation sequence"""
    time: float  # 0-1 progress
    opacity: float = 1.0
    scale: float = 1.0
    translate_x: float = 0
    translate_y: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "time": self.time,
            "opacity": self.opacity,
            "scale": self.scale,
            "translate_x": self.translate_x,
            "translate_y": self.translate_y
        }


def generate_keyframes(animation: Animation) -> List[AnimationKeyframe]:
    """Generate keyframes for animation type"""
    atype = animation.type
    
    if atype == AnimationType.FADE_IN:
        return [
            AnimationKeyframe(time=0, opacity=0),
            AnimationKeyframe(time=1, opacity=1)
        ]
    
    elif atype == AnimationType.FADE_OUT:
        return [
            AnimationKeyframe(time=0, opacity=1),
            AnimationKeyframe(time=1, opacity=0)
        ]
    
    elif atype == AnimationType.POP_IN:
        return [
            AnimationKeyframe(time=0, opacity=0, scale=0.8),
            AnimationKeyframe(time=0.6, opacity=1, scale=1.1),
            AnimationKeyframe(time=1, opacity=1, scale=1.0)
        ]
    
    elif atype == AnimationType.SLIDE_UP:
        return [
            AnimationKeyframe(time=0, opacity=0, translate_y=30),
            AnimationKeyframe(time=1, opacity=1, translate_y=0)
        ]
    
    elif atype == AnimationType.SLIDE_DOWN:
        return [
            AnimationKeyframe(time=0, opacity=0, translate_y=-30),
            AnimationKeyframe(time=1, opacity=1, translate_y=0)
        ]
    
    else:  # NONE or TYPEWRITER
        return [
            AnimationKeyframe(time=0, opacity=1),
            AnimationKeyframe(time=1, opacity=1)
        ]

"""
Visual Change Scheduler
Generates specific visual instructions for retention bumps.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

from app.engines.pacing.presets import BumpType
from app.engines.pacing.bumps import RetentionBump


class VisualChangeType(str, Enum):
    SCENE_CUT = "scene_cut"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    OVERLAY_ADD = "overlay_add"
    OVERLAY_REMOVE = "overlay_remove"
    SPEED_RAMP = "speed_ramp"
    COLOR_SHIFT = "color_shift"
    SHAKE = "shake"


@dataclass
class VisualInstruction:
    """A visual change instruction for video rendering"""
    instruction_id: int
    timestamp: float
    duration: float
    change_type: VisualChangeType
    parameters: Dict
    bump_reference: int
    layer: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.instruction_id,
            "timestamp": round(self.timestamp, 3),
            "duration": round(self.duration, 3),
            "type": self.change_type.value,
            "parameters": self.parameters,
            "bump_ref": self.bump_reference,
            "layer": self.layer
        }


# Mapping bump types to visual changes
BUMP_TO_VISUAL: Dict[BumpType, List[VisualChangeType]] = {
    BumpType.SCENE_CHANGE: [VisualChangeType.SCENE_CUT],
    BumpType.ZOOM_SHIFT: [VisualChangeType.ZOOM_IN, VisualChangeType.ZOOM_OUT],
    BumpType.TEXT_EMPHASIS: [VisualChangeType.OVERLAY_ADD],
    BumpType.AUDIO_STING: [VisualChangeType.SHAKE],
    BumpType.MOTION_CHANGE: [VisualChangeType.SPEED_RAMP],
    BumpType.REVEAL: [VisualChangeType.ZOOM_IN, VisualChangeType.OVERLAY_ADD],
    BumpType.QUESTION: [VisualChangeType.OVERLAY_ADD]
}


def generate_visual_instructions(bumps: List[RetentionBump]) -> List[VisualInstruction]:
    """Generate visual instructions for all bumps"""
    instructions = []
    last_change = None
    
    for bump in bumps:
        change_type = _select_visual_change(bump.bump_type, last_change)
        params = _calculate_parameters(change_type, bump.intensity)
        duration = _calculate_duration(change_type, bump.intensity)
        
        instruction = VisualInstruction(
            instruction_id=len(instructions),
            timestamp=bump.timestamp,
            duration=duration,
            change_type=change_type,
            parameters=params,
            bump_reference=bump.bump_id,
            layer=_get_layer(change_type)
        )
        
        instructions.append(instruction)
        last_change = change_type
    
    return instructions


def _select_visual_change(
    bump_type: BumpType,
    last_change: VisualChangeType = None
) -> VisualChangeType:
    """Select visual change type for bump"""
    options = BUMP_TO_VISUAL.get(bump_type, [VisualChangeType.SCENE_CUT])
    
    # Avoid repeating last change
    if last_change in options and len(options) > 1:
        options = [o for o in options if o != last_change]
    
    return options[0] if options else VisualChangeType.SCENE_CUT


def _calculate_parameters(
    change_type: VisualChangeType,
    intensity: float
) -> Dict:
    """Calculate change-specific parameters"""
    if change_type == VisualChangeType.ZOOM_IN:
        return {
            "scale": 1.0 + (0.2 * intensity),
            "easing": "ease-out"
        }
    
    elif change_type == VisualChangeType.ZOOM_OUT:
        return {
            "scale": 1.0 - (0.1 * intensity),
            "easing": "ease-in-out"
        }
    
    elif change_type in [VisualChangeType.PAN_LEFT, VisualChangeType.PAN_RIGHT]:
        direction = -1 if change_type == VisualChangeType.PAN_LEFT else 1
        return {
            "distance": int(50 * intensity) * direction,
            "easing": "linear"
        }
    
    elif change_type == VisualChangeType.SPEED_RAMP:
        return {
            "speed": 0.5 + intensity,
            "ramp_duration": 0.3
        }
    
    elif change_type == VisualChangeType.SHAKE:
        return {
            "amplitude": 5 * intensity,
            "frequency": 15
        }
    
    elif change_type == VisualChangeType.COLOR_SHIFT:
        return {
            "saturation": 1.0 + (0.3 * intensity),
            "contrast": 1.0 + (0.1 * intensity)
        }
    
    elif change_type == VisualChangeType.OVERLAY_ADD:
        return {
            "opacity": 0.8 + (0.2 * intensity),
            "position": "center"
        }
    
    return {}


def _calculate_duration(change_type: VisualChangeType, intensity: float) -> float:
    """Calculate change duration based on type"""
    base_durations = {
        VisualChangeType.SCENE_CUT: 0,
        VisualChangeType.ZOOM_IN: 0.5,
        VisualChangeType.ZOOM_OUT: 0.5,
        VisualChangeType.PAN_LEFT: 0.8,
        VisualChangeType.PAN_RIGHT: 0.8,
        VisualChangeType.SPEED_RAMP: 0.5,
        VisualChangeType.SHAKE: 0.3,
        VisualChangeType.OVERLAY_ADD: 0.2,
        VisualChangeType.OVERLAY_REMOVE: 0.2,
        VisualChangeType.COLOR_SHIFT: 0.3
    }
    
    base = base_durations.get(change_type, 0.3)
    return base * (0.8 + 0.4 * intensity)


def _get_layer(change_type: VisualChangeType) -> int:
    """Get compositing layer for change type"""
    overlay_types = [VisualChangeType.OVERLAY_ADD, VisualChangeType.OVERLAY_REMOVE]
    return 10 if change_type in overlay_types else 0

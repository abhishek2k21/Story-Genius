"""
Retention Bump Placement
Algorithm for placing attention-recapturing bumps at optimal intervals.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

from app.engines.pacing.presets import BumpType, BumpPattern, PacingPreset, get_optimal_interval
from app.engines.pacing.segments import Segment, SegmentTimeline


@dataclass
class RetentionBump:
    """A retention bump at a specific time"""
    bump_id: int
    timestamp: float
    bump_type: BumpType
    segment_id: str
    intensity: float  # 0-1
    instruction: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.bump_id,
            "timestamp": round(self.timestamp, 3),
            "type": self.bump_type.value,
            "segment": self.segment_id,
            "intensity": round(self.intensity, 2),
            "instruction": self.instruction
        }


# Bump placement rules
MIN_FROM_START = 2.0  # Don't place in first 2 seconds
MIN_FROM_END = 2.0    # Don't place in last 2 seconds
MIN_SPACING = 4.0     # Minimum 4 seconds between bumps
MAX_SPACING = 8.0     # Maximum 8 seconds without bump


def calculate_bump_positions(
    total_duration: float,
    preset: PacingPreset,
    timeline: SegmentTimeline = None
) -> List[float]:
    """Calculate optimal bump positions based on preset"""
    positions = []
    
    # Calculate ideal interval
    interval = (preset.min_interval + preset.max_interval) / 2
    
    # Start after MIN_FROM_START
    current = MIN_FROM_START + interval
    
    # End before last MIN_FROM_END
    end_time = total_duration - MIN_FROM_END
    
    while current < end_time:
        # Check segment boundaries if timeline provided
        if timeline:
            segment = timeline.get_segment_at(current)
            if segment:
                # Avoid placing at segment start/end
                seg_mid = (segment.start_time + segment.end_time) / 2
                if abs(current - segment.start_time) < 1.0:
                    current += 1.0
                elif abs(current - segment.end_time) < 1.0:
                    current -= 0.5
        
        positions.append(current)
        
        # Add jitter based on pattern
        if preset.pattern == BumpPattern.DYNAMIC:
            jitter = random.uniform(-1, 1)
            interval = random.uniform(preset.min_interval, preset.max_interval)
        else:
            jitter = 0
            
        current += interval + jitter
    
    return positions


def assign_bump_types(
    positions: List[float],
    preset: PacingPreset,
    timeline: SegmentTimeline = None
) -> List[RetentionBump]:
    """Assign bump types to positions based on pattern"""
    bumps = []
    allowed_types = preset.allowed_bump_types
    last_type = None
    
    for i, pos in enumerate(positions):
        # Get segment at this position
        segment_id = "unknown"
        if timeline:
            seg = timeline.get_segment_at(pos)
            if seg:
                segment_id = seg.segment_id
        
        # Select bump type avoiding repetition
        bump_type = _select_bump_type(i, len(positions), allowed_types, last_type, preset.pattern)
        last_type = bump_type
        
        # Calculate intensity based on pattern
        intensity = _calculate_intensity(i, len(positions), preset.pattern)
        
        # Generate instruction
        instruction = _generate_instruction(bump_type)
        
        bumps.append(RetentionBump(
            bump_id=i,
            timestamp=pos,
            bump_type=bump_type,
            segment_id=segment_id,
            intensity=intensity,
            instruction=instruction
        ))
    
    return bumps


def _select_bump_type(
    index: int,
    total: int,
    allowed: List[BumpType],
    last_type: BumpType,
    pattern: BumpPattern
) -> BumpType:
    """Select appropriate bump type"""
    if not allowed:
        return BumpType.SCENE_CHANGE
    
    # Filter out last type to avoid repetition
    choices = [t for t in allowed if t != last_type]
    if not choices:
        choices = allowed
    
    # Pattern-specific selection
    if pattern == BumpPattern.BUILDING:
        # Start simple, end with reveals
        progress = index / max(1, total - 1)
        if progress > 0.7 and BumpType.REVEAL in choices:
            return BumpType.REVEAL
        elif progress < 0.3:
            return choices[0]
    
    elif pattern == BumpPattern.CLIMAX:
        # Build to peak at 80%
        progress = index / max(1, total - 1)
        if 0.6 < progress < 0.9 and BumpType.REVEAL in choices:
            return BumpType.REVEAL
    
    elif pattern == BumpPattern.WAVE:
        # Alternate between types
        type_index = index % len(choices)
        return choices[type_index]
    
    # Default: random from allowed
    return random.choice(choices)


def _calculate_intensity(index: int, total: int, pattern: BumpPattern) -> float:
    """Calculate bump intensity based on pattern and position"""
    progress = index / max(1, total - 1)
    
    if pattern == BumpPattern.STEADY:
        return 0.6
    elif pattern == BumpPattern.BUILDING:
        return 0.4 + (progress * 0.5)
    elif pattern == BumpPattern.WAVE:
        return 0.5 + (0.3 * (1 if index % 2 == 0 else -1) * (0.5 - abs(0.5 - progress)))
    elif pattern == BumpPattern.CLIMAX:
        # Peak at 80%
        peak_dist = abs(progress - 0.8)
        return max(0.3, 1.0 - peak_dist)
    
    return 0.6


def _generate_instruction(bump_type: BumpType) -> str:
    """Generate human-readable instruction"""
    instructions = {
        BumpType.SCENE_CHANGE: "Cut to next scene",
        BumpType.ZOOM_SHIFT: "Apply zoom transition",
        BumpType.TEXT_EMPHASIS: "Highlight current text",
        BumpType.AUDIO_STING: "Add sound effect",
        BumpType.MOTION_CHANGE: "Change motion direction/speed",
        BumpType.REVEAL: "Reveal hidden element",
        BumpType.QUESTION: "Show question overlay"
    }
    return instructions.get(bump_type, "Apply visual change")


def place_retention_bumps(
    total_duration: float,
    preset: PacingPreset,
    timeline: SegmentTimeline = None
) -> List[RetentionBump]:
    """Main function to place all retention bumps"""
    positions = calculate_bump_positions(total_duration, preset, timeline)
    bumps = assign_bump_types(positions, preset, timeline)
    return bumps

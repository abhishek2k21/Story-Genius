"""
Segment Timing Calculator
Allocates duration across content sections with constraint validation.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SegmentType(str, Enum):
    HOOK = "hook"
    SETUP = "setup"
    MAIN_POINT = "main_point"
    PAYOFF = "payoff"
    CTA = "cta"


# Duration constraints (seconds)
SEGMENT_CONSTRAINTS = {
    SegmentType.HOOK: {"min": 1.5, "max": 3.0, "default": 2.5},
    SegmentType.SETUP: {"min": 3.0, "max": 8.0, "default": 5.0},
    SegmentType.MAIN_POINT: {"min": 4.0, "max": 10.0, "default": 6.0},
    SegmentType.PAYOFF: {"min": 3.0, "max": 6.0, "default": 4.0},
    SegmentType.CTA: {"min": 2.0, "max": 4.0, "default": 3.0}
}


@dataclass
class Segment:
    """A timed content segment"""
    segment_id: str
    segment_type: SegmentType
    start_time: float
    end_time: float
    duration: float
    content_reference: Optional[str] = None
    flexibility: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict:
        return {
            "id": self.segment_id,
            "type": self.segment_type.value,
            "start": round(self.start_time, 3),
            "end": round(self.end_time, 3),
            "duration": round(self.duration, 3),
            "content": self.content_reference,
            "flexibility": self.flexibility
        }


@dataclass
class SegmentTimeline:
    """Complete segment timeline"""
    segments: List[Segment]
    total_duration: float
    
    @property
    def segment_count(self) -> int:
        return len(self.segments)
    
    def get_segment_at(self, time: float) -> Optional[Segment]:
        """Get segment at specific time"""
        for seg in self.segments:
            if seg.start_time <= time < seg.end_time:
                return seg
        return None
    
    def to_dict(self) -> Dict:
        return {
            "total_duration": round(self.total_duration, 3),
            "segment_count": self.segment_count,
            "segments": [s.to_dict() for s in self.segments]
        }


def calculate_segment_timing(
    target_duration: float,
    main_point_count: int = 3,
    hook_duration: float = None,
    cta_duration: float = None
) -> SegmentTimeline:
    """
    Calculate optimal segment timing for target duration.
    
    Args:
        target_duration: Total video length in seconds
        main_point_count: Number of main content points
        hook_duration: Override hook duration
        cta_duration: Override CTA duration
    """
    segments = []
    current_time = 0
    
    # Hook segment
    hook_dur = hook_duration or SEGMENT_CONSTRAINTS[SegmentType.HOOK]["default"]
    hook_dur = _clamp(hook_dur, SegmentType.HOOK)
    segments.append(Segment(
        segment_id="seg_hook",
        segment_type=SegmentType.HOOK,
        start_time=current_time,
        end_time=current_time + hook_dur,
        duration=hook_dur,
        flexibility="low"
    ))
    current_time += hook_dur
    
    # CTA segment (reserve at end)
    cta_dur = cta_duration or SEGMENT_CONSTRAINTS[SegmentType.CTA]["default"]
    cta_dur = _clamp(cta_dur, SegmentType.CTA)
    
    # Calculate body duration
    body_duration = target_duration - hook_dur - cta_dur
    
    if body_duration < 5:
        # Very short video - minimal structure
        segments.append(Segment(
            segment_id="seg_main_0",
            segment_type=SegmentType.MAIN_POINT,
            start_time=current_time,
            end_time=current_time + body_duration,
            duration=body_duration,
            flexibility="high"
        ))
        current_time += body_duration
    else:
        # Setup segment (20% of body)
        setup_dur = min(body_duration * 0.2, SEGMENT_CONSTRAINTS[SegmentType.SETUP]["max"])
        setup_dur = max(setup_dur, SEGMENT_CONSTRAINTS[SegmentType.SETUP]["min"])
        
        segments.append(Segment(
            segment_id="seg_setup",
            segment_type=SegmentType.SETUP,
            start_time=current_time,
            end_time=current_time + setup_dur,
            duration=setup_dur,
            flexibility="medium"
        ))
        current_time += setup_dur
        
        # Payoff segment (15% of body)
        payoff_dur = min(body_duration * 0.15, SEGMENT_CONSTRAINTS[SegmentType.PAYOFF]["max"])
        payoff_dur = max(payoff_dur, SEGMENT_CONSTRAINTS[SegmentType.PAYOFF]["min"])
        
        # Main points get remaining
        main_total = body_duration - setup_dur - payoff_dur
        main_each = main_total / max(1, main_point_count)
        main_each = _clamp(main_each, SegmentType.MAIN_POINT)
        
        for i in range(main_point_count):
            segments.append(Segment(
                segment_id=f"seg_main_{i}",
                segment_type=SegmentType.MAIN_POINT,
                start_time=current_time,
                end_time=current_time + main_each,
                duration=main_each,
                flexibility="high"
            ))
            current_time += main_each
        
        # Payoff
        segments.append(Segment(
            segment_id="seg_payoff",
            segment_type=SegmentType.PAYOFF,
            start_time=current_time,
            end_time=current_time + payoff_dur,
            duration=payoff_dur,
            flexibility="medium"
        ))
        current_time += payoff_dur
    
    # CTA at end
    segments.append(Segment(
        segment_id="seg_cta",
        segment_type=SegmentType.CTA,
        start_time=current_time,
        end_time=current_time + cta_dur,
        duration=cta_dur,
        flexibility="low"
    ))
    
    # Adjust to exactly match target
    actual_total = sum(s.duration for s in segments)
    if abs(actual_total - target_duration) > 0.1:
        segments = _balance_duration(segments, target_duration)
    
    return SegmentTimeline(
        segments=segments,
        total_duration=target_duration
    )


def _clamp(value: float, seg_type: SegmentType) -> float:
    """Clamp value to segment constraints"""
    constraints = SEGMENT_CONSTRAINTS[seg_type]
    return max(constraints["min"], min(constraints["max"], value))


def _balance_duration(segments: List[Segment], target: float) -> List[Segment]:
    """Adjust segment durations to match target"""
    current_total = sum(s.duration for s in segments)
    diff = target - current_total
    
    # Find flexible segments
    flexible = [s for s in segments if s.flexibility == "high"]
    if not flexible:
        flexible = [s for s in segments if s.flexibility == "medium"]
    
    if flexible and abs(diff) > 0.1:
        adjustment = diff / len(flexible)
        for seg in flexible:
            seg.duration += adjustment
            seg.end_time = seg.start_time + seg.duration
    
    # Recalculate start times
    current = 0
    for seg in segments:
        seg.start_time = current
        seg.end_time = current + seg.duration
        current = seg.end_time
    
    return segments

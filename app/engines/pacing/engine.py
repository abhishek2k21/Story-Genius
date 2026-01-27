"""
Pacing Engine
Main engine for retention optimization through pacing.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import uuid

from app.engines.base import BaseEngine, EngineInput, EngineOutput, EngineStatus, EngineDefinition
from app.engines.registry import EngineRegistry
from app.engines.pacing.presets import get_preset, PacingPreset, list_presets
from app.engines.pacing.segments import calculate_segment_timing, SegmentTimeline
from app.engines.pacing.bumps import place_retention_bumps, RetentionBump
from app.engines.pacing.visual import generate_visual_instructions, VisualInstruction
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PacingResult:
    """Complete pacing output"""
    pacing_id: str
    segment_timeline: SegmentTimeline
    bumps: List[RetentionBump]
    visual_instructions: List[VisualInstruction]
    quality_score: float
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "pacing_id": self.pacing_id,
            "timeline": self.segment_timeline.to_dict(),
            "bump_count": len(self.bumps),
            "bumps": [b.to_dict() for b in self.bumps],
            "instruction_count": len(self.visual_instructions),
            "instructions": [v.to_dict() for v in self.visual_instructions],
            "quality_score": round(self.quality_score, 2),
            "warnings": self.warnings
        }


class PacingEngine(BaseEngine):
    """Engine for video pacing and retention optimization"""
    
    def __init__(self):
        super().__init__(
            engine_id="pacing_engine_v1",
            engine_type="pacing",
            version="1.0.0"
        )
    
    def validate_input(self, input_data: EngineInput) -> Dict:
        errors = []
        params = input_data.parameters
        
        if not params.get("target_duration"):
            errors.append("Missing required: target_duration")
        
        duration = params.get("target_duration", 0)
        if duration < 5 or duration > 300:
            errors.append("target_duration must be 5-300 seconds")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Generate pacing for content"""
        self.status = EngineStatus.RUNNING
        
        params = input_data.parameters
        target_duration = params.get("target_duration", 30)
        preset_name = params.get("preset", "standard")
        main_points = params.get("main_points", 3)
        
        # Get preset
        preset = get_preset(preset_name)
        
        # Calculate segment timing
        timeline = calculate_segment_timing(
            target_duration=target_duration,
            main_point_count=main_points,
            hook_duration=preset.hook_duration,
            cta_duration=preset.cta_duration
        )
        
        # Place retention bumps
        bumps = place_retention_bumps(target_duration, preset, timeline)
        
        # Generate visual instructions
        visual_instructions = generate_visual_instructions(bumps)
        
        # Calculate quality score
        quality_score, warnings = self._score_pacing(timeline, bumps, preset)
        
        result = PacingResult(
            pacing_id=str(uuid.uuid4()),
            segment_timeline=timeline,
            bumps=bumps,
            visual_instructions=visual_instructions,
            quality_score=quality_score,
            warnings=warnings
        )
        
        self.status = EngineStatus.COMPLETED
        
        return EngineOutput(
            job_id=input_data.job_id,
            engine_id=self.engine_id,
            status=EngineStatus.COMPLETED,
            primary_artifact=result.pacing_id,
            metadata=result.to_dict(),
            quality_scores={
                "pacing_quality": quality_score,
                "bump_coverage": self._calc_bump_coverage(bumps, target_duration)
            }
        )
    
    def validate_output(self, output: EngineOutput) -> Dict:
        errors = []
        if not output.metadata.get("bumps"):
            errors.append("No retention bumps generated")
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _score_pacing(
        self,
        timeline: SegmentTimeline,
        bumps: List[RetentionBump],
        preset: PacingPreset
    ) -> tuple:
        """Score pacing quality"""
        warnings = []
        scores = []
        
        # Bump coverage (30%)
        coverage = self._calc_bump_coverage(bumps, timeline.total_duration)
        scores.append(coverage * 0.30)
        if coverage < 0.7:
            warnings.append("Some sections have long gaps without retention bumps")
        
        # Variety (25%)
        bump_types = set(b.bump_type for b in bumps)
        variety = min(1.0, len(bump_types) / 3)
        scores.append(variety * 0.25)
        if len(bump_types) == 1:
            warnings.append("Consider using more bump type variety")
        
        # Spacing consistency (20%)
        if len(bumps) >= 2:
            intervals = [bumps[i+1].timestamp - bumps[i].timestamp for i in range(len(bumps)-1)]
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            spacing_score = max(0, 1 - (variance / 10))
        else:
            spacing_score = 0.5
        scores.append(spacing_score * 0.20)
        
        # Segment balance (15%)
        durations = [s.duration for s in timeline.segments]
        avg_dur = sum(durations) / len(durations)
        dur_variance = sum((d - avg_dur) ** 2 for d in durations) / len(durations)
        balance = max(0, 1 - (dur_variance / 20))
        scores.append(balance * 0.15)
        
        # Intensity curve match (10%)
        scores.append(0.08)  # Simplified
        
        total_score = sum(scores) * 100
        return min(100, total_score), warnings
    
    def _calc_bump_coverage(self, bumps: List[RetentionBump], duration: float) -> float:
        """Calculate what percentage of video has bump coverage"""
        if not bumps or duration <= 0:
            return 0
        
        # Check for gaps > 8 seconds
        max_gap = 8.0
        gaps_ok = True
        current = 2.0  # Start after initial 2 seconds
        
        for bump in bumps:
            if bump.timestamp - current > max_gap:
                gaps_ok = False
                break
            current = bump.timestamp
        
        # Check end gap
        if duration - current > max_gap + 2:
            gaps_ok = False
        
        if gaps_ok:
            return 1.0
        else:
            covered = sum(1 for bump in bumps if bump.timestamp < duration - 2)
            expected = int(duration / 6)
            return min(1.0, covered / max(1, expected))


# Create and register engine
pacing_engine = PacingEngine()
EngineRegistry.register(
    pacing_engine,
    EngineDefinition(
        engine_id="pacing_engine_v1",
        engine_type="pacing",
        version="1.0.0",
        capabilities=["segment_timing", "retention_bumps", "visual_instructions", "quality_scoring"],
        required_inputs=["target_duration"],
        optional_inputs=["preset", "main_points", "intensity"],
        output_types=["pacing_timeline", "bump_schedule", "visual_instructions"]
    )
)

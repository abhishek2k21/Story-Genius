"""
Thumbnail Engine
Main engine for thumbnail generation and CTR optimization.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import uuid
import os

from app.engines.base import BaseEngine, EngineInput, EngineOutput, EngineStatus, EngineDefinition
from app.engines.registry import EngineRegistry
from app.engines.thumbnail.extraction import extract_frames, ExtractionConfig, ExtractedFrame
from app.engines.thumbnail.analysis import analyze_frame, rank_frames, FrameAnalysis
from app.engines.thumbnail.presets import get_style, optimize_text, ThumbStyle
from app.engines.thumbnail.composition import (
    compose_thumbnail, find_best_text_position, ComposedThumbnail
)
from app.engines.thumbnail.export import export_for_all_platforms, ThumbnailExport
from app.engines.thumbnail.scoring import calculate_ctr_score, CTRScore
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ThumbnailCandidate:
    """A thumbnail candidate with scores"""
    frame: ExtractedFrame
    analysis: FrameAnalysis
    composed: ComposedThumbnail
    ctr_score: CTRScore
    rank: int
    
    def to_dict(self) -> Dict:
        return {
            "rank": self.rank,
            "frame": self.frame.to_dict(),
            "analysis": self.analysis.to_dict(),
            "composed": self.composed.to_dict(),
            "ctr_score": self.ctr_score.to_dict()
        }


@dataclass
class ThumbnailResult:
    """Complete thumbnail generation result"""
    thumbnail_id: str
    candidates: List[ThumbnailCandidate]
    recommended_index: int
    exports: List[ThumbnailExport]
    text_used: str
    
    def to_dict(self) -> Dict:
        return {
            "thumbnail_id": self.thumbnail_id,
            "candidate_count": len(self.candidates),
            "recommended_index": self.recommended_index,
            "recommended": self.candidates[self.recommended_index].to_dict() if self.candidates else None,
            "candidates": [c.to_dict() for c in self.candidates],
            "export_count": len(self.exports),
            "exports": [e.to_dict() for e in self.exports],
            "text_used": self.text_used
        }


class ThumbnailEngine(BaseEngine):
    """Engine for thumbnail generation and CTR optimization"""
    
    def __init__(self):
        super().__init__(
            engine_id="thumbnail_engine_v1",
            engine_type="thumbnail",
            version="1.0.0"
        )
    
    def validate_input(self, input_data: EngineInput) -> Dict:
        errors = []
        params = input_data.parameters
        
        # Need video path or mock mode
        if not params.get("video_path") and not params.get("mock_mode"):
            errors.append("Missing required: video_path")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Generate thumbnails for video"""
        self.status = EngineStatus.RUNNING
        
        params = input_data.parameters
        video_path = params.get("video_path", "")
        text = params.get("text", "Amazing Content!")
        style_preset = params.get("style", "bold_shadow")
        candidate_count = params.get("candidate_count", 5)
        platforms = params.get("platforms")
        output_dir = params.get("output_dir", "output/thumbnails")
        mock_mode = params.get("mock_mode", False)
        
        # Generate unique ID
        thumbnail_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(output_dir, thumbnail_id)
        frames_dir = os.path.join(work_dir, "frames")
        composed_dir = os.path.join(work_dir, "composed")
        exports_dir = os.path.join(work_dir, "exports")
        
        # Get style
        style = get_style(style_preset)
        
        # Optimize text
        optimized_text = optimize_text(text)
        
        # Extract frames
        if mock_mode:
            frames = _generate_mock_frames(frames_dir, candidate_count * 2)
        else:
            config = ExtractionConfig(interval=0.5, max_frames=candidate_count * 3)
            frames = extract_frames(video_path, frames_dir, config)
        
        # Analyze frames
        analyses = []
        for frame in frames:
            analysis = analyze_frame(frame.file_path, frame.frame_id)
            analyses.append((frame, analysis))
        
        # Rank and select top candidates
        analyses.sort(key=lambda x: x[1].quality_score, reverse=True)
        top_candidates = analyses[:candidate_count]
        
        # Compose thumbnails
        candidates = []
        for i, (frame, analysis) in enumerate(top_candidates):
            position = find_best_text_position(analysis, frame.width, frame.height)
            
            composed_path = os.path.join(composed_dir, f"thumb_{i}.png")
            composed = compose_thumbnail(
                frame_path=frame.file_path,
                frame_id=frame.frame_id,
                text=optimized_text,
                position=position,
                style=style,
                output_path=composed_path,
                analysis=analysis
            )
            
            ctr_score = calculate_ctr_score(analysis, optimized_text)
            
            candidates.append(ThumbnailCandidate(
                frame=frame,
                analysis=analysis,
                composed=composed,
                ctr_score=ctr_score,
                rank=i + 1
            ))
        
        # Rank by CTR score
        candidates.sort(key=lambda c: c.ctr_score.total_score, reverse=True)
        for i, c in enumerate(candidates):
            c.rank = i + 1
        
        # Export best candidate for all platforms
        exports = []
        if candidates:
            best = candidates[0]
            exports = export_for_all_platforms(
                source_path=best.composed.output_path,
                thumbnail_id=thumbnail_id,
                output_dir=exports_dir,
                platforms=platforms
            )
        
        result = ThumbnailResult(
            thumbnail_id=thumbnail_id,
            candidates=candidates,
            recommended_index=0,
            exports=exports,
            text_used=optimized_text
        )
        
        self.status = EngineStatus.COMPLETED
        
        return EngineOutput(
            job_id=input_data.job_id,
            engine_id=self.engine_id,
            status=EngineStatus.COMPLETED,
            primary_artifact=thumbnail_id,
            metadata=result.to_dict(),
            quality_scores={
                "ctr_prediction": candidates[0].ctr_score.total_score if candidates else 0
            }
        )
    
    def validate_output(self, output: EngineOutput) -> Dict:
        errors = []
        if not output.metadata.get("candidates"):
            errors.append("No thumbnail candidates generated")
        return {"valid": len(errors) == 0, "errors": errors}


def _generate_mock_frames(output_dir: str, count: int) -> List[ExtractedFrame]:
    """Generate mock frames for testing"""
    from app.engines.thumbnail.extraction import ExtractionConfig, _generate_mock_frames
    config = ExtractionConfig(max_frames=count)
    return _generate_mock_frames(output_dir, config)


# Create and register engine
thumbnail_engine = ThumbnailEngine()
EngineRegistry.register(
    thumbnail_engine,
    EngineDefinition(
        engine_id="thumbnail_engine_v1",
        engine_type="thumbnail",
        version="1.0.0",
        capabilities=["frame_extraction", "quality_analysis", "composition", "multi_export", "ctr_scoring"],
        required_inputs=["video_path"],
        optional_inputs=["text", "style", "candidate_count", "platforms"],
        output_types=["thumbnail_candidates", "platform_exports", "ctr_scores"]
    )
)

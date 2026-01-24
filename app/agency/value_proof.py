"""
Value Proof Generator
Creates before/after comparisons for sales and validation.
"""
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValueProof:
    """Quantified value proof from a pilot."""
    agency_name: str
    pilot_date: datetime
    
    # Before (manual process)
    before_videos_per_day: int
    before_time_per_video_min: int
    before_cost_per_video: float  # in INR
    before_editors_needed: int
    
    # After (with platform)
    after_videos_per_day: int
    after_time_per_video_sec: int
    after_cost_per_video: float  # in INR
    after_editors_needed: int
    
    # Actual pilot results
    pilot_videos_generated: int
    pilot_success_rate: float
    pilot_avg_quality_score: float
    
    # Calculated improvements
    speed_multiplier: float = 0.0
    cost_reduction_percent: float = 0.0
    time_saved_hours: float = 0.0
    
    def calculate_improvements(self):
        """Calculate improvement metrics."""
        # Speed: videos per day improvement
        if self.before_videos_per_day > 0:
            self.speed_multiplier = self.after_videos_per_day / self.before_videos_per_day
        
        # Cost reduction
        if self.before_cost_per_video > 0:
            self.cost_reduction_percent = (
                (self.before_cost_per_video - self.after_cost_per_video) 
                / self.before_cost_per_video * 100
            )
        
        # Time saved (per 100 videos)
        before_hours = (self.before_time_per_video_min * 100) / 60
        after_hours = (self.after_time_per_video_sec * 100) / 3600
        self.time_saved_hours = before_hours - after_hours
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        return f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      VALUE PROOF: {self.agency_name.upper()}
╠══════════════════════════════════════════════════════════════════════╣
║  PILOT DATE: {self.pilot_date.strftime('%Y-%m-%d')}
╠══════════════════════════════════════════════════════════════════════╣
║  BEFORE (MANUAL)               AFTER (PLATFORM)
║  ─────────────────────         ─────────────────────
║  {self.before_videos_per_day} videos/day                  {self.after_videos_per_day} videos/day
║  {self.before_time_per_video_min} min/video                  {self.after_time_per_video_sec} sec/video
║  ₹{self.before_cost_per_video:.0f}/video                     ₹{self.after_cost_per_video:.2f}/video
║  {self.before_editors_needed} editors                       {self.after_editors_needed} editors
╠══════════════════════════════════════════════════════════════════════╣
║  IMPROVEMENTS
║  ─────────────────────
║  ⚡ Speed:     {self.speed_multiplier:.1f}x faster
║  💰 Cost:      {self.cost_reduction_percent:.0f}% reduction
║  ⏰ Time:      {self.time_saved_hours:.0f} hours saved per 100 videos
╠══════════════════════════════════════════════════════════════════════╣
║  PILOT RESULTS
║  ─────────────────────
║  Videos: {self.pilot_videos_generated}
║  Success Rate: {self.pilot_success_rate:.0%}
║  Avg Quality: {self.pilot_avg_quality_score:.2f}
╚══════════════════════════════════════════════════════════════════════╝
"""


class ValueProofGenerator:
    """
    Generates value proofs from pilot data.
    """
    
    def __init__(self):
        self._proofs: List[ValueProof] = []
    
    def create_proof(
        self,
        agency_name: str,
        before_metrics: Dict,
        after_metrics: Dict,
        pilot_results: Dict
    ) -> ValueProof:
        """
        Create a value proof from pilot data.
        
        Args:
            agency_name: Name of the pilot agency
            before_metrics: Their manual process metrics
            after_metrics: Platform metrics
            pilot_results: Actual pilot results
            
        Returns:
            Complete ValueProof
        """
        proof = ValueProof(
            agency_name=agency_name,
            pilot_date=datetime.utcnow(),
            before_videos_per_day=before_metrics.get("videos_per_day", 5),
            before_time_per_video_min=before_metrics.get("time_per_video_min", 60),
            before_cost_per_video=before_metrics.get("cost_per_video", 200),
            before_editors_needed=before_metrics.get("editors", 2),
            after_videos_per_day=after_metrics.get("videos_per_day", 50),
            after_time_per_video_sec=after_metrics.get("time_per_video_sec", 20),
            after_cost_per_video=after_metrics.get("cost_per_video", 1),
            after_editors_needed=after_metrics.get("editors", 0),
            pilot_videos_generated=pilot_results.get("videos", 0),
            pilot_success_rate=pilot_results.get("success_rate", 0),
            pilot_avg_quality_score=pilot_results.get("avg_score", 0)
        )
        
        proof.calculate_improvements()
        self._proofs.append(proof)
        
        logger.info(f"Created value proof for {agency_name}: {proof.speed_multiplier:.1f}x faster")
        
        return proof
    
    def export_json(self, proof: ValueProof) -> str:
        """Export proof as JSON."""
        data = asdict(proof)
        data["pilot_date"] = proof.pilot_date.isoformat()
        return json.dumps(data, indent=2)
    
    def generate_sales_snippet(self, proof: ValueProof) -> str:
        """Generate a short sales-ready snippet."""
        return (
            f"🏢 {proof.agency_name} Pilot Results:\n"
            f"• {proof.speed_multiplier:.0f}x faster video production\n"
            f"• {proof.cost_reduction_percent:.0f}% cost reduction per video\n"
            f"• {proof.time_saved_hours:.0f} hours saved per 100 videos\n"
            f"• {proof.pilot_videos_generated} videos at {proof.pilot_success_rate:.0%} success rate"
        )

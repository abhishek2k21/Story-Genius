"""
Economics Model
Cost tracking and value estimation for unit economics analysis.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CostBreakdown:
    """Cost breakdown for a single video generation."""
    job_id: str
    
    # Direct costs (USD)
    llm_cost: float = 0.0      # LLM API calls
    image_cost: float = 0.0    # Image generation
    audio_cost: float = 0.0    # TTS generation
    video_cost: float = 0.0    # Video processing
    
    # Computed
    total_cost: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_total(self):
        """Calculate total cost."""
        self.total_cost = self.llm_cost + self.image_cost + self.audio_cost + self.video_cost


@dataclass
class ValueEstimate:
    """Value estimation for a video."""
    job_id: str
    
    # Revenue proxies
    estimated_views: int = 0
    cpm_rate: float = 4.0  # USD per 1000 views (YouTube Shorts avg)
    
    # Calculated revenue
    estimated_revenue: float = 0.0
    
    # Agency pricing model
    agency_rate: float = 50.0  # USD per video (agency client pricing)
    
    # Quality multiplier
    quality_score: float = 0.8
    
    def calculate_revenue(self):
        """Calculate estimated revenue."""
        # Ad revenue estimate
        self.estimated_revenue = (self.estimated_views / 1000) * self.cpm_rate * self.quality_score


@dataclass
class UnitEconomics:
    """Complete unit economics for a video."""
    job_id: str
    cost: CostBreakdown
    value: ValueEstimate
    
    # ROI metrics
    roi_multiplier: float = 0.0
    profit_margin: float = 0.0
    break_even_views: int = 0
    
    def calculate_roi(self):
        """Calculate ROI metrics."""
        if self.cost.total_cost > 0:
            self.roi_multiplier = self.value.estimated_revenue / self.cost.total_cost
            self.profit_margin = (self.value.estimated_revenue - self.cost.total_cost) / self.value.estimated_revenue if self.value.estimated_revenue > 0 else 0
            self.break_even_views = int((self.cost.total_cost / self.value.cpm_rate) * 1000)


# ============== COST RATES ==============

COST_RATES = {
    "llm": {
        "gemini_flash": 0.00015,     # per 1K input tokens
        "gemini_pro": 0.00125,       # per 1K input tokens
        "calls_per_video": 8         # avg calls per video
    },
    "image": {
        "imagen": 0.02,              # per image
        "midjourney": 0.05,          # per image
        "images_per_video": 0        # currently not generating
    },
    "audio": {
        "edge_tts": 0.0,             # free
        "google_tts": 0.004,         # per 1M characters
        "scenes_per_video": 6
    },
    "video": {
        "veo": 0.05,                 # per clip (estimated)
        "moviepy": 0.0               # free (local processing)
    }
}


class EconomicsService:
    """
    Service for tracking costs and estimating value.
    """
    
    def __init__(self):
        self._costs: Dict[str, CostBreakdown] = {}
        self._values: Dict[str, ValueEstimate] = {}
    
    def estimate_cost(
        self,
        job_id: str,
        llm_calls: int = 8,
        images: int = 0,
        audio_scenes: int = 6,
        video_clips: int = 0
    ) -> CostBreakdown:
        """
        Estimate cost for a video generation.
        
        Args:
            job_id: Job ID
            llm_calls: Number of LLM API calls
            images: Number of images generated
            audio_scenes: Number of audio clips
            video_clips: Number of video clips
            
        Returns:
            CostBreakdown
        """
        cost = CostBreakdown(job_id=job_id)
        
        # LLM costs (Gemini Flash)
        avg_tokens_per_call = 2000
        cost.llm_cost = llm_calls * avg_tokens_per_call * COST_RATES["llm"]["gemini_flash"] / 1000
        
        # Image costs
        cost.image_cost = images * COST_RATES["image"]["imagen"]
        
        # Audio costs (Edge TTS is free)
        cost.audio_cost = 0.0
        
        # Video costs
        cost.video_cost = video_clips * COST_RATES["video"]["veo"]
        
        cost.calculate_total()
        self._costs[job_id] = cost
        
        logger.debug(f"Estimated cost for {job_id[:8]}: ${cost.total_cost:.4f}")
        return cost
    
    def estimate_value(
        self,
        job_id: str,
        estimated_views: int = 1000,
        cpm_rate: float = 4.0,
        quality_score: float = 0.8
    ) -> ValueEstimate:
        """
        Estimate value/revenue for a video.
        
        Args:
            job_id: Job ID
            estimated_views: Expected views
            cpm_rate: CPM rate (USD per 1000 views)
            quality_score: Quality multiplier
            
        Returns:
            ValueEstimate
        """
        value = ValueEstimate(
            job_id=job_id,
            estimated_views=estimated_views,
            cpm_rate=cpm_rate,
            quality_score=quality_score
        )
        
        value.calculate_revenue()
        self._values[job_id] = value
        
        logger.debug(f"Estimated value for {job_id[:8]}: ${value.estimated_revenue:.2f}")
        return value
    
    def calculate_unit_economics(
        self,
        job_id: str,
        estimated_views: int = 1000
    ) -> UnitEconomics:
        """
        Calculate complete unit economics for a job.
        
        Args:
            job_id: Job ID
            estimated_views: Expected views
            
        Returns:
            UnitEconomics with ROI metrics
        """
        # Get or create cost estimate
        cost = self._costs.get(job_id) or self.estimate_cost(job_id)
        
        # Get or create value estimate
        value = self._values.get(job_id) or self.estimate_value(job_id, estimated_views)
        
        economics = UnitEconomics(
            job_id=job_id,
            cost=cost,
            value=value
        )
        
        economics.calculate_roi()
        
        logger.info(f"Unit economics for {job_id[:8]}: "
                   f"Cost=${cost.total_cost:.4f}, Value=${value.estimated_revenue:.2f}, "
                   f"ROI={economics.roi_multiplier:.1f}x")
        
        return economics
    
    def get_batch_economics(self, job_ids: list) -> Dict:
        """Get aggregate economics for a batch of videos."""
        total_cost = 0.0
        total_value = 0.0
        
        for job_id in job_ids:
            cost = self._costs.get(job_id)
            value = self._values.get(job_id)
            
            if cost:
                total_cost += cost.total_cost
            if value:
                total_value += value.estimated_revenue
        
        return {
            "total_videos": len(job_ids),
            "total_cost": round(total_cost, 4),
            "total_value": round(total_value, 2),
            "avg_cost_per_video": round(total_cost / len(job_ids), 4) if job_ids else 0,
            "avg_value_per_video": round(total_value / len(job_ids), 2) if job_ids else 0,
            "overall_roi": round(total_value / total_cost, 1) if total_cost > 0 else 0
        }
    
    def get_pricing_recommendation(
        self,
        cost_per_video: float,
        target_margin: float = 0.7
    ) -> Dict:
        """
        Get pricing recommendations based on costs.
        
        Args:
            cost_per_video: Actual cost per video
            target_margin: Target profit margin (0-1)
            
        Returns:
            Pricing recommendations
        """
        min_price = cost_per_video / (1 - target_margin)
        
        return {
            "cost_per_video": round(cost_per_video, 4),
            "target_margin": target_margin,
            "minimum_price": round(min_price, 2),
            "recommended_prices": {
                "basic": round(min_price * 1.2, 2),
                "standard": round(min_price * 1.5, 2),
                "premium": round(min_price * 2.0, 2)
            },
            "agency_batch_pricing": {
                "10_videos": round(min_price * 10 * 0.9, 2),
                "50_videos": round(min_price * 50 * 0.8, 2),
                "100_videos": round(min_price * 100 * 0.7, 2)
            }
        }

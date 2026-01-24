"""
Channel Service
Multi-channel orchestration for generating content across multiple channels from one idea.
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum

from app.core.logging import get_logger
from app.core.models import Job, JobStatus
from app.orchestrator.service import OrchestratorService

logger = get_logger(__name__)


@dataclass
class ChannelProfile:
    """
    A channel profile defines the brand identity for a content channel.
    """
    id: str
    name: str
    description: str
    
    # Content settings
    platform: str = "youtube_shorts"
    persona_id: str = "curious_kid"
    visual_style_id: str = "bright_kids_cartoon"
    
    # Audience
    target_audience: str = "kids_india"
    genre: str = "kids"
    language: str = "en-hi"
    
    # Defaults
    default_duration: int = 30
    
    # Monetization
    is_monetized: bool = False
    owner_id: str = ""
    
    def to_job_config(self) -> dict:
        """Convert to job configuration."""
        return {
            "platform": self.platform,
            "audience": self.target_audience,
            "genre": self.genre,
            "language": self.language,
            "duration": self.default_duration
        }


# ============== PRESET CHANNELS ==============

PRESET_CHANNELS: Dict[str, ChannelProfile] = {
    "kids_fun_facts": ChannelProfile(
        id="kids_fun_facts",
        name="Kids Fun Facts",
        description="Fun educational facts for children",
        platform="youtube_shorts",
        persona_id="curious_kid",
        visual_style_id="bright_kids_cartoon",
        target_audience="kids_india",
        genre="kids"
    ),
    
    "mind_blowers": ChannelProfile(
        id="mind_blowers",
        name="Mind Blowers",
        description="Fast facts that blow your mind",
        platform="youtube_shorts",
        persona_id="fast_explainer",
        visual_style_id="minimal_facts",
        target_audience="genz_us",
        genre="facts"
    ),
    
    "thriller_tales": ChannelProfile(
        id="thriller_tales",
        name="Thriller Tales",
        description="Short thriller stories with twists",
        platform="tiktok",
        persona_id="storyteller",
        visual_style_id="cinematic_dark",
        target_audience="genz",
        genre="thriller"
    ),
    
    "motivation_daily": ChannelProfile(
        id="motivation_daily",
        name="Motivation Daily",
        description="Daily motivation and success stories",
        platform="instagram_reels",
        persona_id="hype_master",
        visual_style_id="neon_genz",
        target_audience="motivation",
        genre="success"
    ),
    
    "mythology_magic": ChannelProfile(
        id="mythology_magic",
        name="Mythology Magic",
        description="Ancient stories and legends",
        platform="youtube_shorts",
        persona_id="storyteller",
        visual_style_id="mythological_epic",
        target_audience="kids_india",
        genre="mythology"
    )
}


@dataclass
class MultiChannelResult:
    """Result of multi-channel generation."""
    idea: str
    channel_results: List[Dict]
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_time_sec: float


class ChannelService:
    """
    Multi-channel orchestration service.
    Generates content for multiple channels from a single idea.
    """
    
    def __init__(self):
        self._channels: Dict[str, ChannelProfile] = dict(PRESET_CHANNELS)
        self.orchestrator = OrchestratorService()
    
    def register_channel(self, profile: ChannelProfile) -> str:
        """Register a new channel profile."""
        self._channels[profile.id] = profile
        logger.info(f"Registered channel: {profile.name}")
        return profile.id
    
    def get_channel(self, channel_id: str) -> Optional[ChannelProfile]:
        """Get channel by ID."""
        return self._channels.get(channel_id)
    
    def list_channels(self) -> List[str]:
        """List all channel IDs."""
        return list(self._channels.keys())
    
    def generate_for_channel(
        self,
        channel_id: str,
        topic: str = None
    ) -> Dict:
        """
        Generate a single video for a specific channel.
        
        Args:
            channel_id: Target channel
            topic: Optional topic override
            
        Returns:
            Result dict with job_id, success, score
        """
        channel = self.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel not found: {channel_id}")
        
        config = channel.to_job_config()
        if topic:
            config["topic"] = topic
        
        job = self.orchestrator.create_job(config)
        success = self.orchestrator.start_job(job.id)
        final_job = self.orchestrator.get_job(job.id)
        
        return {
            "channel_id": channel_id,
            "channel_name": channel.name,
            "job_id": job.id,
            "success": success,
            "score": final_job.total_score if final_job else 0,
            "persona": channel.persona_id,
            "visual_style": channel.visual_style_id
        }
    
    def generate_multi_channel(
        self,
        idea: str,
        channel_ids: List[str] = None,
        max_channels: int = 3
    ) -> MultiChannelResult:
        """
        Generate the same idea across multiple channels.
        
        Args:
            idea: Content idea/topic
            channel_ids: Specific channels (or use defaults)
            max_channels: Max number of channels
            
        Returns:
            MultiChannelResult with all results
        """
        import time
        start = time.time()
        
        # Use provided channels or pick diverse defaults
        if not channel_ids:
            all_channels = list(self._channels.keys())
            channel_ids = all_channels[:max_channels]
        else:
            channel_ids = channel_ids[:max_channels]
        
        logger.info(f"Multi-channel generation: '{idea}' → {len(channel_ids)} channels")
        
        results = []
        successful = 0
        failed = 0
        
        for channel_id in channel_ids:
            try:
                result = self.generate_for_channel(channel_id, topic=idea)
                results.append(result)
                
                if result["success"]:
                    successful += 1
                    logger.info(f"  ✓ {channel_id}: Score {result['score']:.2f}")
                else:
                    failed += 1
                    logger.warning(f"  ✗ {channel_id}: Failed")
                    
            except Exception as e:
                logger.error(f"  ✗ {channel_id}: Error - {e}")
                results.append({
                    "channel_id": channel_id,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        elapsed = time.time() - start
        
        return MultiChannelResult(
            idea=idea,
            channel_results=results,
            total_jobs=len(channel_ids),
            successful_jobs=successful,
            failed_jobs=failed,
            total_time_sec=round(elapsed, 2)
        )
    
    def generate_persona_variants(
        self,
        idea: str,
        persona_ids: List[str],
        base_channel_id: str = "kids_fun_facts"
    ) -> MultiChannelResult:
        """
        Generate same idea with different personas.
        
        Args:
            idea: Content idea
            persona_ids: List of persona IDs to use
            base_channel_id: Base channel for settings
            
        Returns:
            MultiChannelResult
        """
        base = self.get_channel(base_channel_id)
        if not base:
            base = list(self._channels.values())[0]
        
        # Create temporary channels for each persona
        temp_channels = []
        for persona_id in persona_ids:
            temp_id = f"temp_{persona_id}_{uuid.uuid4().hex[:6]}"
            temp_channel = ChannelProfile(
                id=temp_id,
                name=f"Temp {persona_id}",
                description="Temporary persona variant",
                platform=base.platform,
                persona_id=persona_id,
                visual_style_id=base.visual_style_id,
                target_audience=base.target_audience,
                genre=base.genre
            )
            self._channels[temp_id] = temp_channel
            temp_channels.append(temp_id)
        
        # Generate for all temp channels
        result = self.generate_multi_channel(idea, temp_channels)
        
        # Cleanup temp channels
        for temp_id in temp_channels:
            del self._channels[temp_id]
        
        return result
    
    def close(self):
        """Close orchestrator connection."""
        self.orchestrator.close()

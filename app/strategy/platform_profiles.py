"""
Platform Profiles
Defines platform-specific requirements and optimization settings.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoopImportance(str, Enum):
    """How important loop/replay is for platform algorithm."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TitleImportance(str, Enum):
    """How visible/important title is on platform."""
    HIDDEN = "hidden"      # TikTok - title barely shown
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"          # YouTube - very prominent


@dataclass
class PlatformProfile:
    """
    Platform-specific settings and requirements.
    """
    id: str
    name: str
    
    # Duration settings
    ideal_duration_min: int  # seconds
    ideal_duration_max: int  # seconds
    absolute_max: int        # hard limit
    
    # Hook settings
    hook_window: float       # seconds for hook
    hook_aggressiveness: str # "subtle", "moderate", "aggressive"
    
    # Loop/Replay importance
    loop_importance: LoopImportance
    loop_style: str          # "question", "cliffhanger", "callback"
    
    # Metadata settings
    title_importance: TitleImportance
    max_title_length: int
    description_style: str   # "minimal", "keyword-rich", "narrative"
    hashtag_count: int
    
    # Visual settings
    aspect_ratio: str
    resolution: str
    
    # Algorithm hints
    algorithm_notes: List[str] = field(default_factory=list)
    
    def should_trim_to_ideal(self, current_duration: int) -> bool:
        """Check if video should be trimmed."""
        return current_duration > self.ideal_duration_max
    
    def get_ideal_duration(self) -> int:
        """Get middle of ideal range."""
        return (self.ideal_duration_min + self.ideal_duration_max) // 2


# ============== PLATFORM PROFILE DEFINITIONS ==============

PLATFORM_PROFILES: Dict[str, PlatformProfile] = {
    "youtube_shorts": PlatformProfile(
        id="youtube_shorts",
        name="YouTube Shorts",
        ideal_duration_min=27,
        ideal_duration_max=33,
        absolute_max=60,
        hook_window=2.0,
        hook_aggressiveness="aggressive",
        loop_importance=LoopImportance.HIGH,
        loop_style="question",
        title_importance=TitleImportance.MEDIUM,
        max_title_length=70,
        description_style="keyword-rich",
        hashtag_count=5,
        aspect_ratio="9:16",
        resolution="1080x1920",
        algorithm_notes=[
            "First 2 seconds crucial for retention",
            "Strong loop increases watch time",
            "Title shown in Shorts shelf - make it punchy",
            "Hashtags less important than long-form"
        ]
    ),
    
    "instagram_reels": PlatformProfile(
        id="instagram_reels",
        name="Instagram Reels",
        ideal_duration_min=15,
        ideal_duration_max=30,
        absolute_max=90,
        hook_window=1.5,
        hook_aggressiveness="aggressive",
        loop_importance=LoopImportance.CRITICAL,
        loop_style="seamless_loop",
        title_importance=TitleImportance.LOW,
        max_title_length=50,
        description_style="minimal",
        hashtag_count=8,
        aspect_ratio="9:16",
        resolution="1080x1920",
        algorithm_notes=[
            "Loop is KING - seamless loops get boosted",
            "Shorter is often better (15-20s sweet spot)",
            "Caption is the title",
            "Hashtags still matter for discovery"
        ]
    ),
    
    "tiktok": PlatformProfile(
        id="tiktok",
        name="TikTok",
        ideal_duration_min=20,
        ideal_duration_max=35,
        absolute_max=180,
        hook_window=1.0,
        hook_aggressiveness="extreme",
        loop_importance=LoopImportance.CRITICAL,
        loop_style="cliffhanger",
        title_importance=TitleImportance.HIDDEN,
        max_title_length=40,
        description_style="minimal",
        hashtag_count=5,
        aspect_ratio="9:16",
        resolution="1080x1920",
        algorithm_notes=[
            "First 1 second is EVERYTHING",
            "Loop increases average watch time significantly",
            "Trending sounds boost reach",
            "Hashtags: use trending + niche mix"
        ]
    )
}


class PlatformService:
    """
    Service for platform-aware content optimization.
    """
    
    @classmethod
    def get_profile(cls, platform: str) -> Optional[PlatformProfile]:
        """Get profile by platform ID."""
        # Handle enum values
        if hasattr(platform, 'value'):
            platform = platform.value
        
        platform_key = platform.lower().replace("-", "_").replace(" ", "_")
        return PLATFORM_PROFILES.get(platform_key)
    
    @classmethod
    def get_ideal_duration(cls, platform: str) -> int:
        """Get ideal duration for platform."""
        profile = cls.get_profile(platform)
        return profile.get_ideal_duration() if profile else 30
    
    @classmethod
    def get_hook_window(cls, platform: str) -> float:
        """Get hook window in seconds."""
        profile = cls.get_profile(platform)
        return profile.hook_window if profile else 2.0
    
    @classmethod
    def should_use_aggressive_hook(cls, platform: str) -> bool:
        """Check if platform needs aggressive hooks."""
        profile = cls.get_profile(platform)
        if not profile:
            return True
        return profile.hook_aggressiveness in ["aggressive", "extreme"]
    
    @classmethod
    def get_loop_style(cls, platform: str) -> str:
        """Get recommended loop ending style."""
        profile = cls.get_profile(platform)
        return profile.loop_style if profile else "question"
    
    @classmethod
    def optimize_duration(
        cls,
        platform: str,
        current_duration: int
    ) -> int:
        """Get optimized duration for platform."""
        profile = cls.get_profile(platform)
        if not profile:
            return min(current_duration, 35)
        
        if current_duration < profile.ideal_duration_min:
            return profile.ideal_duration_min
        elif current_duration > profile.ideal_duration_max:
            return profile.ideal_duration_max
        
        return current_duration
    
    @classmethod
    def get_metadata_guidelines(cls, platform: str) -> Dict:
        """Get metadata formatting guidelines."""
        profile = cls.get_profile(platform)
        if not profile:
            return {"max_title": 60, "hashtags": 5}
        
        return {
            "max_title": profile.max_title_length,
            "hashtags": profile.hashtag_count,
            "title_importance": profile.title_importance.value,
            "description_style": profile.description_style
        }
    
    @classmethod
    def list_platforms(cls) -> List[str]:
        """List all platform IDs."""
        return list(PLATFORM_PROFILES.keys())
    
    @classmethod
    def get_algorithm_notes(cls, platform: str) -> List[str]:
        """Get algorithm optimization notes."""
        profile = cls.get_profile(platform)
        return profile.algorithm_notes if profile else []

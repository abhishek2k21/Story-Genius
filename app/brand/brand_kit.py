"""
Week 18 Day 3 - Brand Kit System
Save creator's visual style, voice, and branding preferences.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import uuid


@dataclass
class BrandKit:
    """
    Configuration for consistent channel branding.
    """
    user_id: str
    name: str = "Default Brand"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Style
    visual_style: str = "cinematic"  # "neon_genz", "minimal", "cinematic"
    color_palette: List[str] = field(default_factory=lambda: ["#FFFFFF", "#000000"])
    
    # Audio
    voice_preference: str = "en-US-AndrewNeural"
    background_music_style: str = "lofi"
    
    # Templates
    intro_template: Optional[str] = None  # e.g. "Welcome back to [Channel]!"
    outro_template: Optional[str] = None  # e.g. "Subscribe for more."
    
    # Assets
    logo_url: Optional[str] = None
    watermark_text: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "visual_style": self.visual_style,
            "color_palette": self.color_palette,
            "voice_preference": self.voice_preference,
            "intro_template": self.intro_template,
            "outro_template": self.outro_template,
            "logo_url": self.logo_url,
            "created_at": self.created_at.isoformat()
        }


class BrandKitService:
    """Service to manage Brand Kits."""
    
    def __init__(self):
        # Simulation of DB
        self._kits: Dict[str, BrandKit] = {}
        
    def create_kit(self, user_id: str, name: str, **kwargs) -> BrandKit:
        """Create a new brand kit."""
        kit = BrandKit(user_id=user_id, name=name, **kwargs)
        self._kits[kit.id] = kit
        return kit
        
    def get_kit(self, kit_id: str) -> Optional[BrandKit]:
        """Get kit by ID."""
        return self._kits.get(kit_id)
    
    def list_user_kits(self, user_id: str) -> List[BrandKit]:
        """List all kits for a user."""
        return [k for k in self._kits.values() if k.user_id == user_id]
        
    def get_default_kit(self, user_id: str) -> BrandKit:
        """Get or create a default kit."""
        user_kits = self.list_user_kits(user_id)
        if user_kits:
            return user_kits[0]
        return self.create_kit(user_id, "Default Brand")
    
    def apply_branding(self, script_text: str, kit: BrandKit) -> str:
        """
        Apply intro/outro from brand kit to script.
        Simple string injection.
        """
        final_script = script_text
        
        if kit.intro_template:
            final_script = f"{kit.intro_template}\n\n{final_script}"
            
        if kit.outro_template:
            final_script = f"{final_script}\n\n{kit.outro_template}"
            
        return final_script


# Singleton
_brand_service = None

def get_brand_service() -> BrandKitService:
    global _brand_service
    if _brand_service is None:
        _brand_service = BrandKitService()
    return _brand_service

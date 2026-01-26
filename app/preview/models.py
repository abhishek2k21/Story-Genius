"""
Week 18 Day 1 - Preview Models
Data models for video preview before full generation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import uuid


class PreviewStatus(str, Enum):
    """Status of a preview."""
    PENDING = "pending"
    READY = "ready"
    EDITING = "editing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScenePreview:
    """Preview of a single scene."""
    id: int
    script: str
    visual_description: str
    estimated_duration: float  # seconds
    tone: str = "neutral"
    edited: bool = False
    original_script: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "script": self.script,
            "visual_description": self.visual_description,
            "estimated_duration": self.estimated_duration,
            "tone": self.tone,
            "edited": self.edited,
            "original_script": self.original_script
        }


@dataclass
class Preview:
    """Complete video preview before generation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PreviewStatus = PreviewStatus.PENDING
    
    # Content
    topic: str = ""
    scenes: List[ScenePreview] = field(default_factory=list)
    
    # Scoring
    hook_score: float = 0.0  # 0-100, how catchy is the hook
    depth_score: float = 0.0  # From Path 1
    
    # Estimates
    estimated_duration: float = 0.0  # seconds
    estimated_cost: float = 0.0  # USD
    
    # Config
    audience_baseline: str = "general_adult"
    tone: str = "neutral"
    language: str = "en"
    content_mode: str = "commentary"
    brand_kit_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "topic": self.topic,
            "scenes": [s.to_dict() for s in self.scenes],
            "hook_score": self.hook_score,
            "depth_score": self.depth_score,
            "estimated_duration": self.estimated_duration,
            "estimated_cost": self.estimated_cost,
            "audience_baseline": self.audience_baseline,
            "tone": self.tone,
            "language": self.language,
            "content_mode": self.content_mode,
            "brand_kit_id": self.brand_kit_id,
            "created_at": self.created_at.isoformat()
        }
    
    def get_full_script(self) -> str:
        return "\n\n".join(f"Scene {s.id}: {s.script}" for s in self.scenes)
    
    def update_estimates(self):
        """Recalculate duration and cost based on scenes."""
        self.estimated_duration = sum(s.estimated_duration for s in self.scenes)
        # Cost: ~$0.002 per scene for LLM + $0.01 per scene for video
        self.estimated_cost = len(self.scenes) * 0.012


@dataclass 
class PreviewWarning:
    """Warnings for preview."""
    type: str  # "low_hook", "risky_idea", "long_duration"
    message: str
    severity: str = "warning"  # "info", "warning", "danger"


@dataclass
class PreviewResult:
    """Result of preview generation."""
    preview: Preview
    warnings: List[PreviewWarning] = field(default_factory=list)
    generation_time_ms: int = 0
    
    def to_dict(self) -> dict:
        return {
            "preview": self.preview.to_dict(),
            "warnings": [{"type": w.type, "message": w.message, "severity": w.severity} for w in self.warnings],
            "generation_time_ms": self.generation_time_ms
        }

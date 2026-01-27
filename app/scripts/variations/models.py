"""
Script Variation Models
Data structures for variation generation and management.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class VariationStrategy(str, Enum):
    HOOK_FOCUSED = "hook_focused"
    TONE_VARIED = "tone_varied"
    STRUCTURE_VARIED = "structure_varied"
    ANGLE_VARIED = "angle_varied"
    LENGTH_VARIED = "length_varied"
    MIXED = "mixed"


class SelectionType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


@dataclass
class VariationRequest:
    """Request for generating script variations"""
    request_id: str
    user_id: str
    topic: str
    content_category: str
    target_duration: int
    platform: str
    variation_count: int = 3
    variation_strategy: VariationStrategy = VariationStrategy.MIXED
    style_hints: List[str] = field(default_factory=list)
    avoid_phrases: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "topic": self.topic,
            "content_category": self.content_category,
            "target_duration": self.target_duration,
            "platform": self.platform,
            "variation_count": self.variation_count,
            "variation_strategy": self.variation_strategy.value,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class VariationScores:
    """Scores for a script variation"""
    hook_strength: float = 0.0
    clarity: float = 0.0
    engagement_potential: float = 0.0
    pacing_fit: float = 0.0
    cta_effectiveness: float = 0.0
    uniqueness: float = 0.0
    
    def total(self) -> float:
        """Calculate weighted total score"""
        return (
            self.hook_strength * 0.25 +
            self.clarity * 0.20 +
            self.engagement_potential * 0.20 +
            self.pacing_fit * 0.15 +
            self.cta_effectiveness * 0.10 +
            self.uniqueness * 0.10
        )
    
    def to_dict(self) -> Dict:
        return {
            "hook_strength": round(self.hook_strength, 1),
            "clarity": round(self.clarity, 1),
            "engagement_potential": round(self.engagement_potential, 1),
            "pacing_fit": round(self.pacing_fit, 1),
            "cta_effectiveness": round(self.cta_effectiveness, 1),
            "uniqueness": round(self.uniqueness, 1),
            "total": round(self.total(), 1)
        }


@dataclass
class ScriptVariation:
    """A single script variation"""
    variation_id: str
    request_id: str
    variation_index: int
    hook: str
    body: str
    cta: str
    scores: VariationScores = field(default_factory=VariationScores)
    rank: int = 0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "variation_id": self.variation_id,
            "variation_index": self.variation_index,
            "hook": self.hook,
            "body": self.body,
            "cta": self.cta,
            "scores": self.scores.to_dict(),
            "rank": self.rank,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses
        }
    
    @property
    def full_script(self) -> str:
        return f"{self.hook}\n\n{self.body}\n\n{self.cta}"


@dataclass
class HookTest:
    """Hook A/B testing"""
    test_id: str
    user_id: str
    base_script_id: str
    body: str
    cta: str
    hook_count: int
    hooks: List[Dict] = field(default_factory=list)  # [{text, style, score}]
    selected_hook_index: Optional[int] = None
    selection_reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_id,
            "hook_count": self.hook_count,
            "hooks": self.hooks,
            "selected_hook_index": self.selected_hook_index,
            "status": "completed" if self.completed_at else "pending",
            "created_at": self.created_at.isoformat()
        }


@dataclass
class VariationSelection:
    """Selection of a variation"""
    selection_id: str
    request_id: str
    selected_variation_id: str
    selection_type: SelectionType
    selection_reason: str = ""
    modifications: Dict = field(default_factory=dict)
    final_script_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "selection_id": self.selection_id,
            "selected_variation_id": self.selected_variation_id,
            "selection_type": self.selection_type.value,
            "selection_reason": self.selection_reason,
            "final_script_id": self.final_script_id,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class VariationHistory:
    """History of variation choices"""
    history_id: str
    user_id: str
    request_id: str
    topic: str
    category: str
    variation_count: int
    selected_index: int
    selected_score: float
    average_score: float
    selection_type: SelectionType
    hook_style: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserPreferences:
    """Learned user preferences"""
    user_id: str
    preferred_hook_styles: List[str] = field(default_factory=list)
    preferred_tones: List[str] = field(default_factory=list)
    preferred_structures: List[str] = field(default_factory=list)
    minimum_score_threshold: float = 70.0
    edit_tendency: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "preferred_hook_styles": self.preferred_hook_styles,
            "preferred_tones": self.preferred_tones,
            "preferred_structures": self.preferred_structures,
            "minimum_score_threshold": self.minimum_score_threshold,
            "edit_tendency": round(self.edit_tendency, 2)
        }


def create_request_id() -> str:
    return str(uuid.uuid4())


def create_variation_id() -> str:
    return str(uuid.uuid4())

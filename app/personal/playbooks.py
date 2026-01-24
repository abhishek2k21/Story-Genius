"""
Personal Playbooks
Your thinking patterns encoded - one command = your style.
"""
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Playbook:
    """A personal playbook encoding your style."""
    id: str
    name: str
    description: str
    
    # Content locks
    hook_type: str
    emotion_curve: str
    persona: str
    visual_style: str
    
    # Metadata
    metadata_tone: str = "curiosity"
    hashtag_style: str = "minimal"
    
    # Quality
    min_score: float = 0.75
    target_duration: int = 30


# ============== YOUR PLAYBOOKS ==============

PLAYBOOKS: Dict[str, Playbook] = {
    "viral_fact": Playbook(
        id="viral_fact",
        name="Viral Fact Short",
        description="Mind-blowing facts with rapid pacing",
        hook_type="shock_statement",
        emotion_curve="curiosity_loop",
        persona="fast_explainer",
        visual_style="minimal_facts",
        metadata_tone="curiosity",
        target_duration=27
    ),
    
    "myth_breaker": Playbook(
        id="myth_breaker",
        name="Myth Breaker",
        description="Debunk common misconceptions",
        hook_type="pattern_interrupt",
        emotion_curve="revelation",
        persona="fast_explainer",
        visual_style="minimal_facts",
        metadata_tone="authority",
        target_duration=30
    ),
    
    "curiosity_loop": Playbook(
        id="curiosity_loop",
        name="Curiosity Loop",
        description="Open loop that demands rewatching",
        hook_type="question_gap",
        emotion_curve="curiosity_loop",
        persona="curious_kid",
        visual_style="bright_kids_cartoon",
        metadata_tone="playful",
        target_duration=25
    ),
    
    "high_authority": Playbook(
        id="high_authority",
        name="High Authority Take",
        description="Confident expert opinion",
        hook_type="direct_address",
        emotion_curve="tension_release",
        persona="hype_master",
        visual_style="cinematic_dark",
        metadata_tone="authority",
        target_duration=35
    ),
    
    "thriller_hook": Playbook(
        id="thriller_hook",
        name="Thriller Hook",
        description="Dark, mysterious, can't look away",
        hook_type="visual_contradiction",
        emotion_curve="tension_build",
        persona="storyteller",
        visual_style="cinematic_dark",
        metadata_tone="mystery",
        target_duration=40
    )
}


class PlaybookEngine:
    """
    Engine for executing playbooks.
    """
    
    def __init__(self):
        self._playbooks = dict(PLAYBOOKS)
        self._custom_path = Path("config/custom_playbooks.yaml")
        self._load_custom()
    
    def _load_custom(self):
        """Load custom playbooks from file."""
        if self._custom_path.exists():
            with open(self._custom_path, "r") as f:
                data = yaml.safe_load(f) or {}
                for pb_id, pb_data in data.items():
                    self._playbooks[pb_id] = Playbook(**pb_data)
    
    def get(self, playbook_id: str) -> Optional[Playbook]:
        """Get playbook by ID."""
        return self._playbooks.get(playbook_id)
    
    def list_all(self) -> List[str]:
        """List all playbook IDs."""
        return list(self._playbooks.keys())
    
    def create_custom(self, playbook: Playbook):
        """Create a custom playbook."""
        self._playbooks[playbook.id] = playbook
        self._save_custom()
    
    def _save_custom(self):
        """Save custom playbooks."""
        custom = {k: asdict(v) for k, v in self._playbooks.items() if k not in PLAYBOOKS}
        self._custom_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._custom_path, "w") as f:
            yaml.dump(custom, f)
    
    def to_job_config(self, playbook_id: str) -> Dict:
        """Convert playbook to job config."""
        pb = self.get(playbook_id)
        if not pb:
            return {}
        
        return {
            "hook_type": pb.hook_type,
            "emotion_curve": pb.emotion_curve,
            "persona": pb.persona,
            "visual_style": pb.visual_style,
            "duration": pb.target_duration,
            "min_score": pb.min_score
        }
    
    def display_all(self):
        """Display all playbooks."""
        print("\n" + "=" * 60)
        print("  YOUR PLAYBOOKS")
        print("=" * 60)
        for pb_id, pb in self._playbooks.items():
            print(f"\n  📘 {pb.name} ({pb_id})")
            print(f"     {pb.description}")
            print(f"     Hook: {pb.hook_type} | Persona: {pb.persona}")

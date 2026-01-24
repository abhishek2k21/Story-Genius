"""
A/B Hook Testing Engine
Enables testing multiple hook variants on the same content body.
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.core.models import Job, Story, Scene
from app.strategy.hook_engine import HookEngine, Hook, HookResult

logger = get_logger(__name__)


@dataclass
class ExperimentVariant:
    """A single variant in an A/B experiment."""
    variant_id: str
    experiment_id: str
    hook: Hook
    job_id: str = ""
    score: float = 0.0
    
    # Real metrics (populated later)
    views: int = 0
    avg_watch_time: float = 0.0
    replays: int = 0
    retention_rate: float = 0.0
    
    @property
    def is_winner(self) -> bool:
        """Check if this variant has best metrics."""
        return self.retention_rate > 0.5


@dataclass
class ABExperiment:
    """An A/B hook testing experiment."""
    id: str
    name: str
    topic: str
    created_at: datetime
    
    # Variants
    variants: List[ExperimentVariant] = field(default_factory=list)
    
    # Status
    status: str = "pending"  # pending, running, completed, analyzed
    winner_variant_id: str = ""
    
    def get_winner(self) -> Optional[ExperimentVariant]:
        """Get winning variant based on retention."""
        if not self.variants:
            return None
        
        # Sort by retention rate, then score
        sorted_variants = sorted(
            self.variants,
            key=lambda v: (v.retention_rate, v.score),
            reverse=True
        )
        return sorted_variants[0]


class ABTestingEngine:
    """
    A/B testing engine for hook variants.
    Generates multiple variants of the same content with different hooks.
    """
    
    def __init__(self):
        self.hook_engine = HookEngine()
        self._experiments: Dict[str, ABExperiment] = {}
    
    def create_experiment(
        self,
        topic: str,
        num_variants: int = 3,
        name: str = None
    ) -> ABExperiment:
        """
        Create a new A/B experiment with hook variants.
        
        Args:
            topic: Content topic
            num_variants: Number of hook variants to test
            name: Optional experiment name
            
        Returns:
            ABExperiment with variants
        """
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        experiment = ABExperiment(
            id=experiment_id,
            name=name or f"Hook Test: {topic[:30]}",
            topic=topic,
            created_at=datetime.utcnow(),
            status="pending"
        )
        
        logger.info(f"Creating experiment {experiment_id} with {num_variants} variants")
        
        # Generate hook variants
        hooks = self.hook_engine.generate_hooks(
            topic=topic,
            audience="general",
            count=num_variants
        )
        
        # Score hooks
        scored_hooks = self.hook_engine.score_all_hooks(hooks)
        
        # Create variants
        for i, hook in enumerate(scored_hooks[:num_variants]):
            variant = ExperimentVariant(
                variant_id=f"var_{chr(65+i)}",  # var_A, var_B, var_C
                experiment_id=experiment_id,
                hook=hook,
                score=hook.total_score
            )
            experiment.variants.append(variant)
        
        self._experiments[experiment_id] = experiment
        logger.info(f"Created {len(experiment.variants)} variants for experiment")
        
        return experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[ABExperiment]:
        """Get experiment by ID."""
        return self._experiments.get(experiment_id)
    
    def list_experiments(self) -> List[str]:
        """List all experiment IDs."""
        return list(self._experiments.keys())
    
    def generate_variant_stories(
        self,
        experiment: ABExperiment,
        base_story: Story
    ) -> List[Story]:
        """
        Generate story variants with different hooks.
        
        Args:
            experiment: The A/B experiment
            base_story: Base story to use for body
            
        Returns:
            List of Story variants, one per hook
        """
        stories = []
        
        for variant in experiment.variants:
            # Clone story with new ID
            variant_story = Story(
                id=f"{base_story.id}_{variant.variant_id}",
                job_id=base_story.job_id,
                total_duration=base_story.total_duration,
                scenes=list(base_story.scenes)  # Copy scenes
            )
            
            # Replace hook scene (Scene 1)
            if variant_story.scenes:
                from app.core.models import ScenePurpose
                hook_scene = Scene(
                    id=1,
                    start_sec=0,
                    end_sec=2,
                    purpose=ScenePurpose.HOOK,
                    narration_text=variant.hook.text,
                    visual_prompt=variant.hook.visual_prompt
                )
                variant_story.scenes[0] = hook_scene
            
            stories.append(variant_story)
            logger.debug(f"Created variant story: {variant.variant_id}")
        
        experiment.status = "running"
        return stories
    
    def record_metrics(
        self,
        experiment_id: str,
        variant_id: str,
        metrics: Dict
    ) -> bool:
        """
        Record real-world metrics for a variant.
        
        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID (var_A, var_B, etc.)
            metrics: Dict with views, avg_watch_time, replays
            
        Returns:
            Success status
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.error(f"Experiment not found: {experiment_id}")
            return False
        
        for variant in experiment.variants:
            if variant.variant_id == variant_id:
                variant.views = metrics.get("views", 0)
                variant.avg_watch_time = metrics.get("avg_watch_time", 0)
                variant.replays = metrics.get("replays", 0)
                
                # Calculate retention rate
                if variant.views > 0 and variant.avg_watch_time > 0:
                    # Assume 30s video
                    variant.retention_rate = min(1.0, variant.avg_watch_time / 30.0)
                
                logger.info(f"Recorded metrics for {experiment_id}/{variant_id}")
                return True
        
        return False
    
    def analyze_experiment(self, experiment_id: str) -> Dict:
        """
        Analyze experiment results and determine winner.
        
        Args:
            experiment_id: Experiment to analyze
            
        Returns:
            Analysis results
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        
        winner = experiment.get_winner()
        experiment.status = "analyzed"
        
        if winner:
            experiment.winner_variant_id = winner.variant_id
        
        return {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "winner": {
                "variant_id": winner.variant_id if winner else None,
                "hook_text": winner.hook.text if winner else None,
                "hook_type": winner.hook.hook_type.value if winner else None,
                "retention_rate": winner.retention_rate if winner else 0
            },
            "variants": [
                {
                    "id": v.variant_id,
                    "hook_type": v.hook.hook_type.value,
                    "score": v.score,
                    "views": v.views,
                    "retention_rate": v.retention_rate
                }
                for v in experiment.variants
            ]
        }
    
    def get_experiment_summary(self, experiment_id: str) -> str:
        """Get human-readable experiment summary."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return "Experiment not found"
        
        lines = [
            f"Experiment: {experiment.name}",
            f"Status: {experiment.status}",
            f"Variants: {len(experiment.variants)}",
            ""
        ]
        
        for v in experiment.variants:
            lines.append(f"  {v.variant_id}: [{v.hook.hook_type.value}] {v.hook.text[:40]}...")
            lines.append(f"    Score: {v.score:.2f} | Retention: {v.retention_rate:.2f}")
        
        if experiment.winner_variant_id:
            lines.append(f"\n🏆 Winner: {experiment.winner_variant_id}")
        
        return "\n".join(lines)

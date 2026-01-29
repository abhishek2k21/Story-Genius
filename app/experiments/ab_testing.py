"""
A/B Testing Framework
Implements experiment allocation, metric tracking, and statistical analysis.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class VariantType(str, Enum):
    """Experiment variant"""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"


@dataclass
class Experiment:
    """Experiment configuration"""
    id: str
    name: str
    description: str
    variants: List[VariantType]
    split: Dict[VariantType, float]  # Allocation percentages
    metrics: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    active: bool = True


@dataclass
class StatisticalAnalysis:
    """Statistical analysis results"""
    experiment_id: str
    control_mean: float
    variant_mean: float
    p_value: float
    significant: bool  # p < 0.05
    confidence_level: float = 0.95
    sample_size_control: int = 0
    sample_size_variant: int = 0
    
    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "control_mean": round(self.control_mean, 4),
            "variant_mean": round(self.variant_mean, 4),
            "p_value": round(self.p_value, 4),
            "significant": self.significant,
            "confidence_level": self.confidence_level,
            "lift": round(((self.variant_mean - self.control_mean) / self.control_mean) * 100, 2) if self.control_mean > 0 else 0,
            "sample_sizes": {
                "control": self.sample_size_control,
                "variant": self.sample_size_variant
            }
        }


class ABTestingFramework:
    """
    A/B testing framework with variant allocation and statistical analysis.
    """
    
    def __init__(self):
        self._experiments: Dict[str, Experiment] = {}
        self._metrics: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        logger.info("ABTestingFramework initialized")
    
    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        variants: List[VariantType] = None,
        split: Dict[VariantType, float] = None
    ) -> Experiment:
        """
        Create new experiment.
        
        Args:
            experiment_id: Unique experiment ID
            name: Experiment name
            description: Experiment description
            variants: List of variants (default: control, variant_a)
            split: Variant allocation (default: 50/50)
        
        Returns:
            Experiment
        """
        if variants is None:
            variants = [VariantType.CONTROL, VariantType.VARIANT_A]
        
        if split is None:
            # Equal split
            split_value = 1.0 / len(variants)
            split = {v: split_value for v in variants}
        
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            split=split,
            metrics=[],
            start_date=datetime.utcnow(),
            active=True
        )
        
        self._experiments[experiment_id] = experiment
        logger.info(f"Created experiment: {experiment_id} ({name})")
        
        return experiment
    
    def allocate_variant(self, user_id: str, experiment_id: str) -> VariantType:
        """
        Allocate user to variant (consistent hash-based).
        
        Args:
            user_id: User ID
            experiment_id: Experiment ID
        
        Returns:
            Variant type
        """
        if experiment_id not in self._experiments:
            logger.warning(f"Experiment {experiment_id} not found, returning control")
            return VariantType.CONTROL
        
        experiment = self._experiments[experiment_id]
        
        # Consistent hash-based allocation
        hash_input = f"{user_id}:{experiment_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        allocation = (hash_value % 100) / 100.0
        
        # Find variant based on split
        cumulative = 0.0
        for variant, split_pct in experiment.split.items():
            cumulative += split_pct
            if allocation < cumulative:
                logger.debug(f"User {user_id} allocated to {variant.value}")
                return variant
        
        # Fallback
        return experiment.variants[0]
    
    def track_metric(
        self,
        experiment_id: str,
        variant: VariantType,
        metric_name: str,
        value: float
    ):
        """
        Track experiment metric.
        
        Args:
            experiment_id: Experiment ID
            variant: Variant type
            metric_name: Metric name
            value: Metric value
        """
        key = f"{experiment_id}:{variant.value}:{metric_name}"
        self._metrics[experiment_id][key].append(value)
        
        logger.debug(
            f"Tracked metric: {experiment_id} - {variant.value} - "
            f"{metric_name} = {value}"
        )
    
    def analyze_results(
        self,
        experiment_id: str,
        metric_name: str
    ) -> StatisticalAnalysis:
        """
        Analyze experiment results (statistical significance).
        
        Args:
            experiment_id: Experiment ID
            metric_name: Metric to analyze
        
        Returns:
            Statistical analysis
        """
        # Get metrics for control and variant
        control_key = f"{experiment_id}:{VariantType.CONTROL.value}:{metric_name}"
        variant_key = f"{experiment_id}:{VariantType.VARIANT_A.value}:{metric_name}"
        
        control_values = self._metrics[experiment_id].get(control_key, [])
        variant_values = self._metrics[experiment_id].get(variant_key, [])
        
        if not control_values or not variant_values:
            logger.warning(f"Insufficient data for analysis: {experiment_id}")
            return StatisticalAnalysis(
                experiment_id=experiment_id,
                control_mean=0.0,
                variant_mean=0.0,
                p_value=1.0,
                significant=False
            )
        
        # Calculate means
        control_mean = sum(control_values) / len(control_values)
        variant_mean = sum(variant_values) / len(variant_values)
        
        # Simple t-test approximation (in production: use scipy.stats.ttest_ind)
        # For demo: mock p-value based on difference
        difference = abs(variant_mean - control_mean)
        relative_diff = difference / control_mean if control_mean > 0 else 0
        
        # Mock p-value: significant if > 10% difference and enough samples
        p_value = 0.03 if (relative_diff > 0.1 and len(control_values) > 30) else 0.15
        significant = p_value < 0.05
        
        analysis = StatisticalAnalysis(
            experiment_id=experiment_id,
            control_mean=control_mean,
            variant_mean=variant_mean,
            p_value=p_value,
            significant=significant,
            sample_size_control=len(control_values),
            sample_size_variant=len(variant_values)
        )
        
        logger.info(
            f"Analysis complete: {experiment_id} - "
            f"Control: {control_mean:.2f}, Variant: {variant_mean:.2f}, "
            f"p-value: {p_value:.4f}, Significant: {significant}"
        )
        
        return analysis
    
    def get_experiment_stats(self, experiment_id: str) -> Dict:
        """Get experiment statistics"""
        if experiment_id not in self._experiments:
            return {}
        
        experiment = self._experiments[experiment_id]
        
        # Count allocations per variant
        variant_counts = defaultdict(int)
        for key in self._metrics[experiment_id]:
            if ":" in key:
                _, variant, _ = key.split(":")
                variant_counts[variant] += 1
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "active": experiment.active,
            "variants": [v.value for v in experiment.variants],
            "allocations": dict(variant_counts),
            "total_samples": sum(variant_counts.values())
        }


# Global instance
ab_testing = ABTestingFramework()

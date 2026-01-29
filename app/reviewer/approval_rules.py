"""
Automated Approval Rules
Implements rule-based approval workflow for content quality.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.engines.quality_framework import QualityScore, quality_framework
from app.core.logging import get_logger

logger = get_logger(__name__)


class ApprovalDecision(str, Enum):
    """Approval decision enumeration"""
    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    REGENERATE = "regenerate"


@dataclass
class ApprovalResult:
    """Approval evaluation result"""
    decision: ApprovalDecision
    quality_score: float
    reason: str
    criteria_failed: List[str]
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "quality_score": round(self.quality_score, 2),
            "reason": self.reason,
            "criteria_failed": self.criteria_failed,
            "timestamp": self.timestamp
        }


class ApprovalRules:
    """
    Rule-based approval engine.
    
    Approval Tiers:
    - Auto-Approve: Quality ≥ 85
    - Manual Review: Quality 70-84
    - Regenerate: Quality < 70
    """
    
    def __init__(
        self,
        auto_approve_threshold: float = 85.0,
        manual_review_threshold: float = 70.0
    ):
        self.auto_approve_threshold = auto_approve_threshold
        self.manual_review_threshold = manual_review_threshold
        
        # Statistics
        self._approval_stats = {
            ApprovalDecision.AUTO_APPROVE: 0,
            ApprovalDecision.MANUAL_REVIEW: 0,
            ApprovalDecision.REGENERATE: 0
        }
        
        logger.info(
            f"ApprovalRules initialized: "
            f"auto_approve≥{auto_approve_threshold}, "
            f"manual_review≥{manual_review_threshold}"
        )
    
    def evaluate(
        self,
        content: Dict[str, Any],
        quality_score: Optional[QualityScore] = None
    ) -> ApprovalResult:
        """
        Evaluate content and make approval decision.
        
        Args:
            content: Content to evaluate
            quality_score: Pre-calculated quality score (optional)
        
        Returns:
            ApprovalResult with decision and reasoning
        """
        # Calculate quality score if not provided
        if quality_score is None:
            quality_score = quality_framework.score_content(content)
        
        score = quality_score.overall_score
        
        # Identify failed criteria (score < 70)
        criteria_failed = [
            name for name, criterion in quality_score.criteria_scores.items()
            if criterion.score < 70
        ]
        
        # Make decision
        if score >= self.auto_approve_threshold:
            decision = ApprovalDecision.AUTO_APPROVE
            reason = f"Quality score {score:.1f} meets auto-approve threshold (≥{self.auto_approve_threshold})"
            
        elif score >= self.manual_review_threshold:
            decision = ApprovalDecision.MANUAL_REVIEW
            reason = (
                f"Quality score {score:.1f} requires manual review "
                f"({self.manual_review_threshold}-{self.auto_approve_threshold})"
            )
            
        else:
            decision = ApprovalDecision.REGENERATE
            reason = (
                f"Quality score {score:.1f} below threshold (< {self.manual_review_threshold}), "
                f"regeneration recommended"
            )
        
        # Update statistics
        self._approval_stats[decision] += 1
        
        result = ApprovalResult(
            decision=decision,
            quality_score=score,
            reason=reason,
            criteria_failed=criteria_failed,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Approval decision: {decision.value} (score={score:.1f})"
        )
        
        return result
    
    def get_approval_stats(self) -> Dict:
        """Get approval statistics"""
        total = sum(self._approval_stats.values())
        
        if total == 0:
            return {
                "total_evaluations": 0,
                "auto_approve_rate": 0.0,
                "manual_review_rate": 0.0,
                "regenerate_rate": 0.0
            }
        
        return {
            "total_evaluations": total,
            "auto_approve_rate": (self._approval_stats[ApprovalDecision.AUTO_APPROVE] / total) * 100,
            "manual_review_rate": (self._approval_stats[ApprovalDecision.MANUAL_REVIEW] / total) * 100,
            "regenerate_rate": (self._approval_stats[ApprovalDecision.REGENERATE] / total) * 100,
            "counts": {
                decision.value: count
                for decision, count in self._approval_stats.items()
            }
        }
    
    def adjust_thresholds(
        self,
        auto_approve_threshold: Optional[float] = None,
        manual_review_threshold: Optional[float] = None
    ):
        """
        Adjust approval thresholds (for A/B testing).
        
        Args:
            auto_approve_threshold: New auto-approve threshold
            manual_review_threshold: New manual review threshold
        """
        if auto_approve_threshold is not None:
            self.auto_approve_threshold = auto_approve_threshold
            logger.info(f"Auto-approve threshold adjusted to {auto_approve_threshold}")
        
        if manual_review_threshold is not None:
            self.manual_review_threshold = manual_review_threshold
            logger.info(f"Manual review threshold adjusted to {manual_review_threshold}")


# Global instance
approval_rules = ApprovalRules()

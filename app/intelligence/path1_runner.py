"""
Path 1 Integrated Runner - Week 14
Makes thinking invisible and trustworthy with Silent Mode, Red Flags, and Trust Thresholds.
"""
import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from app.intelligence.assumptions import get_assumption_extractor, AssumptionAnalysis
from app.intelligence.counter import get_counter_engine, CounterAnalysis
from app.intelligence.second_order import get_second_order_checker, SecondOrderAnalysis
from app.intelligence.depth_scorer import get_depth_scorer, DepthScore
from app.intelligence.synthesis import get_synthesis_engine, SynthesisResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class Path1Mode(str, Enum):
    """Path 1 execution modes."""
    SILENT = "silent"      # Only show results, not process
    VERBOSE = "verbose"    # Show full analysis
    FAST = "fast"          # Skip counter-arguments on low-risk ideas


class IdeaStatus(str, Enum):
    """Idea safety status."""
    APPROVED = "approved"     # Safe to proceed
    REVIEW = "review"         # Needs manual review
    DANGER = "danger"         # Should not ship
    REJECTED = "rejected"     # Auto-rejected


@dataclass
class RedFlag:
    """A red flag warning about an idea."""
    flag_type: str
    severity: float  # 0.0-1.0
    reason: str


@dataclass
class Path1Result:
    """Complete Path 1 analysis result."""
    idea: str
    status: IdeaStatus
    depth_score: float
    refined_idea: str
    red_flags: List[RedFlag] = field(default_factory=list)
    
    # Full analysis (only populated in verbose mode)
    assumptions: Optional[AssumptionAnalysis] = None
    counters: Optional[CounterAnalysis] = None
    second_order: Optional[SecondOrderAnalysis] = None
    depth_details: Optional[DepthScore] = None
    synthesis: Optional[SynthesisResult] = None
    
    # Timing
    processing_time_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "idea": self.idea,
            "status": self.status.value,
            "depth_score": self.depth_score,
            "refined_idea": self.refined_idea,
            "red_flags": [{"type": rf.flag_type, "severity": rf.severity, "reason": rf.reason} for rf in self.red_flags],
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class TrustThresholds:
    """Personal trust thresholds for idea filtering."""
    auto_accept: float = 0.80    # Ideas above this are auto-approved
    auto_reject: float = 0.35    # Ideas below this are auto-rejected
    fragile_assumption_limit: int = 3  # Max fragile assumptions before danger
    long_term_risk_limit: float = 0.75  # Max risk score before danger
    min_robustness: float = 0.45  # Minimum robustness to avoid clickbait trap


class Path1Runner:
    """
    Integrated Path 1 thinking loop with Silent Mode.
    Runs full analysis in background, only surfaces what matters.
    """
    
    def __init__(
        self,
        mode: Path1Mode = Path1Mode.SILENT,
        thresholds: TrustThresholds = None,
        cache_enabled: bool = True
    ):
        self.mode = mode
        self.thresholds = thresholds or TrustThresholds()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Path1Result] = {}
        
        # Initialize all engines
        self.assumption_extractor = get_assumption_extractor()
        self.counter_engine = get_counter_engine()
        self.second_order_checker = get_second_order_checker()
        self.depth_scorer = get_depth_scorer()
        self.synthesis_engine = get_synthesis_engine()
        
        logger.info(f"Path1Runner initialized in {mode.value} mode")
    
    def _get_cache_key(self, idea: str) -> str:
        """Generate cache key for idea."""
        return hashlib.md5(idea.encode()).hexdigest()
    
    def _detect_red_flags(
        self,
        assumptions: AssumptionAnalysis,
        counters: CounterAnalysis,
        second_order: SecondOrderAnalysis,
        depth: DepthScore
    ) -> List[RedFlag]:
        """Detect red flags that should prevent shipping."""
        flags = []
        
        # Red Flag 1: Too many fragile assumptions
        fragile_count = len(assumptions.fragile_assumptions)
        if fragile_count > self.thresholds.fragile_assumption_limit:
            flags.append(RedFlag(
                flag_type="fragile_assumptions",
                severity=min(1.0, fragile_count / 5),
                reason=f"Too many fragile assumptions ({fragile_count}). Idea rests on shaky ground."
            ))
        
        # Red Flag 2: Severe second-order risks
        if second_order.long_term_risk_score > self.thresholds.long_term_risk_limit:
            flags.append(RedFlag(
                flag_type="long_term_risk",
                severity=second_order.long_term_risk_score,
                reason=f"High long-term risk ({second_order.long_term_risk_score:.0%}). {second_order.audience_conditioning}"
            ))
        
        # Red Flag 3: Clickbait trap (low robustness + high novelty)
        if depth.robustness < self.thresholds.min_robustness and depth.novelty > 0.7:
            flags.append(RedFlag(
                flag_type="clickbait_trap",
                severity=0.8,
                reason="Low robustness with high novelty = clickbait trap. Looks shiny but won't hold up."
            ))
        
        # Red Flag 4: Very low survival likelihood
        if counters.survival_likelihood < 0.3:
            flags.append(RedFlag(
                flag_type="weak_defense",
                severity=0.9,
                reason=f"Idea unlikely to survive scrutiny ({counters.survival_likelihood:.0%} survival). {counters.strongest_counter}"
            ))
        
        # Red Flag 5: Negative effects outweigh positive
        if len(second_order.negative_effects) > len(second_order.positive_effects) * 2:
            flags.append(RedFlag(
                flag_type="net_negative",
                severity=0.7,
                reason="Negative downstream effects significantly outweigh positives."
            ))
        
        return flags
    
    def _determine_status(self, depth_score: float, red_flags: List[RedFlag]) -> IdeaStatus:
        """Determine idea status based on score and red flags."""
        # Check for danger flags first
        severe_flags = [rf for rf in red_flags if rf.severity >= 0.8]
        if severe_flags:
            return IdeaStatus.DANGER
        
        # Check thresholds
        if depth_score >= self.thresholds.auto_accept and not red_flags:
            return IdeaStatus.APPROVED
        elif depth_score < self.thresholds.auto_reject:
            return IdeaStatus.REJECTED
        elif red_flags:
            return IdeaStatus.REVIEW
        else:
            return IdeaStatus.REVIEW
    
    def analyze(self, idea: str, skip_cache: bool = False) -> Path1Result:
        """
        Run full Path 1 analysis on an idea.
        
        Args:
            idea: The raw idea to analyze
            skip_cache: Force fresh analysis
            
        Returns:
            Path1Result with status, score, refined idea, and any red flags
        """
        start_time = time.time()
        cache_key = self._get_cache_key(idea)
        
        # Check cache
        if self.cache_enabled and not skip_cache and cache_key in self._cache:
            logger.debug(f"Cache hit for idea: {idea[:30]}...")
            return self._cache[cache_key]
        
        if self.mode != Path1Mode.SILENT:
            logger.info(f"Analyzing: {idea[:50]}...")
        
        # Step 1: Extract assumptions
        assumptions = self.assumption_extractor.extract_assumptions(idea)
        
        # Step 2: Generate counter-arguments (skip in FAST mode for high-scoring ideas)
        counters = self.counter_engine.generate_counter_arguments(idea)
        
        # Step 3: Analyze second-order effects
        second_order = self.second_order_checker.analyze_second_order_effects(idea)
        
        # Step 4: Score depth
        depth = self.depth_scorer.score_idea_depth(idea)
        
        # Step 5: Detect red flags
        red_flags = self._detect_red_flags(assumptions, counters, second_order, depth)
        
        # Step 6: Synthesize refined idea
        synthesis = self.synthesis_engine.synthesize_stronger_idea(
            original=idea,
            assumptions=assumptions.assumptions,
            counters=counters.counter_arguments,
            second_order=second_order.second_order_effects
        )
        
        # Determine status
        status = self._determine_status(depth.overall_score, red_flags)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Build result
        result = Path1Result(
            idea=idea,
            status=status,
            depth_score=depth.overall_score,
            refined_idea=synthesis.refined_idea,
            red_flags=red_flags,
            processing_time_ms=processing_time
        )
        
        # Add full analysis in verbose mode
        if self.mode == Path1Mode.VERBOSE:
            result.assumptions = assumptions
            result.counters = counters
            result.second_order = second_order
            result.depth_details = depth
            result.synthesis = synthesis
        
        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result
        
        return result
    
    def analyze_batch(
        self,
        ideas: List[str],
        top_n: int = 2
    ) -> Tuple[List[Path1Result], List[Path1Result]]:
        """
        Analyze multiple ideas and return top N plus any dangerous ones.
        
        Args:
            ideas: List of raw ideas
            top_n: Number of top ideas to surface
            
        Returns:
            Tuple of (top_ideas, flagged_ideas)
        """
        results = [self.analyze(idea) for idea in ideas]
        
        # Separate by status
        approved = [r for r in results if r.status in [IdeaStatus.APPROVED, IdeaStatus.REVIEW]]
        flagged = [r for r in results if r.status in [IdeaStatus.DANGER, IdeaStatus.REJECTED]]
        
        # Sort approved by depth score
        approved.sort(key=lambda r: r.depth_score, reverse=True)
        
        return approved[:top_n], flagged
    
    def silent_filter(self, ideas: List[str]) -> Dict:
        """
        Silent mode batch processing - only surfaces what matters.
        
        Args:
            ideas: List of raw ideas
            
        Returns:
            Dict with top ideas and warnings only
        """
        top_ideas, flagged = self.analyze_batch(ideas)
        
        output = {
            "mode": "silent",
            "top_ideas": [
                {
                    "original": r.idea,
                    "refined": r.refined_idea,
                    "score": r.depth_score,
                    "status": r.status.value
                }
                for r in top_ideas
            ],
            "warning_count": len(flagged),
            "warnings": [
                {
                    "idea": r.idea[:50] + "...",
                    "status": r.status.value,
                    "flags": [rf.reason for rf in r.red_flags[:2]]
                }
                for r in flagged
            ] if flagged else []
        }
        
        return output
    
    def calibrate_weights(
        self,
        ideas_with_ratings: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """
        Calibrate depth scorer weights based on user intuition.
        
        Args:
            ideas_with_ratings: List of (idea, user_rating) tuples
            
        Returns:
            Suggested weight adjustments
        """
        discrepancies = []
        
        for idea, user_rating in ideas_with_ratings:
            result = self.analyze(idea)
            diff = user_rating - result.depth_score
            discrepancies.append({
                "idea": idea,
                "user_rating": user_rating,
                "system_score": result.depth_score,
                "difference": diff
            })
        
        # Analyze patterns
        avg_diff = sum(d["difference"] for d in discrepancies) / len(discrepancies)
        
        return {
            "average_difference": avg_diff,
            "suggested_adjustment": "increase_depth_weight" if avg_diff > 0.1 else "decrease_depth_weight" if avg_diff < -0.1 else "no_change",
            "discrepancies": discrepancies
        }
    
    def get_stats(self) -> Dict:
        """Get runner statistics."""
        return {
            "mode": self.mode.value,
            "cache_size": len(self._cache),
            "thresholds": {
                "auto_accept": self.thresholds.auto_accept,
                "auto_reject": self.thresholds.auto_reject,
                "fragile_limit": self.thresholds.fragile_assumption_limit,
                "risk_limit": self.thresholds.long_term_risk_limit
            }
        }


# Singleton instance
_runner = None

def get_path1_runner(mode: Path1Mode = Path1Mode.SILENT) -> Path1Runner:
    """Get global Path 1 runner instance."""
    global _runner
    if _runner is None:
        _runner = Path1Runner(mode=mode)
    return _runner


def analyze_idea(idea: str, mode: str = "silent") -> Dict:
    """
    Quick function to analyze an idea through Path 1.
    
    Args:
        idea: The idea to analyze
        mode: "silent", "verbose", or "fast"
        
    Returns:
        Analysis result as dict
    """
    runner = get_path1_runner(Path1Mode(mode))
    result = runner.analyze(idea)
    return result.to_dict()


def filter_ideas(ideas: List[str]) -> Dict:
    """
    Filter multiple ideas, returning only the best.
    
    Args:
        ideas: List of raw ideas
        
    Returns:
        Dict with top ideas and any warnings
    """
    runner = get_path1_runner(Path1Mode.SILENT)
    return runner.silent_filter(ideas)

"""
Week 16 - Baseline Path 1 Runner
Path 1 that uses simple baseline to stop over-protecting adult content.
"""
from typing import List, Optional
from dataclasses import dataclass

from app.core.baseline import (
    SimpleConfig, AudienceBaseline, Tone,
    BaselineThresholds, KILL_OVER_EXPLANATION_RULES
)
from app.intelligence.path1_runner import (
    Path1Runner, Path1Mode, Path1Result, TrustThresholds,
    IdeaStatus, RedFlag
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaselinePath1(Path1Runner):
    """
    Path 1 that respects audience baseline.
    Stops over-protecting adult content.
    """
    
    def __init__(self, config: SimpleConfig, mode: Path1Mode = Path1Mode.SILENT):
        # Get thresholds for baseline
        baseline_thresholds = BaselineThresholds.for_baseline(config.audience_baseline)
        
        thresholds = TrustThresholds(
            auto_accept=baseline_thresholds.auto_accept,
            auto_reject=baseline_thresholds.auto_reject,
            fragile_assumption_limit=6 if baseline_thresholds.allow_assumptions else 2,
            long_term_risk_limit=0.90 if baseline_thresholds.allow_controversy else 0.65,
            min_robustness=0.30 if baseline_thresholds.allow_ambiguity else 0.50
        )
        
        super().__init__(mode=mode, thresholds=thresholds)
        
        self.config = config
        self.baseline_thresholds = baseline_thresholds
        
        logger.info(f"BaselinePath1 initialized: {config.audience_baseline}, tone={config.tone}")
    
    def _detect_red_flags(
        self,
        assumptions,
        counters,
        second_order,
        depth
    ) -> List[RedFlag]:
        """Override: adult baseline gets much more leeway."""
        flags = []
        
        # For adult baseline: dramatically reduce flagging
        if self.config.is_adult():
            # Only flag truly severe issues
            if len(assumptions.fragile_assumptions) > 8:
                flags.append(RedFlag(
                    flag_type="fragile_assumptions",
                    severity=0.4,
                    reason="Many assumptions, but acceptable for adult content."
                ))
            
            # Only flag extreme risk for adults
            if second_order.long_term_risk_score > 0.95:
                flags.append(RedFlag(
                    flag_type="extreme_risk",
                    severity=0.5,
                    reason="Very high risk - review recommended."
                ))
            
            # Adults don't need survival likelihood checks
            # Adults can handle controversy
            # Adults can handle ambiguity
            
        else:
            # Kids: stricter flags
            if len(assumptions.fragile_assumptions) > 2:
                flags.append(RedFlag(
                    flag_type="fragile_assumptions",
                    severity=min(1.0, len(assumptions.fragile_assumptions) / 4),
                    reason="Kids content needs solid, clear foundations."
                ))
            
            if second_order.long_term_risk_score > 0.65:
                flags.append(RedFlag(
                    flag_type="long_term_risk",
                    severity=second_order.long_term_risk_score,
                    reason="Kids content should avoid risky approaches."
                ))
            
            if counters.survival_likelihood < 0.4:
                flags.append(RedFlag(
                    flag_type="weak_defense",
                    severity=0.7,
                    reason="Kids content ideas should be defensible."
                ))
        
        return flags
    
    def analyze_with_baseline(self, idea: Optional[str] = None) -> Path1Result:
        """
        Analyze idea with baseline context.
        Uses config.topic if idea not provided.
        """
        idea = idea or self.config.topic
        
        logger.info(f"Baseline analysis: {self.config.audience_baseline} | {idea[:40]}...")
        
        result = self.analyze(idea)
        
        # Upgrade DANGER to REVIEW for adult content unless truly severe
        if self.config.is_adult() and result.status == IdeaStatus.DANGER:
            severe = [f for f in result.red_flags if f.severity >= 0.7]
            if not severe:
                result.status = IdeaStatus.REVIEW
                logger.info("Upgraded DANGER → REVIEW for adult baseline")
        
        return result
    
    def get_synthesis_context(self) -> str:
        """Get context for synthesis."""
        return f"""
AUDIENCE BASELINE: {self.config.audience_baseline}
TONE: {self.config.tone}
LANGUAGE: {self.config.language}
CONTENT MODE: {self.config.get_content_mode()}

{self.config.get_generation_rules()}

{KILL_OVER_EXPLANATION_RULES if self.config.is_adult() else ""}
"""


def quick_analyze(
    topic: str,
    baseline: str = "general_adult",
    tone: str = "neutral",
    language: str = "en"
) -> dict:
    """
    Quick analysis with simple baseline.
    Adult by default.
    
    Args:
        topic: The content topic
        baseline: "general_adult" (default), "kids", "expert"
        tone: "neutral", "sharp", "bold", "playful"
        language: Language code
        
    Returns:
        Analysis result dict
    """
    config = SimpleConfig(
        topic=topic,
        audience_baseline=AudienceBaseline(baseline),
        tone=Tone(tone),
        language=language
    )
    
    runner = BaselinePath1(config, mode=Path1Mode.SILENT)
    result = runner.analyze_with_baseline()
    
    return {
        "topic": topic,
        "baseline": baseline,
        "tone": tone,
        "language": language,
        "content_mode": config.get_content_mode(),
        "status": result.status.value,
        "depth_score": result.depth_score,
        "refined_idea": result.refined_idea,
        "red_flags": len(result.red_flags),
        "rules": config.get_generation_rules()
    }

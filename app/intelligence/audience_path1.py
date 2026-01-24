"""
Week 15 - Audience-Aware Path 1 Runner
Path 1 that respects audience, intent, and content mode.
Stops acting like a school teacher for adult content.
"""
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.intelligence.path1_runner import (
    Path1Runner, Path1Mode, Path1Result, TrustThresholds, 
    IdeaStatus, RedFlag
)
from app.core.global_mode import (
    GenerationConfig, AudienceProfile, Intent, ContentMode, 
    Maturity, AdultPersona
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AudienceAwarePath1(Path1Runner):
    """
    Path 1 that adjusts analysis based on audience and intent.
    
    Key changes:
    - Adult content: Allow ambiguity, assumptions, controversy
    - Provoke intent: Don't penalize edgy ideas
    - Cultural context: Allow regional references
    """
    
    def __init__(
        self,
        config: GenerationConfig,
        mode: Path1Mode = Path1Mode.SILENT
    ):
        # Adjust thresholds based on audience
        thresholds = self._build_thresholds(config)
        super().__init__(mode=mode, thresholds=thresholds)
        
        self.config = config
        self._setup_audience_rules()
        
        logger.info(f"AudienceAwarePath1 initialized for {config.audience.maturity} audience, intent={config.intent}")
    
    def _build_thresholds(self, config: GenerationConfig) -> TrustThresholds:
        """Build thresholds appropriate for audience."""
        if config.audience.is_adult():
            # Adults: More lenient thresholds
            return TrustThresholds(
                auto_accept=0.70,      # Lower bar for approval
                auto_reject=0.25,      # Higher tolerance for risk
                fragile_assumption_limit=5,  # Allow more assumptions
                long_term_risk_limit=0.85,   # Higher risk tolerance
                min_robustness=0.35    # Accept edgier content
            )
        elif config.audience.is_kids():
            # Kids: Strict thresholds
            return TrustThresholds(
                auto_accept=0.82,
                auto_reject=0.45,
                fragile_assumption_limit=2,
                long_term_risk_limit=0.60,
                min_robustness=0.55
            )
        else:
            # Teens: Balanced
            return TrustThresholds(
                auto_accept=0.75,
                auto_reject=0.35,
                fragile_assumption_limit=4,
                long_term_risk_limit=0.75,
                min_robustness=0.45
            )
    
    def _setup_audience_rules(self):
        """Configure rules based on audience and intent."""
        self.allow_ambiguity = self.config.audience.is_adult()
        self.allow_controversy = self.config.intent == Intent.PROVOKE.value
        self.allow_cultural_refs = self.config.audience.allows_cultural_references()
        self.is_comedy = self.config.content_mode == ContentMode.COMEDY.value
    
    def _detect_red_flags(
        self,
        assumptions,
        counters,
        second_order,
        depth
    ) -> List[RedFlag]:
        """
        Override red flag detection to respect audience.
        Adult content gets more leeway.
        """
        flags = []
        
        # Red Flag 1: Fragile assumptions (but allow more for adults)
        fragile_count = len(assumptions.fragile_assumptions)
        if fragile_count > self.thresholds.fragile_assumption_limit:
            # For adults with provoke intent, be even more lenient
            if self.allow_controversy:
                # Only flag if really excessive
                if fragile_count > self.thresholds.fragile_assumption_limit + 2:
                    flags.append(RedFlag(
                        flag_type="fragile_assumptions",
                        severity=min(0.6, fragile_count / 8),  # Lower severity
                        reason=f"Many assumptions ({fragile_count}), but acceptable for provocative content."
                    ))
            elif self.allow_ambiguity:
                # Adults: reduced severity
                flags.append(RedFlag(
                    flag_type="fragile_assumptions",
                    severity=min(0.5, fragile_count / 7),
                    reason=f"Some fragile assumptions ({fragile_count}), acceptable for adult content."
                ))
            else:
                # Kids: strict
                flags.append(RedFlag(
                    flag_type="fragile_assumptions",
                    severity=min(1.0, fragile_count / 4),
                    reason=f"Too many fragile assumptions ({fragile_count}). Kids content needs solid ground."
                ))
        
        # Red Flag 2: Long-term risk (but comedy can be risky)
        if second_order.long_term_risk_score > self.thresholds.long_term_risk_limit:
            if self.is_comedy:
                # Comedy is inherently edgy - don't over-penalize
                if second_order.long_term_risk_score > 0.9:
                    flags.append(RedFlag(
                        flag_type="long_term_risk",
                        severity=0.5,  # Reduced
                        reason=f"High risk for comedy ({second_order.long_term_risk_score:.0%}), but comedy pushes limits."
                    ))
            elif self.allow_controversy:
                # Provocative content: risk is the point
                pass  # Don't flag at all
            else:
                flags.append(RedFlag(
                    flag_type="long_term_risk",
                    severity=second_order.long_term_risk_score,
                    reason=f"High long-term risk ({second_order.long_term_risk_score:.0%})."
                ))
        
        # Red Flag 3: Clickbait trap (but not for entertainment)
        if depth.robustness < self.thresholds.min_robustness and depth.novelty > 0.7:
            if self.config.intent == Intent.ENTERTAIN.value:
                # Entertainment can be novel without being robust
                pass
            elif self.allow_ambiguity:
                # Adults: reduced severity
                flags.append(RedFlag(
                    flag_type="clickbait_trap",
                    severity=0.4,
                    reason="Shiny but shallow - but acceptable for adult audience."
                ))
            else:
                flags.append(RedFlag(
                    flag_type="clickbait_trap",
                    severity=0.8,
                    reason="Clickbait trap: high novelty, low substance."
                ))
        
        # Red Flag 4: Survival likelihood
        if counters.survival_likelihood < 0.3:
            if self.allow_controversy:
                # Provocative ideas don't need to "survive" - they're meant to challenge
                pass
            else:
                flags.append(RedFlag(
                    flag_type="weak_defense",
                    severity=0.7 if self.allow_ambiguity else 0.9,
                    reason=f"Idea may not survive scrutiny ({counters.survival_likelihood:.0%} survival)."
                ))
        
        return flags
    
    def get_synthesis_context(self) -> str:
        """Get context for synthesis based on audience."""
        context = [
            f"TARGET AUDIENCE: {self.config.audience.age_group}, {self.config.audience.maturity} maturity",
            f"INTENT: {self.config.intent}",
            f"CONTENT MODE: {self.config.content_mode}",
            f"LANGUAGE: {self.config.audience.language}",
        ]
        
        if self.config.persona:
            context.append(f"PERSONA: {self.config.persona}")
        
        if self.allow_ambiguity:
            context.append("RULE: Ambiguity and assumptions are ALLOWED for this adult audience.")
        
        if self.allow_controversy:
            context.append("RULE: Controversy is ALLOWED - this is provocative content.")
        
        if self.allow_cultural_refs:
            context.append(f"RULE: Cultural references for {self.config.audience.region} are ENCOURAGED.")
        
        return "\n".join(context)
    
    def analyze_with_context(self, idea: str) -> Path1Result:
        """
        Analyze idea with full audience context.
        
        Args:
            idea: The idea to analyze
            
        Returns:
            Path1Result adjusted for audience
        """
        logger.info(f"Analyzing for {self.config.audience.maturity} audience: {idea[:50]}...")
        
        # Get base result
        result = self.analyze(idea)
        
        # Adjust status based on audience rules
        if self.allow_ambiguity and result.status == IdeaStatus.DANGER:
            # Re-evaluate: adult content shouldn't be rejected as easily
            severe_flags = [f for f in result.red_flags if f.severity >= 0.8]
            if not severe_flags:
                result.status = IdeaStatus.REVIEW
                logger.info(f"Upgraded from DANGER to REVIEW for adult audience")
        
        return result


def create_audience_aware_runner(config: GenerationConfig) -> AudienceAwarePath1:
    """
    Create a Path 1 runner configured for specific audience.
    
    Args:
        config: Complete generation configuration
        
    Returns:
        Configured AudienceAwarePath1 instance
    """
    return AudienceAwarePath1(config)


def analyze_for_audience(
    idea: str,
    audience: AudienceProfile,
    intent: Intent,
    content_mode: ContentMode,
    persona: Optional[AdultPersona] = None
) -> Dict:
    """
    Quick function to analyze an idea for a specific audience.
    
    Args:
        idea: The idea to analyze
        audience: Target audience profile
        intent: Content intent
        content_mode: Content mode
        persona: Adult persona (if applicable)
        
    Returns:
        Analysis result as dict
    """
    config = GenerationConfig(
        audience=audience,
        intent=intent,
        content_mode=content_mode,
        persona=persona,
        topic=idea
    )
    
    runner = AudienceAwarePath1(config, mode=Path1Mode.SILENT)
    result = runner.analyze_with_context(idea)
    
    return {
        "idea": idea,
        "audience": f"{audience.age_group}, {audience.region}, {audience.maturity}",
        "intent": intent,
        "status": result.status.value,
        "depth_score": result.depth_score,
        "refined_idea": result.refined_idea,
        "red_flags": len(result.red_flags),
        "context": runner.get_synthesis_context()
    }

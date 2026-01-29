"""
Content Analysis & Feedback Generation
Analyzes content and generates actionable improvement suggestions.
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field

from app.engines.quality_framework import QualityScore, quality_framework
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Feedback:
    """Feedback for content improvement"""
    area: str
    message: str
    priority: str  # high, medium, low
    impact: str  # Expected improvement impact


@dataclass
class ContentAnalysis:
    """Comprehensive content analysis"""
    strengths: List[str]
    weaknesses: List[str]
    feedback: List[Feedback]
    quality_score: QualityScore
    
    def to_dict(self) -> dict:
        return {
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "feedback": [
                {
                    "area": f.area,
                    "message": f.message,
                    "priority": f.priority,
                    "impact": f.impact
                }
                for f in self.feedback
            ],
            "quality_score": self.quality_score.to_dict()
        }


class ContentAnalyzer:
    """
    Analyzes content and generates improvement feedback.
    """
    
    def __init__(self):
        logger.info("ContentAnalyzer initialized")
    
    def analyze(self, content: Dict[str, Any]) -> ContentAnalysis:
        """
        Analyze content and generate feedback.
        
        Args:
            content: Content to analyze
        
        Returns:
            ContentAnalysis with strengths, weaknesses, feedback
        """
        logger.info("Analyzing content")
        
        # Score content
        quality_score = quality_framework.score_content(content)
        
        # Identify strengths (criteria score ≥ 80)
        strengths = [
            f"{name.replace('_', ' ').title()}: {criterion.details}"
            for name, criterion in quality_score.criteria_scores.items()
            if criterion.score >= 80
        ]
        
        # Identify weaknesses (criteria score < 70)
        weaknesses = [
            f"{name.replace('_', ' ').title()}: {criterion.details}"
            for name, criterion in quality_score.criteria_scores.items()
            if criterion.score < 70
        ]
        
        # Generate feedback
        feedback = self._generate_feedback(content, quality_score)
        
        # Sort by priority
        feedback.sort(key=lambda f: {"high": 0, "medium": 1, "low": 2}[f.priority])
        
        analysis = ContentAnalysis(
            strengths=strengths,
            weaknesses=weaknesses,
            feedback=feedback,
            quality_score=quality_score
        )
        
        logger.info(
            f"Analysis complete: {len(strengths)} strengths, "
            f"{len(weaknesses)} weaknesses, {len(feedback)} suggestions"
        )
        
        return analysis
    
    def _generate_feedback(
        self,
        content: Dict,
        quality_score: QualityScore
    ) -> List[Feedback]:
        """Generate actionable feedback"""
        feedback = []
        
        # Hook feedback
        hook_score = quality_score.criteria_scores["hook_quality"]
        if hook_score.score < 80:
            feedback.append(Feedback(
                area="Hook",
                message="Consider making hook more compelling with a question or surprising fact",
                priority="high",
                impact="Increased viewer retention"
            ))
        
        # Engagement feedback
        engagement_score = quality_score.criteria_scores["engagement"]
        if engagement_score.score < 75:
            feedback.append(Feedback(
                area="Engagement",
                message="Add emotional triggers or numbers to boost engagement",
                priority="high",
                impact="Higher click-through rate"
            ))
        
        # Clarity feedback
        clarity_score = quality_score.criteria_scores["clarity"]
        if clarity_score.score < 80:
            if clarity_score.suggestions:
                feedback.append(Feedback(
                    area="Clarity",
                    message=clarity_score.suggestions[0],
                    priority="medium",
                    impact="Better comprehension"
                ))
        
        # Pacing feedback
        pacing_score = quality_score.criteria_scores["pacing"]
        if pacing_score.score < 75:
            feedback.append(Feedback(
                area="Pacing",
                message="Adjust content pacing to match genre expectations",
                priority="medium",
                impact="Improved viewer retention"
            ))
        
        # Grammar feedback
        grammar_score = quality_score.criteria_scores["grammar"]
        if grammar_score.score < 80:
            feedback.append(Feedback(
                area="Grammar",
                message="Review and correct grammar issues",
                priority="low",
                impact="Professional appearance"
            ))
        
        # Originality feedback
        originality_score = quality_score.criteria_scores["originality"]
        if originality_score.score < 70:
            feedback.append(Feedback(
                area="Originality",
                message="Content may be too similar to existing material, add unique angle",
                priority="high",
                impact="Stand out from competition"
            ))
        
        return feedback


# Global instance
content_analyzer = ContentAnalyzer()

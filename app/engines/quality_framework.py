"""
Multi-Criteria Quality Framework
Implements comprehensive content quality scoring across 10+ criteria.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class QualityGrade(str, Enum):
    """Quality grade enumeration"""
    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"            # 60-79
    FAIR = "fair"            # 40-59
    POOR = "poor"            # 0-39


@dataclass
class CriterionScore:
    """Score for a single quality criterion"""
    name: str
    score: float  # 0-100
    weight: float  # 0-1
    details: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Comprehensive quality score"""
    overall_score: float  # 0-100
    grade: QualityGrade
    criteria_scores: Dict[str, CriterionScore]
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade.value,
            "criteria": {
                name: {
                    "score": round(score.score, 2),
                    "weight": score.weight,
                    "details": score.details,
                    "suggestions": score.suggestions
                }
                for name, score in self.criteria_scores.items()
            },
            "timestamp": self.timestamp
        }


class QualityFramework:
    """
    Multi-criteria quality framework for content evaluation.
    """
    
    def __init__(self):
        # Criterion weights (must sum to 1.0)
        self.weights = {
            "clarity": 0.12,
            "engagement": 0.15,
            "hook_quality": 0.12,
            "tone_consistency": 0.10,
            "pacing": 0.10,
            "grammar": 0.08,
            "originality": 0.10,
            "emotional_impact": 0.10,
            "brand_alignment": 0.08,
            "technical_quality": 0.05
        }
        
        logger.info("QualityFramework initialized with 10 criteria")
    
    def score_content(self, content: Dict[str, Any]) -> QualityScore:
        """
        Score content across all criteria.
        
        Args:
            content: Content to score (hook, script, metadata, etc.)
        
        Returns:
            QualityScore with overall and per-criterion scores
        """
        from datetime import datetime
        
        logger.info("Scoring content quality")
        
        # Score each criterion
        criteria_scores = {
            "clarity": self._score_clarity(content),
            "engagement": self._score_engagement(content),
            "hook_quality": self._score_hook_quality(content),
            "tone_consistency": self._score_tone_consistency(content),
            "pacing": self._score_pacing(content),
            "grammar": self._score_grammar(content),
            "originality": self._score_originality(content),
            "emotional_impact": self._score_emotional_impact(content),
            "brand_alignment": self._score_brand_alignment(content),
            "technical_quality": self._score_technical_quality(content)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            score.score * score.weight
            for score in criteria_scores.values()
        )
        
        # Determine grade
        grade = self._get_grade(overall_score)
        
        quality_score = QualityScore(
            overall_score=overall_score,
            grade=grade,
            criteria_scores=criteria_scores,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Quality score: {overall_score:.1f} ({grade.value}) - "
            f"Best: {max(criteria_scores.items(), key=lambda x: x[1].score)[0]}"
        )
        
        return quality_score
    
    def _score_clarity(self, content: Dict) -> CriterionScore:
        """Score text clarity and readability"""
        script = content.get("script", "")
        
        # Calculate metrics
        word_count = len(script.split())
        sentence_count = len(re.split(r'[.!?]+', script))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Score based on readability
        if avg_sentence_length < 15:
            score = 90
            details = "Excellent clarity with short, clear sentences"
        elif avg_sentence_length < 25:
            score = 75
            details = "Good clarity with moderate sentence length"
        else:
            score = 60
            details = "Fair clarity but sentences could be shorter"
        
        suggestions = []
        if avg_sentence_length > 20:
            suggestions.append("Consider breaking long sentences for clarity")
        
        return CriterionScore(
            name="clarity",
            score=score,
            weight=self.weights["clarity"],
            details=details,
            suggestions=suggestions
        )
    
    def _score_engagement(self, content: Dict) -> CriterionScore:
        """Score engagement potential"""
        hook = content.get("hook", "")
        script = content.get("script", "")
        
        # Engagement indicators
        has_question = "?" in hook
        has_numbers = any(char.isdigit() for char in hook)
        has_emotional_words = any(
            word in hook.lower()
            for word in ["shocking", "amazing", "incredible", "secret", "never"]
        )
        
        score = 60  # Base
        if has_question:
            score += 15
        if has_numbers:
            score += 10
        if has_emotional_words:
            score += 15
        
        score = min(score, 100)
        
        details = f"Engagement score based on hook analysis"
        suggestions = []
        if not has_question:
            suggestions.append("Consider adding a question to hook")
        
        return CriterionScore(
            name="engagement",
            score=score,
            weight=self.weights["engagement"],
            details=details,
            suggestions=suggestions
        )
    
    def _score_hook_quality(self, content: Dict) -> CriterionScore:
        """Score hook effectiveness"""
        hook = content.get("hook", "")
        
        # Hook quality metrics
        length = len(hook.split())
        
        if 5 <= length <= 15:
            score = 85
            details = "Optimal hook length"
        elif length < 5:
            score = 60
            details = "Hook is too short"
        else:
            score = 70
            details = "Hook is slightly long"
        
        return CriterionScore(
            name="hook_quality",
            score=score,
            weight=self.weights["hook_quality"],
            details=details
        )
    
    def _score_tone_consistency(self, content: Dict) -> CriterionScore:
        """Score tone consistency with brand"""
        # Mock: In production, use sentiment analysis
        score = 80
        details = "Tone aligns with brand guidelines"
        
        return CriterionScore(
            name="tone_consistency",
            score=score,
            weight=self.weights["tone_consistency"],
            details=details
        )
    
    def _score_pacing(self, content: Dict) -> CriterionScore:
        """Score content pacing"""
        # Mock: In production, use pacing engine
        score = 75
        details = "Pacing appropriate for genre"
        
        return CriterionScore(
            name="pacing",
            score=score,
            weight=self.weights["pacing"],
            details=details
        )
    
    def _score_grammar(self, content: Dict) -> CriterionScore:
        """Score grammar and language quality"""
        script = content.get("script", "")
        
        # Simple grammar checks (in production: use NLP library)
        has_basic_punctuation = any(p in script for p in ['.', '!', '?'])
        
        score = 85 if has_basic_punctuation else 70
        details = "Grammar quality acceptable"
        
        return CriterionScore(
            name="grammar",
            score=score,
            weight=self.weights["grammar"],
            details=details
        )
    
    def _score_originality(self, content: Dict) -> CriterionScore:
        """Score content originality"""
        # Mock: In production, check against content database
        score = 80
        details = "Content appears original"
        
        return CriterionScore(
            name="originality",
            score=score,
            weight=self.weights["originality"],
            details=details
        )
    
    def _score_emotional_impact(self, content: Dict) -> CriterionScore:
        """Score emotional impact"""
        # Mock: In production, use emotional arc analyzer
        score = 75
        details = "Emotional arc present"
        
        return CriterionScore(
            name="emotional_impact",
            score=score,
            weight=self.weights["emotional_impact"],
            details=details
        )
    
    def _score_brand_alignment(self, content: Dict) -> CriterionScore:
        """Score brand alignment"""
        persona = content.get("persona", "")
        
        score = 85 if persona else 70
        details = "Content aligns with brand persona"
        
        return CriterionScore(
            name="brand_alignment",
            score=score,
            weight=self.weights["brand_alignment"],
            details=details
        )
    
    def _score_technical_quality(self, content: Dict) -> CriterionScore:
        """Score technical quality (metadata, format)"""
        metadata = content.get("metadata", {})
        
        has_title = bool(metadata.get("title"))
        has_description = bool(metadata.get("description"))
        
        score = 90 if (has_title and has_description) else 75
        details = "Technical quality good"
        
        return CriterionScore(
            name="technical_quality",
            score=score,
            weight=self.weights["technical_quality"],
            details=details
        )
    
    def _get_grade(self, score: float) -> QualityGrade:
        """Convert score to grade"""
        if score >= 80:
            return QualityGrade.EXCELLENT
        elif score >= 60:
            return QualityGrade.GOOD
        elif score >= 40:
            return QualityGrade.FAIR
        else:
            return QualityGrade.POOR


# Global instance
quality_framework = QualityFramework()

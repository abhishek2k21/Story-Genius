"""
Variation Scoring
Score and rank script variations.
"""
from typing import List
import re

from app.scripts.variations.models import ScriptVariation, VariationScores


# Scoring patterns
EMOTIONAL_WORDS = ["amazing", "incredible", "secret", "powerful", "transform", "discover",
                   "surprising", "shocking", "essential", "ultimate", "proven"]
QUESTION_PATTERN = r'\?'
EXCLAMATION_PATTERN = r'!'


class VariationScorer:
    """Score script variations"""
    
    def score_variation(self, variation: ScriptVariation, target_duration: int = 60) -> VariationScores:
        """Calculate all scores for a variation"""
        scores = VariationScores(
            hook_strength=self._score_hook(variation.hook),
            clarity=self._score_clarity(variation.full_script),
            engagement_potential=self._score_engagement(variation.full_script),
            pacing_fit=self._score_pacing(variation.full_script, target_duration),
            cta_effectiveness=self._score_cta(variation.cta),
            uniqueness=80.0  # Default, adjusted during comparison
        )
        variation.scores = scores
        return scores
    
    def score_all(self, variations: List[ScriptVariation], target_duration: int = 60) -> None:
        """Score all variations and set uniqueness"""
        # Score individual dimensions
        for v in variations:
            self.score_variation(v, target_duration)
        
        # Calculate uniqueness between variations
        self._calculate_uniqueness(variations)
        
        # Detect strengths and weaknesses
        for v in variations:
            v.strengths = self._detect_strengths(v.scores)
            v.weaknesses = self._detect_weaknesses(v.scores)
        
        # Rank by total score
        self._rank_variations(variations)
    
    def _score_hook(self, hook: str) -> float:
        """Score hook effectiveness"""
        score = 50.0
        
        # Question boosts curiosity
        if re.search(QUESTION_PATTERN, hook):
            score += 15
        
        # Emotional words add impact
        hook_lower = hook.lower()
        for word in EMOTIONAL_WORDS:
            if word in hook_lower:
                score += 5
        
        # Length sweet spot (10-25 words)
        words = len(hook.split())
        if 10 <= words <= 25:
            score += 15
        elif words < 10:
            score += 5
        else:
            score -= 5
        
        # First word power
        first_word = hook.split()[0].lower() if hook else ""
        power_words = ["stop", "warning", "secret", "discover", "why", "how", "what"]
        if first_word in power_words:
            score += 10
        
        return min(100, max(0, score))
    
    def _score_clarity(self, script: str) -> float:
        """Score readability and clarity"""
        score = 70.0
        
        sentences = re.split(r'[.!?]', script)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 50.0
        
        # Average sentence length
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if avg_words <= 12:
            score += 20
        elif avg_words <= 18:
            score += 10
        elif avg_words > 25:
            score -= 15
        
        # Short paragraphs (check for line breaks)
        if script.count('\n\n') >= 2:
            score += 10
        
        return min(100, max(0, score))
    
    def _score_engagement(self, script: str) -> float:
        """Score engagement potential"""
        score = 50.0
        
        # Questions engage audience
        questions = len(re.findall(QUESTION_PATTERN, script))
        score += min(20, questions * 5)
        
        # Emotional language
        script_lower = script.lower()
        for word in EMOTIONAL_WORDS:
            if word in script_lower:
                score += 3
        
        # Direct address (you, your)
        you_count = script_lower.count(' you ') + script_lower.count(' your ')
        score += min(15, you_count * 2)
        
        # Exclamations add energy
        exclamations = len(re.findall(EXCLAMATION_PATTERN, script))
        score += min(10, exclamations * 3)
        
        return min(100, max(0, score))
    
    def _score_pacing(self, script: str, target_duration: int) -> float:
        """Score pacing fit to target duration"""
        # Estimate: ~150 words per minute
        words = len(script.split())
        estimated_seconds = (words / 150) * 60
        
        deviation = abs(estimated_seconds - target_duration) / target_duration
        
        if deviation <= 0.1:
            return 100.0
        elif deviation <= 0.2:
            return 85.0
        elif deviation <= 0.3:
            return 70.0
        elif deviation <= 0.5:
            return 50.0
        else:
            return 30.0
    
    def _score_cta(self, cta: str) -> float:
        """Score call to action effectiveness"""
        score = 50.0
        
        cta_lower = cta.lower()
        
        # Action verbs
        action_words = ["subscribe", "like", "share", "comment", "follow", "save", "click", "watch"]
        for word in action_words:
            if word in cta_lower:
                score += 10
        
        # Urgency words
        urgency_words = ["now", "today", "next", "immediately", "don't miss"]
        for word in urgency_words:
            if word in cta_lower:
                score += 10
        
        # Single focus
        action_count = sum(1 for w in action_words if w in cta_lower)
        if action_count == 1:
            score += 10
        elif action_count > 2:
            score -= 10
        
        return min(100, max(0, score))
    
    def _calculate_uniqueness(self, variations: List[ScriptVariation]) -> None:
        """Calculate uniqueness scores between variations"""
        if len(variations) <= 1:
            for v in variations:
                v.scores.uniqueness = 100.0
            return
        
        for i, v1 in enumerate(variations):
            other_hooks = [v.hook for j, v in enumerate(variations) if j != i]
            
            # Check hook distinctness
            hook_words = set(v1.hook.lower().split())
            similarities = []
            
            for other in other_hooks:
                other_words = set(other.lower().split())
                overlap = len(hook_words & other_words) / max(len(hook_words), 1)
                similarities.append(overlap)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            v1.scores.uniqueness = max(0, 100 - (avg_similarity * 100))
    
    def _detect_strengths(self, scores: VariationScores) -> List[str]:
        """Detect strengths from scores"""
        strengths = []
        
        if scores.hook_strength >= 80:
            strengths.append("Strong hook")
        if scores.clarity >= 85:
            strengths.append("Clear message")
        if scores.engagement_potential >= 80:
            strengths.append("High engagement")
        if scores.pacing_fit >= 90:
            strengths.append("Perfect pacing")
        if scores.cta_effectiveness >= 80:
            strengths.append("Effective CTA")
        if scores.uniqueness >= 85:
            strengths.append("Highly unique")
        
        return strengths
    
    def _detect_weaknesses(self, scores: VariationScores) -> List[str]:
        """Detect weaknesses from scores"""
        weaknesses = []
        
        if scores.hook_strength < 60:
            weaknesses.append("Weak opening")
        if scores.clarity < 60:
            weaknesses.append("Too complex")
        if scores.engagement_potential < 60:
            weaknesses.append("Low engagement")
        if scores.pacing_fit < 70:
            weaknesses.append("Duration mismatch")
        if scores.cta_effectiveness < 50:
            weaknesses.append("Weak CTA")
        if scores.uniqueness < 50:
            weaknesses.append("Too similar to others")
        
        return weaknesses
    
    def _rank_variations(self, variations: List[ScriptVariation]) -> None:
        """Rank variations by total score"""
        sorted_vars = sorted(variations, key=lambda v: v.scores.total(), reverse=True)
        
        for rank, v in enumerate(sorted_vars, 1):
            v.rank = rank


variation_scorer = VariationScorer()

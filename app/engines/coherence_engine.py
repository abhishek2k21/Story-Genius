"""
Coherence Engine for Script-Hook Validation
Scores the coherence between hooks and scripts on a 0-100 scale.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CoherenceScore:
    """Coherence score with breakdown"""
    total_score: float  # 0-100
    semantic_overlap: float  # 0-20
    tone_consistency: float  # 0-20
    narrative_continuity: float  # 0-20
    emotion_alignment: float  # 0-20
    brand_voice: float  # 0-20
    grade: str  # Excellent, Good, Fair, Poor
    issues: List[str]
    suggestions: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 2),
            "breakdown": {
                "semantic_overlap": round(self.semantic_overlap, 2),
                "tone_consistency": round(self.tone_consistency, 2),
                "narrative_continuity": round(self.narrative_continuity, 2),
                "emotion_alignment": round(self.emotion_alignment, 2),
                "brand_voice": round(self.brand_voice, 2)
            },
            "grade": self.grade,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }


class CoherenceEngine:
    """
    Analyzes coherence between hooks and scripts.
    Uses 5 metrics to calculate a comprehensive coherence score.
    """
    
    # Scoring thresholds
    EXCELLENT_THRESHOLD = 90
    GOOD_THRESHOLD = 70
    FAIR_THRESHOLD = 50
    
    def __init__(self):
        logger.info("CoherenceEngine initialized")
    
    def calculate_coherence(
        self,
        hook: str,
        script: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CoherenceScore:
        """
        Calculate coherence score between hook and script.
        
        Args:
            hook: Hook text
            script: Full script text
            metadata: Optional metadata (genre, tone, brand)
        
        Returns:
            CoherenceScore with detailed breakdown
        """
        logger.info("Calculating coherence between hook and script")
        
        # Calculate individual metrics
        semantic = self._calculate_semantic_overlap(hook, script)
        tone = self._calculate_tone_consistency(hook, script)
        narrative = self._calculate_narrative_continuity(hook, script)
        emotion = self._calculate_emotion_alignment(hook, script)
        brand = self._calculate_brand_voice(hook, script, metadata)
        
        # Total score (sum of all metrics)
        total = semantic + tone + narrative + emotion + brand
        
        # Determine grade
        if total >= self.EXCELLENT_THRESHOLD:
            grade = "Excellent"
        elif total >= self.GOOD_THRESHOLD:
            grade = "Good"
        elif total >= self.FAIR_THRESHOLD:
            grade = "Fair"
        else:
            grade = "Poor"
        
        # Identify issues
        issues = self._identify_issues(semantic, tone, narrative, emotion, brand)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(semantic, tone, narrative, emotion, brand)
        
        score = CoherenceScore(
            total_score=total,
            semantic_overlap=semantic,
            tone_consistency=tone,
            narrative_continuity=narrative,
            emotion_alignment=emotion,
            brand_voice=brand,
            grade=grade,
            issues=issues,
            suggestions=suggestions
        )
        
        logger.info(f"Coherence calculated: {total}/100 ({grade})")
        return score
    
    def _calculate_semantic_overlap(self, hook: str, script: str) -> float:
        """
        Calculate semantic overlap between hook and script (0-20).
        Uses word overlap and key concept matching.
        """
        hook_words = set(self._extract_keywords(hook.lower()))
        script_words = set(self._extract_keywords(script.lower()))
        
        if not hook_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = hook_words.intersection(script_words)
        union = hook_words.union(script_words)
        
        similarity = len(intersection) / len(union) if union else 0
        
        # Scale to 0-20 (70%+ similarity = full 20 points)
        score = min(20, (similarity / 0.7) * 20)
        
        logger.debug(f"Semantic overlap: {score:.2f}/20 ({similarity:.1%} similarity)")
        return score
    
    def _calculate_tone_consistency(self, hook: str, script: str) -> float:
        """
        Calculate tone consistency between hook and script (0-20).
        Analyzes formality, sentiment, and style.
        """
        hook_tone = self._analyze_tone(hook)
        script_tone = self._analyze_tone(script)
        
        # Compare tones (simple heuristic)
        tone_match = 0
        if hook_tone["formality"] == script_tone["formality"]:
            tone_match += 0.33
        if abs(hook_tone["sentiment"] - script_tone["sentiment"]) < 0.3:
            tone_match += 0.33
        if hook_tone["energy"] == script_tone["energy"]:
            tone_match += 0.34
        
        # Scale to 0-20 (80%+ match = full 20 points)
        score = min(20, (tone_match / 0.8) * 20)
        
        logger.debug(f"Tone consistency: {score:.2f}/20")
        return score
    
    def _calculate_narrative_continuity(self, hook: str, script: str) -> float:
        """
        Calculate narrative continuity (0-20).
        Checks if script naturally flows from hook.
        """
        # Check if hook concepts appear in script
        hook_concepts = self._extract_keywords(hook)
        script_start = script[:len(script)//3]  # First third of script
        
        concepts_in_script = sum(
            1 for concept in hook_concepts 
            if concept.lower() in script_start.lower()
        )
        
        continuity = concepts_in_script / len(hook_concepts) if hook_concepts else 0
        
        # Check for narrative progression (hook should lead into script)
        has_progression = self._check_progression(hook, script)
        if has_progression:
            continuity += 0.2
        
        score = min(20, continuity * 20)
        
        logger.debug(f"Narrative continuity: {score:.2f}/20")
        return score
    
    def _calculate_emotion_alignment(self, hook: str, script: str) -> float:
        """
        Calculate emotion alignment (0-20).
        Ensures emotional tone is consistent.
        """
        hook_emotions = self._detect_emotions(hook)
        script_emotions = self._detect_emotions(script)
        
        # Check for emotion overlap
        emotion_overlap = len(set(hook_emotions).intersection(set(script_emotions)))
        total_emotions = len(set(hook_emotions + script_emotions))
        
        alignment = emotion_overlap / total_emotions if total_emotions else 0
        
        score = alignment * 20
        
        logger.debug(f"Emotion alignment: {score:.2f}/20")
        return score
    
    def _calculate_brand_voice(
        self, 
        hook: str, 
        script: str, 
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Calculate brand voice consistency (0-20).
        Checks adherence to brand guidelines.
        """
        # Default: check for consistent person (1st/2nd/3rd)
        hook_person = self._detect_person(hook)
        script_person = self._detect_person(script)
        
        consistency = 1.0 if hook_person == script_person else 0.5
        
        # If metadata provided, check brand keywords
        if metadata and "brand_keywords" in metadata:
            brand_keywords = metadata["brand_keywords"]
            brand_presence = sum(
                1 for keyword in brand_keywords 
                if keyword.lower() in script.lower()
            )
            consistency *= (1 + brand_presence * 0.1)
        
        score = min(20, consistency * 20)
        
        logger.debug(f"Brand voice: {score:.2f}/20")
        return score
    
    def _identify_issues(
        self, 
        semantic: float, 
        tone: float, 
        narrative: float, 
        emotion: float, 
        brand: float
    ) -> List[str]:
        """Identify specific issues based on low scores"""
        issues = []
        
        if semantic < 10:
            issues.append("Low semantic overlap between hook and script")
        if tone < 10:
            issues.append("Inconsistent tone between hook and script")
        if narrative < 10:
            issues.append("Weak narrative continuity from hook to script")
        if emotion < 10:
            issues.append("Emotional misalignment between hook and script")
        if brand < 10:
            issues.append("Brand voice inconsistency detected")
        
        return issues
    
    def _generate_suggestions(
        self, 
        semantic: float, 
        tone: float, 
        narrative: float, 
        emotion: float, 
        brand: float
    ) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if semantic < 15:
            suggestions.append("Incorporate more keywords from the hook into the script")
        if tone < 15:
            suggestions.append("Adjust script tone to match the hook's style")
        if narrative < 15:
            suggestions.append("Strengthen the narrative connection between hook and opening")
        if emotion < 15:
            suggestions.append("Align emotional trajectory with hook's emotional tone")
        if brand < 15:
            suggestions.append("Ensure consistent voice and perspective throughout")
        
        return suggestions
    
    # Helper methods
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simple stopword filtering)"""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                     'it', 'this', 'that', 'these', 'those', 'you', 'your', 'we', 'our'}
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 3]
    
    def _analyze_tone(self, text: str) -> Dict[str, Any]:
        """Analyze tone of text"""
        # Simple heuristics
        formal_markers = ['therefore', 'furthermore', 'moreover', 'consequently']
        casual_markers = ['yeah', 'cool', 'awesome', 'wow', 'hey']
        
        is_formal = any(marker in text.lower() for marker in formal_markers)
        is_casual = any(marker in text.lower() for marker in casual_markers)
        
        # Sentiment (simple positive/negative word counting)
        positive_words = ['good', 'great', 'amazing', 'excellent', 'love', 'best']
        negative_words = ['bad', 'terrible', 'worst', 'hate', 'awful', 'poor']
        
        pos_count = sum(1 for word in positive_words if word in text.lower())
        neg_count = sum(1 for word in negative_words if word in text.lower())
        
        sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        
        # Energy (exclamation marks, caps)
        energy = "high" if "!" in text or text.isupper() else "low"
        
        return {
            "formality": "formal" if is_formal else ("casual" if is_casual else "neutral"),
            "sentiment": sentiment,
            "energy": energy
        }
    
    def _check_progression(self, hook: str, script: str) -> bool:
        """Check if script progresses naturally from hook"""
        # Simple check: script should not just repeat hook
        hook_lower = hook.lower()
        script_start = script[:len(script)//4].lower()
        
        # If script start is very similar to hook, it's just repeating
        if hook_lower in script_start:
            return False  # Repetition, not progression
        
        return True  # Assumed progression
    
    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotions in text"""
        emotion_keywords = {
            "joy": ["happy", "joy", "excited", "love", "amazing", "wonderful"],
            "sadness": ["sad", "unhappy", "disappointed", "depressed", "crying"],
            "anger": ["angry", "mad", "furious", "rage", "annoyed"],
            "fear": ["scared", "afraid", "terrified", "worried", "anxious"],
            "surprise": ["surprised", "shocked", "astonished", "wow"],
            "anticipation": ["excited", "eager", "looking forward", "anticipate"]
        }
        
        detected = []
        text_lower = text.lower()
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected.append(emotion)
        
        return detected if detected else ["neutral"]
    
    def _detect_person(self, text: str) -> str:
        """Detect grammatical person (1st, 2nd, 3rd)"""
        if any(word in text.lower() for word in ['i', 'me', 'my', 'we', 'our', 'us']):
            return "first"
        elif any(word in text.lower() for word in ['you', 'your', 'yours']):
            return "second"
        else:
            return "third"


# Global instance
coherence_engine = CoherenceEngine()

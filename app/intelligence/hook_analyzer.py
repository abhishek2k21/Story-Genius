"""
Hook Intelligence Analyzer
Generates original, high-performing hooks using AI and pattern analysis.
"""
from typing import List, Optional, Dict
from dataclasses import dataclass
import difflib
from app.intelligence.viral_patterns import (
    GENERIC_PATTERNS,
    VIRAL_PATTERNS,
    EmotionalTrigger,
    get_high_retention_patterns
)
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Hook:
    """Represents a generated hook"""
    text: str
    originality_score: float
    predicted_retention: float
    emotional_trigger: EmotionalTrigger
    pattern_used: Optional[str] = None


class HookAnalyzer:
    """Analyzes and generates high-quality hooks"""
    
    def __init__(self, llm_service=None):
        """
        Initialize hook analyzer
        
        Args:
            llm_service: LLM service for generation (defaults to Gemini)
        """
        self.llm_service = llm_service or self._get_default_llm()
        self.previous_hooks: List[str] = []
    
    def _get_default_llm(self):
        """Get default LLM service (Gemini)"""
        # Import here to avoid circular dependency
        from app.llm.gemini_service import GeminiService
        return GeminiService()
    
    def score_hook_originality(self, hook: str, avoid_patterns: Optional[List[str]] = None) -> float:
        """
        Score hook originality from 0-1
        
        Checks against:
        - Generic patterns (templates to avoid)
        - Previous hooks (avoid repetition)
        - Custom patterns to avoid
        
        Returns:
            float: Originality score (1.0 = completely original, 0 = generic)
        """
        hook_lower = hook.lower()
        
        # Check for generic patterns
        for pattern in GENERIC_PATTERNS:
            if pattern in hook_lower:
                logger.debug(f"Hook contains generic pattern: {pattern}")
                return 0.2  # Very low originality
        
        # Check for custom avoid patterns
        if avoid_patterns:
            for pattern in avoid_patterns:
                if pattern.lower() in hook_lower:
                    logger.debug(f"Hook contains avoided pattern: {pattern}")
                    return 0.3
        
        # Check similarity to previous hooks
        if self.previous_hooks:
            max_similarity = max(
                difflib.SequenceMatcher(None, hook_lower, prev.lower()).ratio()
                for prev in self.previous_hooks
            )
            if max_similarity > 0.8:
                logger.debug(f"Hook too similar to previous (similarity: {max_similarity:.2f})")
                return 0.4
        
        # Check uniqueness - simple heuristic based on word choice
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that'}
        words = set(hook_lower.split())
        unique_ratio = len(words - common_words) / max(len(words), 1)
        
        # Calculate final score
        base_score = 0.7  # Start with decent score if no issues
        uniqueness_bonus = unique_ratio * 0.3  # Up to 0.3 bonus for unique words
        
        return min(base_score + uniqueness_bonus, 1.0)
    
    def generate_hook_variants(
        self,
        topic: str,
        avoid_patterns: Optional[List[str]] = None,
        emotional_trigger: Optional[EmotionalTrigger] = None,
        count: int = 10
    ) -> List[Hook]:
        """
        Generate multiple hook variants and rank them
        
        Args:
            topic: The video topic
            avoid_patterns: List of patterns/phrases to avoid
            emotional_trigger: Preferred emotional trigger
            count: Number of variants to generate
        
        Returns:
            List of top 3 hooks ranked by predicted performance
        """
        # Get relevant patterns
        if emotional_trigger:
            patterns = [p for p in VIRAL_PATTERNS if p.emotional_trigger == emotional_trigger]
        else:
            patterns = get_high_retention_patterns(min_retention=0.75)
        
        # Build generation prompt
        pattern_examples = "\n".join([
            f"- Pattern: {p.pattern_type}, Examples: {', '.join(p.examples[:2])}"
            for p in patterns[:3]
        ])
        
        avoid_text = ""
        if avoid_patterns:
            avoid_text = f"\n\nAVOID these phrases: {', '.join(avoid_patterns)}"
        
        prompt = f"""
Generate {count} unique, attention-grabbing hooks for a short video about: "{topic}"

Requirements:
- Each hook should be 3-12 words
- Must hook viewer in first 2 seconds
- Use interesting, specific language
- Avoid generic phrases like "did you know", "you won't believe"
{avoid_text}

Inspiration from viral patterns:
{pattern_examples}

Return ONLY the hooks, one per line, numbered 1-{count}.
Make each one distinctly different.
"""
        
        try:
            # Generate hooks using LLM
            response = self.llm_service.generate_text(prompt)
            
            # Parse hooks from response
            generated_texts = self._parse_hook_list(response, count)
            
            # Score and rank hooks
            hooks = []
            for hook_text in generated_texts:
                originality = self.score_hook_originality(hook_text, avoid_patterns)
                
                # Predict retention based on originality and length
                word_count = len(hook_text.split())
                length_penalty = 0 if word_count <= 10 else 0.1
                predicted_retention = min(originality * 0.85 - length_penalty, 1.0)
                
                # Determine emotional trigger (simple heuristic)
                detected_trigger = self._detect_emotional_trigger(hook_text)
                
                hooks.append(Hook(
                    text=hook_text,
                    originality_score=originality,
                    predicted_retention=predicted_retention,
                    emotional_trigger=detected_trigger,
                    pattern_used=None  # Could enhance this later
                ))
            
            # Sort by predicted retention and originality
            hooks.sort(
                key=lambda h: (h.predicted_retention * 0.6 + h.originality_score * 0.4),
                reverse=True
            )
            
            # Return top 3
            top_hooks = hooks[:3]
            
            # Store for future originality checks
            self.previous_hooks.extend([h.text for h in top_hooks])
            
            logger.info(f"Generated {len(hooks)} hooks, returning top 3")
            for i, hook in enumerate(top_hooks, 1):
                logger.debug(
                    f"Hook {i}: '{hook.text}' "
                    f"(originality: {hook.originality_score:.2f}, "
                    f"retention: {hook.predicted_retention:.2f})"
                )
            
            return top_hooks
            
        except Exception as e:
            logger.error(f"Error generating hooks: {e}")
            # Return fallback hook
            return [Hook(
                text=f"Discover the truth about {topic}",
                originality_score=0.5,
                predicted_retention=0.6,
                emotional_trigger=EmotionalTrigger.CURIOSITY
            )]
    
    def _parse_hook_list(self, response: str, expected_count: int) -> List[str]:
        """Parse numbered list of hooks from LLM response"""
        hooks = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 1), etc.)
            if line[0].isdigit():
                # Find first non-digit, non-punctuation char
                for i, char in enumerate(line):
                    if char.isalpha():
                        line = line[i:].strip()
                        break
            
            if line and len(line.split()) >= 3:  # At least 3 words
                hooks.append(line)
        
        return hooks[:expected_count]
    
    def _detect_emotional_trigger(self, hook: str) -> EmotionalTrigger:
        """Simple heuristic to detect emotional trigger"""
        hook_lower = hook.lower()
        
        # Curiosity keywords
        if any(word in hook_lower for word in ['why', 'how', 'secret', 'hidden', 'mystery']):
            return EmotionalTrigger.CURIOSITY
        
        # Shock keywords
        if any(word in hook_lower for word in ['shocking', 'unbelievable', 'insane', 'crazy']):
            return EmotionalTrigger.SHOCK
        
        # Fear keywords
        if any(word in hook_lower for word in ['danger', 'warning', 'stop', 'never']):
            return EmotionalTrigger.FEAR
        
        # Surprise keywords
        if any(word in hook_lower for word in ['discover', 'reveal', 'truth', 'nobody knows']):
            return EmotionalTrigger.SURPRISE
        
        # Default to intrigue
        return EmotionalTrigger.INTRIGUE

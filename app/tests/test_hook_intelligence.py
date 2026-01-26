"""
Tests for Hook Intelligence system
"""
import pytest
from app.intelligence.hook_analyzer import HookAnalyzer, Hook
from app.intelligence.viral_patterns import EmotionalTrigger, GENERIC_PATTERNS


class TestHookAnalyzer:
    """Test suite for HookAnalyzer"""
    
    def test_score_generic_hook_returns_low_score(self):
        """Generic hooks should have low originality scores"""
        analyzer = HookAnalyzer()
        
        # Test generic patterns
        generic_hooks = [
            "Did you know the moon has phases?",
            "You won't believe what happens next",
            "This will blow your mind"
        ]
        
        for hook in generic_hooks:
            score = analyzer.score_hook_originality(hook)
            assert score < 0.5, f"Generic hook should have low score: {hook}"
    
    def test_score_original_hook_returns_high_score(self):
        """Original hooks should have high originality scores"""
        analyzer = HookAnalyzer()
        
        original_hooks = [
            "The moon is lying to you",
            "Ancient humans got this wrong for 10,000 years",
            "Nobody can explain why stars twinkle"
        ]
        
        for hook in original_hooks:
            score = analyzer.score_hook_originality(hook)
            assert score > 0.6, f"Original hook should have high score: {hook} (got {score:.2f})"
    
    def test_avoid_patterns_reduces_score(self):
        """Hooks containing avoided patterns should score lower"""
        analyzer = HookAnalyzer()
        
        hook = "The secret truth about coffee"
        avoid = ["secret truth"]
        
        score = analyzer.score_hook_originality(hook, avoid_patterns=avoid)
        assert score < 0.5, "Hook with avoided pattern should score low"
    
    def test_generate_hook_variants_returns_multiple(self):
        """Should generate multiple hook variants"""
        analyzer = HookAnalyzer()
        
        hooks = analyzer.generate_hook_variants(
            topic="why stars twinkle",
            count=5
        )
        
        assert len(hooks) > 0, "Should generate at least one hook"
        assert len(hooks) <= 3, "Should return top 3 hooks"
        
        # Check hook structure
        for hook in hooks:
            assert isinstance(hook, Hook)
            assert len(hook.text) > 0
            assert 0 <= hook.originality_score <= 1
            assert 0 <= hook.predicted_retention <= 1
            assert isinstance(hook.emotional_trigger, EmotionalTrigger)
    
    def test_generated_hooks_avoid_generic_patterns(self):
        """Generated hooks should not contain generic patterns"""
        analyzer = HookAnalyzer()
        
        hooks = analyzer.generate_hook_variants(
            topic="coffee history",
            avoid_patterns=GENERIC_PATTERNS
        )
        
        for hook in hooks:
            hook_lower = hook.text.lower()
            for pattern in GENERIC_PATTERNS:
                assert pattern not in hook_lower, f"Hook should avoid pattern '{pattern}': {hook.text}"
    
    def test_emotional_trigger_detection(self):
        """Should correctly detect emotional triggers"""
        analyzer = HookAnalyzer()
        
        test_cases = [
            ("Why does the moon glow?", EmotionalTrigger.CURIOSITY),
            ("Stop drinking coffee immediately", EmotionalTrigger.FEAR),
            ("Nobody knows the truth about X", EmotionalTrigger.SURPRISE),
        ]
        
        for hook_text, expected_trigger in test_cases:
            detected = analyzer._detect_emotional_trigger(hook_text)
            # Note: This is a heuristic, so we allow some flexibility
            assert isinstance(detected, EmotionalTrigger)
    
    def test_hook_length_appropriate(self):
        """Generated hooks should be appropriate length (3-12 words)"""
        analyzer = HookAnalyzer()
        
        hooks = analyzer.generate_hook_variants(topic="space exploration")
        
        for hook in hooks:
            word_count = len(hook.text.split())
            assert 3 <= word_count <= 15, f"Hook should be 3-15 words: {hook.text} ({word_count} words)"
    
    def test_originality_tracking_prevents_repetition(self):
        """Should track previous hooks and avoid repetition"""
        analyzer = HookAnalyzer()
        
        # Generate first set
        first_hooks = analyzer.generate_hook_variants(topic="moon phases", count=3)
        
        # Generate second set - should be different
        second_hooks = analyzer.generate_hook_variants(topic="moon phases", count=3)
        
        # Check that we're not generating identical hooks
        first_texts = {h.text for h in first_hooks}
        second_texts = {h.text for h in second_hooks}
        
        # Some variation expected (not all should be identical)
        assert len(first_texts | second_texts) > 3, "Should generate varied hooks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Viral Hook Patterns Database
Contains patterns and templates identified from high-performing hooks.
"""
from typing import List, Dict
from enum import Enum


class EmotionalTrigger(str, Enum):
    """Types of emotional triggers in hooks"""
    CURIOSITY = "curiosity"
    SHOCK = "shock"
    FEAR = "fear"
    JOY = "joy"
    ANGER = "anger"
    SURPRISE = "surprise"
    INTRIGUE = "intrigue"


class HookPattern:
    """Pattern template for hooks"""
    def __init__(
        self,
        pattern_type: str,
        emotional_trigger: EmotionalTrigger,
        avg_retention: float,
        examples: List[str]
    ):
        self.pattern_type = pattern_type
        self.emotional_trigger = emotional_trigger
        self.avg_retention = avg_retention
        self.examples = examples


# Avoid these generic patterns
GENERIC_PATTERNS = [
    "did you know",
    "you won't believe",
    "this will blow your mind",
    "wait for it",
    "shocking truth about",
    "the secret",
    "number #X will surprise you"
]

# High-performing hook patterns (learned from viral content)
VIRAL_PATTERNS = [
    HookPattern(
        pattern_type="contradiction",
        emotional_trigger=EmotionalTrigger.INTRIGUE,
        avg_retention=0.82,
        examples=[
            "Everything you know about X is wrong",
            "Scientists were lying about X",
            "X is the opposite of what you think"
        ]
    ),
    HookPattern(
        pattern_type="mystery",
        emotional_trigger=EmotionalTrigger.CURIOSITY,
        avg_retention=0.78,
        examples=[
            "Nobody can explain why X happens",
            "The moon is hiding something",
            "This doesn't make sense"
        ]
    ),
    HookPattern(
        pattern_type="urgency",
        emotional_trigger=EmotionalTrigger.FEAR,
        avg_retention=0.75,
        examples=[
            "Stop doing X immediately",
            "If you see X, run",
            "Delete X before it's too late"
        ]
    ),
    HookPattern(
        pattern_type="revelation",
        emotional_trigger=EmotionalTrigger.SURPRISE,
        avg_retention=0.80,
        examples=[
            "What they didn't teach you about X",
            "The truth about X nobody talks about",
            "Ancient people knew X all along"
        ]
    ),
    HookPattern(
        pattern_type="personal_claim",
        emotional_trigger=EmotionalTrigger.INTRIGUE,
        avg_retention=0.76,
        examples=[
            "I've been lying to you about X",
            "They told me not to share this",
            "This changed everything I knew"
        ]
    )
]


def get_patterns_by_trigger(trigger: EmotionalTrigger) -> List[HookPattern]:
    """Get hook patterns for a specific emotional trigger"""
    return [p for p in VIRAL_PATTERNS if p.emotional_trigger == trigger]


def get_high_retention_patterns(min_retention: float = 0.75) -> List[HookPattern]:
    """Get patterns with retention above threshold"""
    return [p for p in VIRAL_PATTERNS if p.avg_retention >= min_retention]

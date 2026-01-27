"""
Hook Templates
Proven viral hook patterns for video content.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class HookStyle(str, Enum):
    CURIOSITY = "curiosity"
    CONTRARIAN = "contrarian"
    FEAR = "fear"
    SECRET = "secret"
    CHALLENGE = "challenge"
    SHOCKING = "shocking"
    STORY = "story"
    QUESTION = "question"


@dataclass
class HookTemplate:
    """Template for generating hooks"""
    id: str
    name: str
    style: HookStyle
    pattern: str  # Pattern with {topic} placeholder
    example: str
    effectiveness_baseline: float  # 0-1
    
    def generate(self, topic: str, **kwargs) -> str:
        """Generate hook text from template"""
        return self.pattern.format(topic=topic, **kwargs)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "style": self.style.value,
            "pattern": self.pattern,
            "example": self.example,
            "effectiveness": self.effectiveness_baseline
        }


# Built-in hook templates
HOOK_TEMPLATES: List[HookTemplate] = [
    HookTemplate(
        id="curiosity_gap",
        name="Curiosity Gap",
        style=HookStyle.CURIOSITY,
        pattern="Nobody knows why {topic} actually happens",
        example="Nobody knows why yawning is contagious",
        effectiveness_baseline=0.75
    ),
    HookTemplate(
        id="contrarian_claim",
        name="Contrarian Claim",
        style=HookStyle.CONTRARIAN,
        pattern="Everything you believe about {topic} is wrong",
        example="Everything you believe about dieting is wrong",
        effectiveness_baseline=0.80
    ),
    HookTemplate(
        id="fear_trigger",
        name="Fear Trigger",
        style=HookStyle.FEAR,
        pattern="Stop doing this with {topic} immediately",
        example="Stop doing this with your phone immediately",
        effectiveness_baseline=0.72
    ),
    HookTemplate(
        id="secret_promise",
        name="Secret Promise",
        style=HookStyle.SECRET,
        pattern="What experts won't tell you about {topic}",
        example="What doctors won't tell you about sleep",
        effectiveness_baseline=0.78
    ),
    HookTemplate(
        id="direct_challenge",
        name="Direct Challenge",
        style=HookStyle.CHALLENGE,
        pattern="You're using {topic} completely wrong",
        example="You're using your brain completely wrong",
        effectiveness_baseline=0.70
    ),
    HookTemplate(
        id="shocking_fact",
        name="Shocking Fact",
        style=HookStyle.SHOCKING,
        pattern="Here's a fact about {topic} that will shock you",
        example="Here's a fact about water that will shock you",
        effectiveness_baseline=0.68
    ),
    HookTemplate(
        id="story_open",
        name="Story Opening",
        style=HookStyle.STORY,
        pattern="In 2024, something impossible happened with {topic}",
        example="In 2024, something impossible happened with AI",
        effectiveness_baseline=0.73
    ),
    HookTemplate(
        id="provocative_question",
        name="Provocative Question",
        style=HookStyle.QUESTION,
        pattern="Why does {topic} work this way?",
        example="Why does gravity work this way?",
        effectiveness_baseline=0.65
    ),
    HookTemplate(
        id="conspiracy",
        name="Hidden Truth",
        style=HookStyle.SECRET,
        pattern="They don't want you to know this about {topic}",
        example="They don't want you to know this about money",
        effectiveness_baseline=0.82
    ),
    HookTemplate(
        id="bet_you",
        name="Bet You Didn't Know",
        style=HookStyle.CURIOSITY,
        pattern="I bet you didn't know this about {topic}",
        example="I bet you didn't know this about your eyes",
        effectiveness_baseline=0.67
    )
]


def get_template(template_id: str) -> HookTemplate:
    """Get template by ID"""
    for t in HOOK_TEMPLATES:
        if t.id == template_id:
            return t
    return HOOK_TEMPLATES[0]


def get_templates_by_style(style: HookStyle) -> List[HookTemplate]:
    """Get all templates for a style"""
    return [t for t in HOOK_TEMPLATES if t.style == style]


def list_all_templates() -> List[Dict]:
    """List all available templates"""
    return [t.to_dict() for t in HOOK_TEMPLATES]

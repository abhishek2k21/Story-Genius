"""
Base Prompts System
Centralized prompt management for LLM interactions.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class PromptType(str, Enum):
    """Types of prompts in the system"""
    HOOK = "hook"
    SCRIPT = "script"
    CRITIC = "critic"
    STRATEGY = "strategy"
    NARRATION = "narration"
    SCENE_DESCRIPTION = "scene_description"
    TITLE_GENERATION = "title_generation"


@dataclass
class Prompt:
    """Prompt definition with metadata"""
    id: str
    name: str
    type: PromptType
    template: str
    version: str
    variables: List[str]
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    author: str = "system"
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


# ==================== Base Prompts ====================

HOOK_GENERATION_PROMPT = Prompt(
    id="hook_v1",
    name="Hook Generation",
    type=PromptType.HOOK,
    version="1.0",
    template="""You are an expert short-form video creator specializing in {{platform}} content.

Generate an attention-grabbing hook for a {{genre}} video targeting {{audience}}.

Requirements:
- First 3 seconds must stop scrolling
- Match {{tone}} tone
- Maximum 15 words
- Include emotional trigger or curiosity gap

Context:
- Platform: {{platform}}
- Duration: {{duration}} seconds
- Audience: {{audience}}
- Genre: {{genre}}

Return ONLY the hook text, no explanations.""",
    variables=["platform", "genre", "audience", "tone", "duration"],
    description="Generates scroll-stopping hooks for short-form videos",
    metadata={"max_tokens": 100, "temperature": 0.9}
)


SCRIPT_GENERATION_PROMPT = Prompt(
    id="script_v1",
    name="Script Generation",
    type=PromptType.SCRIPT,
    version="1.0",
    template="""You are a professional scriptwriter for {{platform}} content.

Create a compelling {{duration}}-second script for a {{genre}} video.

Requirements:
- Target audience: {{audience}}
- Tone: {{tone}}
- Include strong hook (first 3 seconds)
- Build emotional arc
- Clear call-to-action at end
- Optimize for {{platform}} algorithm

{% if additional_context %}
Additional Context: {{additional_context}}
{% endif %}

Format your response as JSON:
{
    "hook": "First 3 seconds script",
    "main_content": "Main story/content",
    "call_to_action": "Ending CTA",
    "estimated_duration": <seconds>
}""",
    variables=["platform", "duration", "genre", "audience", "tone"],
    description="Generates full video scripts with hook, content, and CTA",
    metadata={"max_tokens": 1500, "temperature": 0.8}
)


CRITIC_PROMPT = Prompt(
    id="critic_v1",
    name="Content Critique",
    type=PromptType.CRITIC,
    version="1.0",
    template="""You are an expert video content critic specializing in {{platform}}.

Evaluate this script for a {{genre}} video targeting {{audience}}:

SCRIPT:
{{script}}

Provide scores (1-10) for:
1. **Hook Strength**: Does it stop scrolling in first 3 seconds?
2. **Pacing**: Is the rhythm appropriate for {{platform}}?
3. **Emotional Arc**: Does it build engagement?
4. **Platform Fit**: Optimized for {{platform}} algorithm?
5. **Audience Match**: Resonates with {{audience}}?

Format response as JSON:
{
    "scores": {
        "hook_strength": <1-10>,
        "pacing": <1-10>,
        "emotional_arc": <1-10>,
        "platform_fit": <1-10>,
        "audience_match": <1-10>
    },
    "overall_score": <average>,
    "strengths": ["strength1", "strength2"],
    "improvements": ["suggestion1", "suggestion2"]
}""",
    variables=["platform", "genre", "audience", "script"],
    description="Critiques video scripts with detailed scoring",
    metadata={"max_tokens": 800, "temperature": 0.5}
)


STRATEGY_PROMPT = Prompt(
    id="strategy_v1",
    name="Audience Strategy",
    type=PromptType.STRATEGY,
    version="1.0",
    template="""You are a social media strategist specializing in {{platform}}.

Create a content strategy for reaching {{audience}} with {{genre}} content.

Recommendations needed:
1. Best posting times
2. Hashtag strategy (5-10 tags)
3. Thumbnail/cover image style
4. Caption recommendations
5. Engagement tactics

Target metrics:
- Reach: {{target_reach}}
- Engagement rate: {{target_engagement}}%

Format response as JSON:
{
    "posting_times": ["time1", "time2"],
    "hashtags": ["tag1", "tag2", ...],
    "thumbnail_style": "description",
    "caption_template": "template",
    "engagement_tactics": ["tactic1", "tactic2"]
}""",
    variables=["platform", "audience", "genre", "target_reach", "target_engagement"],
    description="Generates platform-specific content strategy",
    metadata={"max_tokens": 600, "temperature": 0.7}
)


NARRATION_STYLE_PROMPT = Prompt(
    id="narration_v1",
    name="Narration Style",
    type=PromptType.NARRATION,
    version="1.0",
    template="""You are a voice director for {{platform}} content.

Recommend narration style for this script:

SCRIPT:
{{script}}

Considerations:
- Audience: {{audience}}
- Genre: {{genre}}
- Tone: {{tone}}

Provide:
1. Voice type (male/female/neutral)
2. Pace (slow/medium/fast)
3. Emotion level (subdued/moderate/expressive)
4. Accent/dialect recommendation
5. Background music style

Format as JSON:
{
    "voice_type": "male/female/neutral",
    "pace": "slow/medium/fast",
    "emotion": "subdued/moderate/expressive",
    "accent": "recommendation",
    "music_style": "description"
}""",
    variables=["platform", "audience", "genre", "tone", "script"],
    description="Recommends narration style and voice settings",
    metadata={"max_tokens": 400, "temperature": 0.6}
)


# Prompt registry
PROMPT_REGISTRY: Dict[str, Prompt] = {
    "hook_v1": HOOK_GENERATION_PROMPT,
    "script_v1": SCRIPT_GENERATION_PROMPT,
    "critic_v1": CRITIC_PROMPT,
    "strategy_v1": STRATEGY_PROMPT,
    "narration_v1": NARRATION_STYLE_PROMPT,
}


def get_prompt(prompt_id: str) -> Optional[Prompt]:
    """Retrieve prompt by ID"""
    return PROMPT_REGISTRY.get(prompt_id)


def list_prompts(prompt_type: Optional[PromptType] = None) -> List[Prompt]:
    """List all prompts, optionally filtered by type"""
    prompts = list(PROMPT_REGISTRY.values())
    
    if prompt_type:
        prompts = [p for p in prompts if p.type == prompt_type]
    
    return prompts

"""
Hook Engine
Generates and scores video hooks for maximum viewer retention.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

from app.engines.base import BaseEngine, EngineInput, EngineOutput, EngineStatus, EngineDefinition
from app.engines.registry import EngineRegistry
from app.engines.hook_templates import (
    HookTemplate, HookStyle, HOOK_TEMPLATES,
    get_template, get_templates_by_style
)
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HookScore:
    """Effectiveness score breakdown"""
    curiosity: float = 0.0  # 30% weight
    relevance: float = 0.0  # 25% weight
    emotion: float = 0.0  # 20% weight
    clarity: float = 0.0  # 15% weight
    brevity: float = 0.0  # 10% weight
    
    @property
    def total(self) -> float:
        return (
            self.curiosity * 0.30 +
            self.relevance * 0.25 +
            self.emotion * 0.20 +
            self.clarity * 0.15 +
            self.brevity * 0.10
        )
    
    def to_dict(self) -> Dict:
        return {
            "curiosity": round(self.curiosity, 2),
            "relevance": round(self.relevance, 2),
            "emotion": round(self.emotion, 2),
            "clarity": round(self.clarity, 2),
            "brevity": round(self.brevity, 2),
            "total": round(self.total, 2)
        }


@dataclass
class GeneratedHook:
    """A generated hook with scoring"""
    text: str
    template_id: str
    score: HookScore
    recommended_visual: str = "text_overlay"
    recommended_tone: str = "energetic"
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "template_id": self.template_id,
            "score": self.score.to_dict(),
            "total_score": round(self.score.total, 2),
            "visual": self.recommended_visual,
            "tone": self.recommended_tone
        }


class HookEngine(BaseEngine):
    """Engine for generating viral video hooks"""
    
    def __init__(self):
        super().__init__(
            engine_id="hook_engine_v1",
            engine_type="hook",
            version="1.0.0"
        )
    
    def validate_input(self, input_data: EngineInput) -> Dict:
        errors = []
        params = input_data.parameters
        
        if not params.get("topic"):
            errors.append("Missing required parameter: topic")
        
        style = params.get("style")
        if style and style not in [s.value for s in HookStyle]:
            errors.append(f"Invalid style: {style}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Generate hooks for the given topic"""
        self.status = EngineStatus.RUNNING
        
        params = input_data.parameters
        topic = params.get("topic", "")
        style = HookStyle(params.get("style", "curiosity"))
        count = params.get("count", 5)
        
        # Generate hooks
        hooks = self._generate_hooks(topic, style, count)
        
        # Sort by score
        hooks.sort(key=lambda h: h.score.total, reverse=True)
        
        self.status = EngineStatus.COMPLETED
        
        return EngineOutput(
            job_id=input_data.job_id,
            engine_id=self.engine_id,
            status=EngineStatus.COMPLETED,
            primary_artifact=hooks[0].text if hooks else None,
            metadata={
                "hooks": [h.to_dict() for h in hooks],
                "topic": topic,
                "style": style.value,
                "best_hook": hooks[0].to_dict() if hooks else None
            },
            quality_scores={"hook_effectiveness": hooks[0].score.total if hooks else 0}
        )
    
    def validate_output(self, output: EngineOutput) -> Dict:
        errors = []
        if not output.primary_artifact:
            errors.append("No hook generated")
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _generate_hooks(self, topic: str, style: HookStyle, count: int) -> List[GeneratedHook]:
        """Generate multiple hook variations"""
        hooks = []
        
        # Get templates for style
        templates = get_templates_by_style(style)
        if not templates:
            templates = HOOK_TEMPLATES[:3]
        
        # Generate from each template
        for template in templates[:count]:
            hook_text = template.generate(topic)
            score = self._score_hook(hook_text, template)
            
            hooks.append(GeneratedHook(
                text=hook_text,
                template_id=template.id,
                score=score,
                recommended_visual=self._suggest_visual(style),
                recommended_tone=self._suggest_tone(style)
            ))
        
        return hooks
    
    def _score_hook(self, hook_text: str, template: HookTemplate) -> HookScore:
        """Score a hook's effectiveness"""
        # Base scores from template effectiveness
        base = template.effectiveness_baseline
        
        # Analyze hook text
        words = hook_text.split()
        word_count = len(words)
        
        # Brevity score (shorter is better for hooks)
        brevity = 1.0 if word_count <= 8 else max(0.5, 1.0 - (word_count - 8) * 0.05)
        
        # Clarity score (simple words)
        avg_word_len = sum(len(w) for w in words) / max(1, word_count)
        clarity = 1.0 if avg_word_len <= 5 else max(0.6, 1.0 - (avg_word_len - 5) * 0.1)
        
        return HookScore(
            curiosity=base + random.uniform(-0.1, 0.1),
            relevance=base + random.uniform(-0.1, 0.1),
            emotion=base + random.uniform(-0.1, 0.1),
            clarity=clarity,
            brevity=brevity
        )
    
    def _suggest_visual(self, style: HookStyle) -> str:
        """Suggest visual type for hook style"""
        visuals = {
            HookStyle.CURIOSITY: "zoom_in",
            HookStyle.CONTRARIAN: "shake_effect",
            HookStyle.FEAR: "flash_red",
            HookStyle.SHOCKING: "glitch_effect",
            HookStyle.STORY: "fade_in",
            HookStyle.QUESTION: "text_overlay"
        }
        return visuals.get(style, "text_overlay")
    
    def _suggest_tone(self, style: HookStyle) -> str:
        """Suggest voice tone for hook style"""
        tones = {
            HookStyle.CURIOSITY: "intriguing",
            HookStyle.CONTRARIAN: "confident",
            HookStyle.FEAR: "urgent",
            HookStyle.SECRET: "whispered",
            HookStyle.CHALLENGE: "provocative"
        }
        return tones.get(style, "energetic")


# Create and register engine
hook_engine = HookEngine()
EngineRegistry.register(
    hook_engine,
    EngineDefinition(
        engine_id="hook_engine_v1",
        engine_type="hook",
        version="1.0.0",
        capabilities=["generate", "score", "variations"],
        required_inputs=["topic"],
        optional_inputs=["style", "count"],
        output_types=["hook_text", "hook_scores"]
    )
)

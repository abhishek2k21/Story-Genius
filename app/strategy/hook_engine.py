"""
Hook Engine
Generates, classifies, and scores multiple hook variants for maximum first-3-second impact.
"""
import json
import sys
from pathlib import Path
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.logging import get_logger

logger = get_logger(__name__)


class HookType(str, Enum):
    """Types of hooks optimized for short-form content."""
    PATTERN_INTERRUPT = "pattern_interrupt"     # Breaks expected pattern
    QUESTION_GAP = "question_gap"               # Creates curiosity gap
    SHOCK_STATEMENT = "shock_statement"         # Surprising fact/claim
    VISUAL_CONTRADICTION = "visual_contradiction"  # "Wait, what?"
    DIRECT_ADDRESS = "direct_address"           # "You won't believe..."
    MYSTERY_TEASE = "mystery_tease"             # Hints at secret


@dataclass
class Hook:
    """A single hook variant."""
    text: str
    hook_type: HookType
    visual_prompt: str
    clarity_score: float = 0.0
    curiosity_score: float = 0.0
    total_score: float = 0.0
    rank: int = 0
    

@dataclass
class HookResult:
    """Result of hook generation and selection."""
    selected_hook: Hook
    all_hooks: List[Hook]
    generation_time: float = 0.0


class HookEngine:
    """
    Generates and evaluates multiple hook variants for short-form content.
    Selects the best hook based on clarity and curiosity scores.
    """
    
    HOOK_TYPE_PROMPTS = {
        HookType.PATTERN_INTERRUPT: "Start with something unexpected that breaks the viewer's mental pattern",
        HookType.QUESTION_GAP: "Open with a question that creates immediate curiosity",
        HookType.SHOCK_STATEMENT: "Begin with a surprising fact or bold claim",
        HookType.VISUAL_CONTRADICTION: "Describe a visual that seems wrong or contradictory",
        HookType.DIRECT_ADDRESS: "Speak directly to the viewer with urgency",
        HookType.MYSTERY_TEASE: "Hint at a secret or hidden knowledge"
    }
    
    def __init__(self):
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from story_genius.llm.vertex_wrapper import VertexLLM
                self._llm = VertexLLM()
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise
        return self._llm
    
    def generate_hooks(
        self,
        topic: str,
        audience: str,
        platform: str = "youtube_shorts",
        count: int = 5
    ) -> List[Hook]:
        """
        Generate multiple hook variants for a topic.
        
        Args:
            topic: Content topic or theme
            audience: Target audience (e.g., kids_india)
            platform: Target platform
            count: Number of hooks to generate
            
        Returns:
            List of Hook objects with scores
        """
        logger.info(f"Generating {count} hook variants for: {topic}")
        
        llm = self._get_llm()
        
        # Select hook types to try
        hook_types = list(HookType)[:count] if count <= len(HookType) else list(HookType)
        
        prompt = f"""
        You are a viral short-form content expert. Generate {count} different hook variants for a {platform} video.
        
        Topic: {topic}
        Target Audience: {audience}
        
        For each hook, use a DIFFERENT hook type:
        1. PATTERN_INTERRUPT - Break expectations immediately
        2. QUESTION_GAP - Create curiosity with a question
        3. SHOCK_STATEMENT - Start with surprising fact
        4. VISUAL_CONTRADICTION - Describe paradoxical visual
        5. DIRECT_ADDRESS - Speak urgently to viewer
        
        Requirements:
        - Each hook text must be MAX 10 words
        - Must grab attention in first 2 seconds
        - Match the audience (simple language for kids)
        
        Output ONLY valid JSON array:
        [
            {{
                "text": "Wait, this dinosaur is STILL alive?",
                "hook_type": "shock_statement",
                "visual": "Close-up of mysterious eye opening"
            }},
            ...
        ]
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            hooks = []
            for i, item in enumerate(data[:count]):
                try:
                    hook_type = HookType(item.get("hook_type", "pattern_interrupt").lower())
                except ValueError:
                    hook_type = HookType.PATTERN_INTERRUPT
                
                hook = Hook(
                    text=item.get("text", ""),
                    hook_type=hook_type,
                    visual_prompt=item.get("visual", "")
                )
                hooks.append(hook)
            
            logger.info(f"Generated {len(hooks)} hooks")
            return hooks
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hooks: {e}")
            # Return a default hook
            return [Hook(
                text=f"You won't believe what happens next!",
                hook_type=HookType.DIRECT_ADDRESS,
                visual_prompt="Exciting opening shot"
            )]
        except Exception as e:
            logger.error(f"Hook generation failed: {e}")
            raise
    
    def score_hook(self, hook: Hook, audience: str = "general") -> Hook:
        """
        Score a hook on clarity and curiosity.
        
        Args:
            hook: Hook to score
            audience: Target audience for context
            
        Returns:
            Hook with scores filled in
        """
        llm = self._get_llm()
        
        prompt = f"""
        Rate this short-form video hook for a {audience} audience.
        
        Hook: "{hook.text}"
        Hook Type: {hook.hook_type.value}
        
        Score from 0.0 to 1.0:
        
        1. CLARITY (0-1): Is the message instantly clear?
           - Can a viewer understand it in 1 second?
           - No confusion or ambiguity?
        
        2. CURIOSITY (0-1): Does it make viewers NEED to keep watching?
           - Creates an information gap?
           - Triggers "wait, what?" response?
        
        Output ONLY valid JSON:
        {{"clarity": 0.X, "curiosity": 0.X}}
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            hook.clarity_score = float(data.get("clarity", 0.5))
            hook.curiosity_score = float(data.get("curiosity", 0.5))
            
            # Total score: curiosity weighted higher for shorts
            hook.total_score = (hook.clarity_score * 0.4) + (hook.curiosity_score * 0.6)
            
            logger.debug(f"Hook scored: {hook.total_score:.2f} (clarity={hook.clarity_score}, curiosity={hook.curiosity_score})")
            return hook
            
        except Exception as e:
            logger.warning(f"Hook scoring failed, using defaults: {e}")
            hook.clarity_score = 0.5
            hook.curiosity_score = 0.5
            hook.total_score = 0.5
            return hook
    
    def score_all_hooks(self, hooks: List[Hook], audience: str = "general") -> List[Hook]:
        """Score all hooks and rank them."""
        scored_hooks = [self.score_hook(hook, audience) for hook in hooks]
        
        # Sort by total score (descending)
        scored_hooks.sort(key=lambda h: h.total_score, reverse=True)
        
        # Assign ranks
        for i, hook in enumerate(scored_hooks):
            hook.rank = i + 1
        
        return scored_hooks
    
    def select_best_hook(self, hooks: List[Hook]) -> Hook:
        """Select the highest-scoring hook."""
        if not hooks:
            raise ValueError("No hooks to select from")
        
        # Already sorted by score if score_all_hooks was called
        best = max(hooks, key=lambda h: h.total_score)
        logger.info(f"Selected hook (score={best.total_score:.2f}): {best.text[:50]}...")
        return best
    
    def generate_and_select(
        self,
        topic: str,
        audience: str,
        platform: str = "youtube_shorts",
        count: int = 5
    ) -> HookResult:
        """
        Complete workflow: generate, score, and select best hook.
        
        Args:
            topic: Content topic
            audience: Target audience
            platform: Target platform
            count: Number of variants to generate
            
        Returns:
            HookResult with selected hook and all variants
        """
        import time
        start = time.time()
        
        # Generate hooks
        hooks = self.generate_hooks(topic, audience, platform, count)
        
        # Score all hooks
        scored_hooks = self.score_all_hooks(hooks, audience)
        
        # Select best
        best_hook = self.select_best_hook(scored_hooks)
        
        elapsed = time.time() - start
        
        # Log rankings
        logger.info("Hook Rankings:")
        for hook in scored_hooks:
            logger.info(f"  #{hook.rank}: {hook.total_score:.2f} [{hook.hook_type.value}] {hook.text[:40]}...")
        
        return HookResult(
            selected_hook=best_hook,
            all_hooks=scored_hooks,
            generation_time=elapsed
        )
    
    def hook_to_scene_dict(self, hook: Hook) -> dict:
        """Convert hook to scene format for story integration."""
        return {
            "start_sec": 0,
            "end_sec": 2,
            "purpose": "hook",
            "narration_text": hook.text,
            "visual_prompt": hook.visual_prompt,
            "hook_type": hook.hook_type.value,
            "hook_score": hook.total_score
        }

"""
Enhanced Critic Service (Week 2)
LLM-based quality scoring with emotion alignment and targeted retries.
"""
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.models import Story, CriticScore
from app.core.config import settings
from app.core.logging import get_logger
from app.intelligence.emotion_curves import EmotionCurveService, Emotion

logger = get_logger(__name__)


class RetryTarget:
    """Targeted retry options."""
    HOOK_ONLY = "hook_only"
    ENDING_ONLY = "ending_only"
    FULL = "full"


class CriticService:
    """
    Enhanced LLM-based critic for Week 2.
    Includes emotion alignment scoring and targeted retry suggestions.
    """
    
    def __init__(self):
        self._llm = None
        self.retry_threshold = settings.CRITIC_RETRY_THRESHOLD
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from story_genius.llm.vertex_wrapper import VertexLLM
                self._llm = VertexLLM()
            except Exception as e:
                logger.error(f"Failed to initialize LLM for critic: {e}")
                raise
        return self._llm
    
    def score_content(
        self,
        story: Story,
        platform: str = "youtube_shorts",
        expected_curve_id: str = None
    ) -> CriticScore:
        """
        Score the generated content with emotion alignment.
        
        Args:
            story: Generated story with scenes
            platform: Target platform
            expected_curve_id: Expected emotion curve for alignment check
            
        Returns:
            CriticScore with individual scores, emotion alignment, and retry target
        """
        logger.info(f"Scoring story {story.id[:8]} for {platform}")
        
        llm = self._get_llm()
        
        # Build scene summary for evaluation
        scene_summary = "\n".join([
            f"Scene {s.id} ({s.start_sec}-{s.end_sec}s, {s.purpose.value}): {s.narration_text}"
            for s in story.scenes
        ])
        
        # Get expected emotion curve if provided
        curve_guidance = ""
        if expected_curve_id:
            curve = EmotionCurveService.get_curve(expected_curve_id)
            if curve:
                curve_guidance = f"\nExpected Emotion Flow: {curve.to_prompt_guidance()}"
        
        prompt = f"""
        You are a TikTok/YouTube Shorts content expert. Evaluate this short-form video script:
        
        Platform: {platform}
        Total Duration: {story.total_duration} seconds
        {curve_guidance}
        
        SCENES:
        {scene_summary}
        
        Score each criterion from 0.0 to 1.0:
        
        1. HOOK STRENGTH (0-1): Does the first scene grab attention immediately?
           - 1.0: Pattern interrupt, immediate curiosity, can't look away
           - 0.5: Decent start but not compelling
           - 0.0: Boring, slow, viewers will scroll away
        
        2. PACING (0-1): Is the content rhythm optimized for short attention spans?
           - 1.0: Quick cuts, no dead air, constant engagement
           - 0.5: Some slow moments but generally okay
           - 0.0: Too slow, loses attention
        
        3. LOOP EFFECTIVENESS (0-1): Does the ending encourage replay?
           - 1.0: Ends with cliffhanger, question, or mid-action cut
           - 0.5: Ends okay but not compelling to rewatch
           - 0.0: Ends flat, no reason to replay
        
        4. EMOTION ALIGNMENT (0-1): Does the emotional flow feel intentional?
           - 1.0: Clear emotional journey, each scene evokes right feeling
           - 0.5: Some emotional variation but not cohesive
           - 0.0: Flat, no emotional progression
        
        Also determine what would best fix any issues:
        - "hook_only" if only the first scene needs work
        - "ending_only" if only the last scene needs work
        - "full" if major rewrite needed
        - null if content is good
        
        Output ONLY valid JSON:
        {{
            "hook_score": 0.X,
            "pacing_score": 0.X,
            "loop_score": 0.X,
            "emotion_alignment": 0.X,
            "retry_target": "hook_only" or "ending_only" or "full" or null,
            "feedback": "Brief improvement suggestions"
        }}
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            hook = float(data.get("hook_score", 0.5))
            pacing = float(data.get("pacing_score", 0.5))
            loop = float(data.get("loop_score", 0.5))
            emotion = float(data.get("emotion_alignment", 0.5))
            
            # Calculate total: hook still most important, but emotion matters now
            total = (hook * 0.35) + (pacing * 0.25) + (loop * 0.25) + (emotion * 0.15)
            
            verdict = "accept" if total >= self.retry_threshold else "retry"
            retry_target = data.get("retry_target") if verdict == "retry" else None
            
            score = CriticScore(
                hook_score=hook,
                pacing_score=pacing,
                loop_score=loop,
                emotion_alignment=emotion,
                total_score=round(total, 2),
                verdict=verdict,
                retry_target=retry_target,
                feedback=data.get("feedback", "")
            )
            
            logger.info(f"Critic: {score.total_score} ({score.verdict})"
                       + (f" → retry {score.retry_target}" if score.retry_target else ""))
            return score
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse critic response: {e}")
            return CriticScore(
                hook_score=0.5,
                pacing_score=0.5,
                loop_score=0.5,
                emotion_alignment=0.5,
                total_score=0.5,
                verdict="accept",
                retry_target=None,
                feedback="Scoring error, defaulting to accept"
            )
        except Exception as e:
            logger.error(f"Critic evaluation failed: {e}")
            raise
    
    def should_retry(self, score: CriticScore) -> bool:
        """Check if content should be regenerated."""
        return score.verdict == "retry"
    
    def get_retry_target(self, score: CriticScore) -> Optional[str]:
        """Get what specifically should be retried."""
        return score.retry_target
    
    def analyze_weakest_area(self, score: CriticScore) -> Tuple[str, float]:
        """Find the weakest scoring area."""
        scores = {
            "hook": score.hook_score,
            "pacing": score.pacing_score,
            "loop": score.loop_score,
            "emotion": score.emotion_alignment
        }
        weakest = min(scores, key=scores.get)
        return weakest, scores[weakest]

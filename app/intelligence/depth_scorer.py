"""
Depth Scorer Module
Ranks ideas by conceptual depth, robustness, and long-term value - not just virality.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DepthScore:
    """Multi-dimensional depth score for an idea."""
    idea: str
    depth: float              # Conceptual depth (0.0-1.0)
    robustness: float         # How well it holds up to scrutiny (0.0-1.0)
    novelty: float            # Uniqueness in market (0.0-1.0)
    long_term_value: float    # Sustainable value over time (0.0-1.0)
    overall_score: float      # Weighted composite score
    rank_explanation: str     # Why it got this score

    def to_dict(self) -> Dict:
        return {
            "idea": self.idea,
            "depth": self.depth,
            "robustness": self.robustness,
            "novelty": self.novelty,
            "long_term_value": self.long_term_value,
            "overall_score": self.overall_score,
            "rank_explanation": self.rank_explanation
        }


class DepthScorer:
    """
    Scores ideas on dimensions that matter for lasting success.
    This is a taste filter for thinking, not aesthetics.
    """
    
    SCORING_PROMPT = """You are an expert evaluator who assesses ideas based on depth and sustainability, NOT just virality or shock value.

Score the following idea on these dimensions (0.0 to 1.0 each):

1. DEPTH (0.0-1.0): Conceptual richness. Does it have layers? Is it thought-provoking?
2. ROBUSTNESS (0.0-1.0): How well does it hold up to scrutiny? Is it logically sound?
3. NOVELTY (0.0-1.0): How unique is this in the current landscape? Not just different, but meaningfully new.
4. LONG_TERM_VALUE (0.0-1.0): Will this still be valuable in 6 months? 1 year? Is it timeless or trendy?

IDEA TO SCORE: {idea}

Respond in this exact JSON format:
{{
  "depth": 0.85,
  "robustness": 0.72,
  "novelty": 0.68,
  "long_term_value": 0.81,
  "overall_score": 0.77,
  "rank_explanation": "Brief explanation of why these scores were assigned and what makes this idea strong or weak."
}}

The overall_score should be a weighted average favoring depth and long_term_value.
Be honest and precise. High scores should be rare."""

    # Weights for composite score
    WEIGHTS = {
        "depth": 0.30,
        "robustness": 0.25,
        "novelty": 0.15,
        "long_term_value": 0.30
    }

    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("DepthScorer initialized with Gemini")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}. Using mock mode.")
            self.client = None

    def score_idea_depth(self, idea_text: str) -> DepthScore:
        """
        Score an idea on depth and related dimensions.
        
        Args:
            idea_text: The idea to score
            
        Returns:
            DepthScore with multi-dimensional assessment
        """
        logger.info(f"Scoring depth for: {idea_text[:50]}...")
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.SCORING_PROMPT.format(idea=idea_text),
                    config=types.GenerateContentConfig(
                        temperature=0.5,  # Lower temp for more consistent scoring
                        max_output_tokens=1024,
                    )
                )
                result_text = response.text
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    raise ValueError("No JSON found in response")
                
                # Recalculate overall score with our weights for consistency
                depth = result.get("depth", 0.5)
                robustness = result.get("robustness", 0.5)
                novelty = result.get("novelty", 0.5)
                long_term = result.get("long_term_value", 0.5)
                
                overall = (
                    depth * self.WEIGHTS["depth"] +
                    robustness * self.WEIGHTS["robustness"] +
                    novelty * self.WEIGHTS["novelty"] +
                    long_term * self.WEIGHTS["long_term_value"]
                )
                    
                return DepthScore(
                    idea=idea_text,
                    depth=depth,
                    robustness=robustness,
                    novelty=novelty,
                    long_term_value=long_term,
                    overall_score=round(overall, 2),
                    rank_explanation=result.get("rank_explanation", "")
                )
            except Exception as e:
                logger.error(f"LLM depth scoring failed: {e}")
                return self._mock_score(idea_text)
        else:
            return self._mock_score(idea_text)

    def _mock_score(self, idea_text: str) -> DepthScore:
        """Fallback mock scoring for testing."""
        return DepthScore(
            idea=idea_text,
            depth=0.65,
            robustness=0.60,
            novelty=0.55,
            long_term_value=0.70,
            overall_score=0.64,
            rank_explanation="Mock score: Moderate depth with reasonable long-term potential. Needs refinement for robustness."
        )

    def rank_ideas(self, ideas: List[str]) -> List[DepthScore]:
        """
        Score and rank multiple ideas by overall score.
        
        Args:
            ideas: List of ideas to score and rank
            
        Returns:
            List of DepthScores sorted by overall_score (descending)
        """
        scores = [self.score_idea_depth(idea) for idea in ideas]
        return sorted(scores, key=lambda s: s.overall_score, reverse=True)


# Singleton instance
_scorer = None

def get_depth_scorer() -> DepthScorer:
    """Get global depth scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = DepthScorer()
    return _scorer


def score_idea_depth(idea_text: str) -> Dict:
    """
    Convenience function to score an idea's depth.
    
    Args:
        idea_text: The idea to score
        
    Returns:
        Dictionary with depth scores
    """
    scorer = get_depth_scorer()
    score = scorer.score_idea_depth(idea_text)
    return score.to_dict()

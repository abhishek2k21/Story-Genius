"""
Synthesis Engine Module
The most powerful module - takes raw ideas and evolves them into refined, defensible versions.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SynthesisResult:
    """Result of idea synthesis."""
    original_idea: str
    refined_idea: str
    improvements_made: List[str]
    assumptions_addressed: List[str]
    counters_neutralized: List[str]
    confidence_boost: float  # How much stronger the idea became (0.0-1.0 increase)

    def to_dict(self) -> Dict:
        return {
            "original_idea": self.original_idea,
            "refined_idea": self.refined_idea,
            "improvements_made": self.improvements_made,
            "assumptions_addressed": self.assumptions_addressed,
            "counters_neutralized": self.counters_neutralized,
            "confidence_boost": self.confidence_boost
        }


class SynthesisEngine:
    """
    Synthesizes stronger ideas from raw input and analysis.
    Doesn't just critique - it evolves and improves.
    """
    
    SYNTHESIS_PROMPT = """You are an expert at taking raw ideas and making them bulletproof.

Given an original idea AND the analysis of its weaknesses, create a REFINED version that:
1. Addresses the fragile assumptions
2. Neutralizes the strongest counter-arguments
3. Accounts for negative second-order effects
4. Maintains what was strong about the original

ORIGINAL IDEA:
{original}

HIDDEN ASSUMPTIONS FOUND:
{assumptions}

COUNTER-ARGUMENTS TO ADDRESS:
{counters}

SECOND-ORDER RISKS:
{second_order}

Create a refined, sharper, more defensible version of this idea.

Respond in this exact JSON format:
{{
  "refined_idea": "The improved, evolved version of the idea that you would actually stand behind.",
  "improvements_made": [
    "Specific improvement 1",
    "Specific improvement 2"
  ],
  "assumptions_addressed": [
    "Which fragile assumptions were fixed"
  ],
  "counters_neutralized": [
    "Which counter-arguments were addressed"
  ],
  "confidence_boost": 0.25
}}

The confidence_boost should be 0.0-1.0 representing how much stronger the refined idea is.
The refined idea should be concrete and actionable, not generic."""

    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("SynthesisEngine initialized with Gemini")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}. Using mock mode.")
            self.client = None

    def synthesize_stronger_idea(
        self,
        original: str,
        assumptions: List[str] = None,
        counters: List[str] = None,
        second_order: List[str] = None
    ) -> SynthesisResult:
        """
        Synthesize a stronger version of an idea using analysis insights.
        
        Args:
            original: The original idea
            assumptions: Hidden assumptions to address
            counters: Counter-arguments to neutralize
            second_order: Second-order effects to account for
            
        Returns:
            SynthesisResult with the refined idea and improvements
        """
        logger.info(f"Synthesizing stronger version of: {original[:50]}...")
        
        assumptions = assumptions or []
        counters = counters or []
        second_order = second_order or []
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.SYNTHESIS_PROMPT.format(
                        original=original,
                        assumptions="\n".join(f"- {a}" for a in assumptions) or "None provided",
                        counters="\n".join(f"- {c}" for c in counters) or "None provided",
                        second_order="\n".join(f"- {s}" for s in second_order) or "None provided"
                    ),
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=1500,
                    )
                )
                result_text = response.text
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    raise ValueError("No JSON found in response")
                    
                return SynthesisResult(
                    original_idea=original,
                    refined_idea=result.get("refined_idea", original),
                    improvements_made=result.get("improvements_made", []),
                    assumptions_addressed=result.get("assumptions_addressed", []),
                    counters_neutralized=result.get("counters_neutralized", []),
                    confidence_boost=result.get("confidence_boost", 0.1)
                )
            except Exception as e:
                logger.error(f"LLM synthesis failed: {e}")
                return self._mock_synthesis(original)
        else:
            return self._mock_synthesis(original)

    def _mock_synthesis(self, original: str) -> SynthesisResult:
        """Fallback mock synthesis for testing."""
        refined = f"{original} — refined with clearer value proposition and sustainable execution path."
        return SynthesisResult(
            original_idea=original,
            refined_idea=refined,
            improvements_made=[
                "Added clearer value proposition",
                "Included sustainability considerations",
                "Addressed competitive differentiation"
            ],
            assumptions_addressed=[
                "Removed assumption about audience behavior"
            ],
            counters_neutralized=[
                "Added evidence against novelty-only criticism"
            ],
            confidence_boost=0.20
        )


# Singleton instance
_engine = None

def get_synthesis_engine() -> SynthesisEngine:
    """Get global synthesis engine instance."""
    global _engine
    if _engine is None:
        _engine = SynthesisEngine()
    return _engine


def synthesize_stronger_idea(
    original: str,
    assumptions: List[str] = None,
    counters: List[str] = None,
    second_order: List[str] = None
) -> str:
    """
    Convenience function to synthesize a stronger idea.
    
    Args:
        original: The original idea
        assumptions: Hidden assumptions
        counters: Counter-arguments
        second_order: Second-order effects
        
    Returns:
        The refined idea as a string
    """
    engine = get_synthesis_engine()
    result = engine.synthesize_stronger_idea(original, assumptions, counters, second_order)
    return result.refined_idea

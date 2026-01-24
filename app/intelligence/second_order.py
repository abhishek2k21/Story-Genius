"""
Second-Order Consequence Checker Module
Analyzes what happens AFTER an idea works - the ripple effects most miss.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SecondOrderAnalysis:
    """Result of second-order effect analysis."""
    idea: str
    second_order_effects: List[str]
    positive_effects: List[str]
    negative_effects: List[str]
    long_term_risk_score: float  # 0.0-1.0, higher = more risky
    audience_conditioning: str  # How this shapes audience expectations

    def to_dict(self) -> Dict:
        return {
            "idea": self.idea,
            "second_order_effects": self.second_order_effects,
            "positive_effects": self.positive_effects,
            "negative_effects": self.negative_effects,
            "long_term_risk_score": self.long_term_risk_score,
            "audience_conditioning": self.audience_conditioning
        }


class SecondOrderChecker:
    """
    Analyzes consequences beyond immediate success.
    Focuses on audience conditioning, long-term effects, and unintended consequences.
    """
    
    ANALYSIS_PROMPT = """You are an expert strategist who thinks in second and third-order effects.

When given an idea that "works," you ask: "What happens AFTER it works? What does success create?"

Analyze the following idea for its downstream consequences:

IDEA: {idea}

Consider:
- Audience conditioning (how does this shape future expectations?)
- Long-term sustainability (can this approach be maintained?)
- Unintended consequences (what unexpected effects might emerge?)
- Competitive dynamics (how will others respond?)

Respond in this exact JSON format:
{{
  "second_order_effects": [
    "Effect 1 that follows from success",
    "Effect 2 that follows from success",
    "Effect 3 that follows from success"
  ],
  "positive_effects": [
    "Beneficial downstream consequence"
  ],
  "negative_effects": [
    "Harmful downstream consequence"
  ],
  "long_term_risk_score": 0.4,
  "audience_conditioning": "Description of how this shapes audience expectations over time"
}}

The risk score should be 0.0-1.0 where 1.0 means high long-term risk.
Think beyond the obvious first-order outcomes."""

    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("SecondOrderChecker initialized with Gemini")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}. Using mock mode.")
            self.client = None

    def analyze_second_order_effects(self, idea_text: str) -> SecondOrderAnalysis:
        """
        Analyze second-order consequences of an idea.
        
        Args:
            idea_text: The idea to analyze for downstream effects
            
        Returns:
            SecondOrderAnalysis with consequence mapping
        """
        logger.info(f"Analyzing second-order effects for: {idea_text[:50]}...")
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.ANALYSIS_PROMPT.format(idea=idea_text),
                    config=types.GenerateContentConfig(
                        temperature=0.7,
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
                    
                return SecondOrderAnalysis(
                    idea=idea_text,
                    second_order_effects=result.get("second_order_effects", []),
                    positive_effects=result.get("positive_effects", []),
                    negative_effects=result.get("negative_effects", []),
                    long_term_risk_score=result.get("long_term_risk_score", 0.5),
                    audience_conditioning=result.get("audience_conditioning", "")
                )
            except Exception as e:
                logger.error(f"LLM second-order analysis failed: {e}")
                return self._mock_analysis(idea_text)
        else:
            return self._mock_analysis(idea_text)

    def _mock_analysis(self, idea_text: str) -> SecondOrderAnalysis:
        """Fallback mock analysis for testing."""
        return SecondOrderAnalysis(
            idea=idea_text,
            second_order_effects=[
                "Audience may feel manipulated over time",
                "Retention improves short-term, trust drops long-term",
                "Expectations escalate, making future content harder"
            ],
            positive_effects=[
                "Builds initial momentum and visibility"
            ],
            negative_effects=[
                "Creates unsustainable content treadmill",
                "Trains audience to expect constant novelty"
            ],
            long_term_risk_score=0.65,
            audience_conditioning="This approach trains audiences to expect escalating intensity, which becomes harder to maintain."
        )


# Singleton instance
_checker = None

def get_second_order_checker() -> SecondOrderChecker:
    """Get global second-order checker instance."""
    global _checker
    if _checker is None:
        _checker = SecondOrderChecker()
    return _checker


def analyze_second_order_effects(idea_text: str) -> List[str]:
    """
    Convenience function to analyze second-order effects.
    
    Args:
        idea_text: The idea to analyze
        
    Returns:
        List of second-order effects
    """
    checker = get_second_order_checker()
    analysis = checker.analyze_second_order_effects(idea_text)
    return analysis.second_order_effects

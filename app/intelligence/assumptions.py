"""
Assumption Extractor Module
Exposes hidden, unstated, and fragile assumptions in any idea.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AssumptionAnalysis:
    """Result of assumption extraction."""
    idea: str
    assumptions: List[str]
    fragile_assumptions: List[str]  # Assumptions most likely to be wrong
    confidence_scores: Dict[str, float]  # Assumption -> confidence it's valid

    def to_dict(self) -> Dict:
        return {
            "idea": self.idea,
            "assumptions": self.assumptions,
            "fragile_assumptions": self.fragile_assumptions,
            "confidence_scores": self.confidence_scores
        }


class AssumptionExtractor:
    """
    Extracts hidden, unstated, and fragile assumptions from ideas.
    Uses LLM to surface unconscious beliefs embedded in any statement.
    """
    
    EXTRACTION_PROMPT = """You are an expert critical thinker specializing in exposing hidden assumptions.

Given the following idea or statement, identify:
1. Hidden assumptions - beliefs that are taken for granted but not explicitly stated
2. Unstated beliefs - presuppositions the idea relies on
3. Fragile premises - assumptions most likely to be wrong or context-dependent
4. For each assumption, estimate a confidence score (0.0-1.0) of how likely it is to be valid

IDEA: {idea}

Respond in this exact JSON format:
{{
  "assumptions": [
    "Hidden assumption 1",
    "Hidden assumption 2",
    ...
  ],
  "fragile_assumptions": [
    "Most fragile assumption",
    ...
  ],
  "confidence_scores": {{
    "Assumption 1": 0.7,
    "Assumption 2": 0.4,
    ...
  }}
}}

Be thorough but concise. Focus on the most impactful hidden beliefs."""

    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("AssumptionExtractor initialized with Gemini")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}. Using mock mode.")
            self.client = None

    def extract_assumptions(self, idea_text: str) -> AssumptionAnalysis:
        """
        Extract hidden assumptions from an idea.
        
        Args:
            idea_text: The idea or statement to analyze
            
        Returns:
            AssumptionAnalysis with extracted assumptions
        """
        logger.info(f"Extracting assumptions from: {idea_text[:50]}...")
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.EXTRACTION_PROMPT.format(idea=idea_text),
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1024,
                    )
                )
                result_text = response.text
                # Parse JSON from response
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    raise ValueError("No JSON found in response")
                    
                return AssumptionAnalysis(
                    idea=idea_text,
                    assumptions=result.get("assumptions", []),
                    fragile_assumptions=result.get("fragile_assumptions", []),
                    confidence_scores=result.get("confidence_scores", {})
                )
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}")
                return self._mock_extraction(idea_text)
        else:
            return self._mock_extraction(idea_text)

    def _mock_extraction(self, idea_text: str) -> AssumptionAnalysis:
        """Fallback mock extraction for testing."""
        mock_assumptions = [
            "The target audience will find this relevant",
            "Current trends support this approach",
            "Competition hasn't already saturated this space",
            "Execution quality can match the concept"
        ]
        return AssumptionAnalysis(
            idea=idea_text,
            assumptions=mock_assumptions,
            fragile_assumptions=[mock_assumptions[2]],
            confidence_scores={a: 0.6 for a in mock_assumptions}
        )


# Singleton instance
_extractor = None

def get_assumption_extractor() -> AssumptionExtractor:
    """Get global assumption extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = AssumptionExtractor()
    return _extractor


def extract_assumptions(idea_text: str) -> List[str]:
    """
    Convenience function to extract assumptions from an idea.
    
    Args:
        idea_text: The idea to analyze
        
    Returns:
        List of hidden assumptions
    """
    extractor = get_assumption_extractor()
    analysis = extractor.extract_assumptions(idea_text)
    return analysis.assumptions

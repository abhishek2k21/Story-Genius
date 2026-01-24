"""
Counter-Argument Engine Module
Generates the strongest case against any idea - not strawmen, but real opposition.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CounterAnalysis:
    """Result of counter-argument generation."""
    idea: str
    counter_arguments: List[str]
    strongest_counter: str
    weaknesses_exposed: List[str]
    survival_likelihood: float  # 0.0-1.0, how likely the idea survives critique

    def to_dict(self) -> Dict:
        return {
            "idea": self.idea,
            "counter_arguments": self.counter_arguments,
            "strongest_counter": self.strongest_counter,
            "weaknesses_exposed": self.weaknesses_exposed,
            "survival_likelihood": self.survival_likelihood
        }


class CounterArgumentEngine:
    """
    Generates the best opposing views to any idea.
    Designed to steelman opposition, not strawman it.
    """
    
    COUNTER_PROMPT = """You are a world-class debater tasked with making the STRONGEST case against an idea.

Your job is NOT to agree or be nice. Your job is to find the most compelling, intelligent opposition.

Do not create strawman arguments. Create steelman counterarguments that would be made by a smart critic.

IDEA TO OPPOSE: {idea}

Respond in this exact JSON format:
{{
  "counter_arguments": [
    "Strong counter-argument 1",
    "Strong counter-argument 2",
    "Strong counter-argument 3"
  ],
  "strongest_counter": "The single most devastating argument against this idea",
  "weaknesses_exposed": [
    "Fundamental weakness 1",
    "Fundamental weakness 2"
  ],
  "survival_likelihood": 0.65
}}

The survival_likelihood should be 0.0-1.0 representing how likely the idea survives your critique.
Be ruthlessly honest but fair."""

    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "gemini-2.0-flash-001"
            logger.info("CounterArgumentEngine initialized with Gemini")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}. Using mock mode.")
            self.client = None

    def generate_counter_arguments(self, idea_text: str) -> CounterAnalysis:
        """
        Generate the strongest counter-arguments against an idea.
        
        Args:
            idea_text: The idea to challenge
            
        Returns:
            CounterAnalysis with opposing arguments
        """
        logger.info(f"Generating counter-arguments for: {idea_text[:50]}...")
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.COUNTER_PROMPT.format(idea=idea_text),
                    config=types.GenerateContentConfig(
                        temperature=0.8,
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
                    
                return CounterAnalysis(
                    idea=idea_text,
                    counter_arguments=result.get("counter_arguments", []),
                    strongest_counter=result.get("strongest_counter", ""),
                    weaknesses_exposed=result.get("weaknesses_exposed", []),
                    survival_likelihood=result.get("survival_likelihood", 0.5)
                )
            except Exception as e:
                logger.error(f"LLM counter generation failed: {e}")
                return self._mock_counter(idea_text)
        else:
            return self._mock_counter(idea_text)

    def _mock_counter(self, idea_text: str) -> CounterAnalysis:
        """Fallback mock counter-arguments for testing."""
        return CounterAnalysis(
            idea=idea_text,
            counter_arguments=[
                "It relies on shock value but lacks lasting substance",
                "The novelty wears off quickly after first exposure",
                "It may cause early drop-off despite initial clicks",
                "Competitors can easily replicate the approach"
            ],
            strongest_counter="The execution complexity may not justify the marginal engagement increase",
            weaknesses_exposed=[
                "Relies heavily on novelty",
                "No sustainable competitive advantage"
            ],
            survival_likelihood=0.55
        )


# Singleton instance
_engine = None

def get_counter_engine() -> CounterArgumentEngine:
    """Get global counter-argument engine instance."""
    global _engine
    if _engine is None:
        _engine = CounterArgumentEngine()
    return _engine


def generate_counter_arguments(idea_text: str) -> List[str]:
    """
    Convenience function to generate counter-arguments.
    
    Args:
        idea_text: The idea to challenge
        
    Returns:
        List of counter-arguments
    """
    engine = get_counter_engine()
    analysis = engine.generate_counter_arguments(idea_text)
    return analysis.counter_arguments

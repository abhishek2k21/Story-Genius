"""
Week 17 - Contract-Based Generator
Generates content strictly following the contract.
"""
import json
from typing import Dict, Optional
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.contract import GenerationContract, ContentMode
from app.core.model_router import get_model_router, TaskType
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContractOutput:
    """Output from contract-based generation."""
    script: str
    segments: list
    contract_summary: dict
    model_used: str


class ContractGenerator:
    """
    Generates content based on the contract.
    The contract is the ONE source of truth.
    """
    
    def __init__(self, project_id: str = "winged-precept-458206-j1", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.router = get_model_router()
        
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            logger.info("ContractGenerator initialized")
        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")
            self.client = None
    
    def generate(self, contract: GenerationContract) -> ContractOutput:
        """
        Generate content following the contract exactly.
        
        Args:
            contract: The generation contract (source of truth)
            
        Returns:
            Generated content output
        """
        # Select model based on contract
        model_config = self.router.select_for_contract(contract, TaskType.SCRIPTING)
        
        logger.info(f"Generating with contract: {contract.audience_baseline}, {contract.tone}, {contract.resolve_language()}")
        logger.info(f"Using model: {model_config.model_id}")
        
        # Build prompt from contract
        prompt = self._build_prompt(contract)
        
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=model_config.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=2048,
                    )
                )
                return self._parse_response(response.text, contract, model_config.model_id)
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return self._mock_output(contract, model_config.model_id)
        else:
            return self._mock_output(contract, model_config.model_id)
    
    def _build_prompt(self, contract: GenerationContract) -> str:
        """Build generation prompt from contract."""
        
        # Start with contract prompt
        prompt = contract.to_generation_prompt()
        
        # Add output format
        prompt += """

OUTPUT FORMAT (JSON):
{
    "script": "The complete script as one string",
    "segments": [
        {"text": "Segment text", "duration": 5, "tone": "segment tone"},
        ...
    ]
}
"""
        return prompt
    
    def _parse_response(self, response_text: str, contract: GenerationContract, model_id: str) -> ContractOutput:
        """Parse LLM response."""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("No JSON found")
            
            return ContractOutput(
                script=data.get("script", ""),
                segments=data.get("segments", []),
                contract_summary={
                    "audience": contract.audience_baseline,
                    "intent": contract.resolve_intent(),
                    "mode": contract.resolve_content_mode(),
                    "tone": contract.tone,
                    "language": contract.resolve_language()
                },
                model_used=model_id
            )
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._mock_output(contract, model_id)
    
    def _mock_output(self, contract: GenerationContract, model_id: str) -> ContractOutput:
        """Mock output for testing."""
        mode = contract.resolve_content_mode()
        lang = contract.resolve_language()
        
        if contract.audience_baseline == "kids":
            script = "Once upon a time, there was a curious little explorer who discovered something amazing..."
            segments = [
                {"text": "Once upon a time...", "duration": 4, "tone": "warm"},
                {"text": "There was a curious explorer.", "duration": 4, "tone": "wonder"},
            ]
        elif contract.tone == "bold":
            if lang == "hi":
                script = "यहाँ वो सच है जो कोई नहीं बोलता। ज़रा सोचो।"
                segments = [
                    {"text": "यहाँ वो सच है।", "duration": 3, "tone": "bold"},
                    {"text": "जो कोई नहीं बोलता।", "duration": 3, "tone": "provocative"},
                ]
            else:
                script = "Here's the truth no one wants to say. Think about it."
                segments = [
                    {"text": "Here's the truth.", "duration": 3, "tone": "bold"},
                    {"text": "No one wants to say it.", "duration": 3, "tone": "provocative"},
                ]
        else:
            script = "There's something interesting happening here. The data tells a clear story."
            segments = [
                {"text": "There's something interesting.", "duration": 4, "tone": "confident"},
                {"text": "The data is clear.", "duration": 3, "tone": "neutral"},
            ]
        
        return ContractOutput(
            script=script,
            segments=segments,
            contract_summary={
                "audience": contract.audience_baseline,
                "intent": contract.resolve_intent(),
                "mode": contract.resolve_content_mode(),
                "tone": contract.tone,
                "language": contract.resolve_language()
            },
            model_used=model_id
        )


# Singleton
_generator = None

def get_contract_generator() -> ContractGenerator:
    global _generator
    if _generator is None:
        _generator = ContractGenerator()
    return _generator


def generate_from_contract(contract: GenerationContract) -> Dict:
    """
    Generate content from a contract.
    
    Args:
        contract: The generation contract
        
    Returns:
        Output as dict
    """
    generator = get_contract_generator()
    output = generator.generate(contract)
    
    return {
        "script": output.script,
        "segments": output.segments,
        "contract": output.contract_summary,
        "model": output.model_used
    }


def quick_generate(
    idea: str,
    audience_baseline: str = "general_adult",
    tone: str = "neutral",
    language: str = "auto"
) -> Dict:
    """
    Quick generation with locked defaults.
    
    Args:
        idea: Content idea
        audience_baseline: "general_adult" (default), "kids", "expert"
        tone: "neutral", "sharp", "bold", "playful"
        language: Language code or "auto" for English
        
    Returns:
        Generated output
    """
    from app.core.contract import create_contract
    
    contract = create_contract(
        idea=idea,
        audience_baseline=audience_baseline,
        tone=tone,
        language=language
    )
    
    return generate_from_contract(contract)

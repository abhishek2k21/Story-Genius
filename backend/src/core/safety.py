"""
Prompt Safety Filters
Detect and handle potentially unsafe content.
"""
import re
from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel

from src.core.logging import get_logger

logger = get_logger(__name__)


class SafetyLevel(str, Enum):
    """Content safety levels."""
    SAFE = "safe"
    CAUTION = "caution"
    BLOCKED = "blocked"


class SafetyResult(BaseModel):
    """Result of safety check."""
    level: SafetyLevel
    original_prompt: str
    safe_prompt: Optional[str] = None
    reason: Optional[str] = None
    modifications: list[str] = []


# Patterns that trigger safety checks
BLOCKED_PATTERNS = [
    r"\b(kill|murder|attack|shoot|stab)\b",
    r"\b(nude|naked|explicit|porn)\b",
    r"\b(bomb|explosive|weapon)\b",
    r"\b(suicide|self.harm)\b",
    r"\b(child|minor).*(abuse|explicit)\b",
]

CAUTION_PATTERNS = [
    r"\b(violent|violence|blood|gore)\b",
    r"\b(fight|fighting|combat)\b",
    r"\b(death|dying|dead)\b",
    r"\b(fire|explosion|crash)\b",
    r"\b(scary|horror|terrifying)\b",
]

# Safe replacements for common scenarios
SAFE_ALTERNATIVES = {
    "explode": "burst into light",
    "explosion": "dramatic burst of energy",
    "crash": "dramatic collision",
    "fight": "dynamic confrontation",
    "blood": "red liquid",
    "gore": "dramatic effect",
    "death": "end of journey",
    "kill": "defeat",
    "fire": "glowing energy",
    "burning": "glowing warmly",
}


def check_prompt_safety(prompt: str) -> SafetyResult:
    """
    Check prompt for safety concerns.

    Returns:
        SafetyResult with level and optional modifications
    """
    prompt_lower = prompt.lower()

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            logger.warning(f"Blocked pattern detected in prompt")
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                original_prompt=prompt,
                reason="Content violates safety guidelines",
            )

    # Check caution patterns
    modifications = []
    safe_prompt = prompt

    for pattern in CAUTION_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            # Apply safe alternatives
            for unsafe, safe in SAFE_ALTERNATIVES.items():
                if unsafe in prompt_lower:
                    safe_prompt = re.sub(
                        rf"\b{unsafe}\b",
                        safe,
                        safe_prompt,
                        flags=re.IGNORECASE,
                    )
                    modifications.append(f"'{unsafe}' → '{safe}'")

    if modifications:
        logger.info(f"Prompt modified for safety: {modifications}")
        return SafetyResult(
            level=SafetyLevel.CAUTION,
            original_prompt=prompt,
            safe_prompt=safe_prompt,
            modifications=modifications,
        )

    return SafetyResult(
        level=SafetyLevel.SAFE,
        original_prompt=prompt,
    )


def get_safe_visual_prompt(visual_prompt: str, style_prefix: Optional[str] = None) -> str:
    """
    Ensure visual prompt is safe for video generation.

    Adds style modifiers and safety prefixes.
    """
    result = check_prompt_safety(visual_prompt)

    if result.level == SafetyLevel.BLOCKED:
        # Replace with generic safe version
        return (
            f"{style_prefix or 'Cinematic'}, abstract artistic interpretation, "
            "symbolic visualization, metaphorical imagery"
        )

    # Use modified prompt if available
    prompt = result.safe_prompt or visual_prompt

    # Add safety prefix for AI generation
    safety_prefix = "safe for all audiences, family-friendly visualization"

    if style_prefix:
        return f"{style_prefix}, {safety_prefix}, {prompt}"

    return f"{safety_prefix}, {prompt}"


def get_fallback_style(original_style: str) -> str:
    """
    Get a fallback style when content is flagged.

    Cartoon/animated styles are generally safer.
    """
    # If style already safe, keep it
    safe_styles = ["cartoon", "animated", "illustration", "children", "family"]

    if any(s in original_style.lower() for s in safe_styles):
        return original_style

    # Add cartoon modifier for safety
    return f"family-friendly cartoon style, {original_style}"

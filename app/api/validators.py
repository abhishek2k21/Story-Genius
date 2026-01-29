"""
Input Validation Layer
Request validation, sanitization, and security checks.
"""
import re
from typing import Optional, List
from pydantic import BaseModel, validator, Field

from app.core.exceptions import ValidationError


class ContentValidator:
    """Validates content inputs"""
    
    MIN_PROMPT_LENGTH = 10
    MAX_PROMPT_LENGTH = 500
    MIN_SCRIPT_LENGTH = 50
    MAX_SCRIPT_LENGTH = 5000
    
    # Dangerous patterns for prompt injection
    INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+prior",
        r"forget\s+everything",
        r"system\s*:",
        r"<\s*script",  # XSS attempts
        r"javascript\s*:",
        r"on\w+\s*=",  # Event handlers
    ]
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> str:
        """Validate and sanitize prompt"""
        if not prompt or not prompt.strip():
            raise ValidationError("Prompt cannot be empty", details={"field": "prompt"})
        
        prompt = prompt.strip()
        
        # Length check
        if len(prompt) < cls.MIN_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt too short (min {cls.MIN_PROMPT_LENGTH} chars)",
                details={"field": "prompt", "length": len(prompt)}
            )
        
        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt too long (max {cls.MAX_PROMPT_LENGTH} chars)",
                details={"field": "prompt", "length": len(prompt)}
            )
        
        # Check for injection attempts
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise ValidationError(
                    "Prompt contains potentially malicious content",
                    details={"field": "prompt", "pattern": pattern}
                )
        
        # Remove HTML tags
        prompt = re.sub(r'<[^>]+>', '', prompt)
        
        return prompt
    
    @classmethod
    def validate_script(cls, script: str) -> str:
        """Validate script content"""
        if not script or not script.strip():
            raise ValidationError("Script cannot be empty", details={"field": "script"})
        
        script = script.strip()
        
        if len(script) < cls.MIN_SCRIPT_LENGTH:
            raise ValidationError(
                f"Script too short (min {cls.MIN_SCRIPT_LENGTH} chars)",
                details={"field": "script", "length": len(script)}
            )
        
        if len(script) > cls.MAX_SCRIPT_LENGTH:
            raise ValidationError(
                f"Script too long (max {cls.MAX_SCRIPT_LENGTH} chars)",
                details={"field": "script", "length": len(script)}
            )
        
        return script


class PlatformValidator:
    """Validates platform-specific constraints"""
    
    PLATFORM_CONSTRAINTS = {
        "youtube_shorts": {
            "max_duration": 60,
            "aspect_ratio": "9:16",
            "min_resolution": (1080, 1920)
        },
        "instagram_reels": {
            "max_duration": 90,
            "aspect_ratio": "9:16",
            "min_resolution": (1080, 1920)
        },
        "tiktok": {
            "max_duration": 180,
            "aspect_ratio": "9:16",
            "min_resolution": (1080, 1920)
        }
    }
    
    @classmethod
    def validate_platform(cls, platform: str, duration: Optional[int] = None, 
                         aspect_ratio: Optional[str] = None) -> None:
        """Validate platform constraints"""
        platform_lower = platform.lower()
        
        if platform_lower not in cls.PLATFORM_CONSTRAINTS:
            raise ValidationError(
                f"Invalid platform: {platform}",
                details={
                    "field": "platform",
                    "valid_platforms": list(cls.PLATFORM_CONSTRAINTS.keys())
                }
            )
        
        constraints = cls.PLATFORM_CONSTRAINTS[platform_lower]
        
        # Validate duration
        if duration and duration > constraints["max_duration"]:
            raise ValidationError(
                f"Duration exceeds {platform} limit ({constraints['max_duration']}s)",
                details={
                    "field": "duration",
                    "max": constraints["max_duration"],
                    "actual": duration
                }
            )
        
        # Validate aspect ratio
        if aspect_ratio and aspect_ratio != constraints["aspect_ratio"]:
            raise ValidationError(
                f"Invalid aspect ratio for {platform}",
                details={
                    "field": "aspect_ratio",
                    "expected": constraints["aspect_ratio"],
                    "actual": aspect_ratio
                }
            )


class AudienceValidator:
    """Validates audience compatibility"""
    
    VALID_AUDIENCES = ["kids", "teens", "adults", "general"]
    CONTENT_RATINGS = ["G", "PG", "PG-13", "R"]
    
    @classmethod
    def validate_audience(cls, audience: str, content_rating: Optional[str] = None) -> None:
        """Validate audience settings"""
        if audience.lower() not in cls.VALID_AUDIENCES:
            raise ValidationError(
                f"Invalid audience: {audience}",
                details={
                    "field": "audience",
                    "valid_audiences": cls.VALID_AUDIENCES
                }
            )
        
        if content_rating and content_rating.upper() not in cls.CONTENT_RATINGS:
            raise ValidationError(
                f"Invalid content rating: {content_rating}",
                details={
                    "field": "content_rating",
                    "valid_ratings": cls.CONTENT_RATINGS
                }
            )
        
        # Check compatibility
        if audience.lower() == "kids" and content_rating and content_rating.upper() != "G":
            raise ValidationError(
                "Kids audience requires G rating",
                details={"field": "content_rating", "audience": audience}
            )


def sanitize_html(text: str) -> str:
    """Remove HTML tags and dangerous content"""
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    import html
    text = html.unescape(text)
    
    return text.strip()


# Validation schemas for common requests
class VideoGenerationRequest(BaseModel):
    """Validated video generation request"""
    prompt: str
    platform: str = "youtube_shorts"
    audience: str = "general"
    duration: Optional[int] = Field(None, ge=10, le=180)
    
    @validator('prompt')
    def validate_prompt_field(cls, v):
        return ContentValidator.validate_prompt(v)
    
    @validator('platform')
    def validate_platform_field(cls, v):
        PlatformValidator.validate_platform(v)
        return v.lower()
    
    @validator('audience')
    def validate_audience_field(cls, v):
        AudienceValidator.validate_audience(v)
        return v.lower()

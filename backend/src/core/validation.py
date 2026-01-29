"""
Input Validation Middleware
Request body validation and sanitization.
"""
import re
from typing import Callable

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger

logger = get_logger(__name__)


# Maximum request body sizes by content type
MAX_BODY_SIZES = {
    "application/json": 1 * 1024 * 1024,  # 1MB
    "multipart/form-data": 100 * 1024 * 1024,  # 100MB for file uploads
    "default": 512 * 1024,  # 512KB
}

# Fields that should be sanitized
SANITIZE_FIELDS = ["prompt", "narration", "description", "title", "content"]


def sanitize_string(value: str) -> str:
    """Sanitize a string input."""
    if not isinstance(value, str):
        return value

    # Remove potential XSS
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

    # Remove control characters (keep newlines/tabs)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def sanitize_dict(data: dict) -> dict:
    """Recursively sanitize dictionary values."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str) and key.lower() in SANITIZE_FIELDS:
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item) if isinstance(item, dict)
                else sanitize_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize request inputs."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Check content length
        content_type = request.headers.get("content-type", "").split(";")[0]
        content_length = request.headers.get("content-length")

        if content_length:
            max_size = MAX_BODY_SIZES.get(content_type, MAX_BODY_SIZES["default"])
            if int(content_length) > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large. Max size: {max_size} bytes",
                )

        # Validate path parameters
        if ".." in request.url.path or "%" in request.url.path:
            if "%2e%2e" in request.url.path.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Invalid path",
                )

        return await call_next(request)


# Common validators
def validate_uuid(value: str) -> bool:
    """Validate UUID format."""
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(pattern, value.lower()))


def validate_prompt(prompt: str, min_length: int = 10, max_length: int = 5000) -> str:
    """Validate and sanitize a prompt."""
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt is required")

    prompt = sanitize_string(prompt)

    if len(prompt) < min_length:
        raise ValueError(f"Prompt must be at least {min_length} characters")

    if len(prompt) > max_length:
        raise ValueError(f"Prompt must be at most {max_length} characters")

    return prompt

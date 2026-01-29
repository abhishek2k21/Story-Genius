"""
Custom Exceptions for Story-Genius
"""
from typing import Any, Optional


class StoryGeniusError(Exception):
    """Base exception for all Story-Genius errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(StoryGeniusError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class NotFoundError(StoryGeniusError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ExternalServiceError(StoryGeniusError):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str,
        message: str,
        retryable: bool = True,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "retryable": retryable, **(details or {})},
        )
        self.service = service
        self.retryable = retryable


class RateLimitError(StoryGeniusError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after}s",
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class AuthenticationError(StoryGeniusError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(StoryGeniusError):
    """Raised when user lacks permission."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, code="AUTHORIZATION_ERROR")

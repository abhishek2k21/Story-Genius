from typing import Any, Dict, Optional

class CustomException(Exception):
    """Base class for all custom application exceptions."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

# Standard HTTP Exceptions
class ValidationError(CustomException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)

class NotFoundError(CustomException):
    def __init__(self, message: str, resource: str = "Resource"):
        super().__init__(
            message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource}
        )

class UnauthorizedError(CustomException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)

class ForbiddenError(CustomException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="FORBIDDEN", status_code=403)

class RateLimitError(CustomException):
    def __init__(self, message: str = "Too many requests", retry_after: int = 60):
        super().__init__(
            message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )

class MethodNotAllowedError(CustomException):
    def __init__(self, method: str):
        super().__init__(
            f"Method {method} not allowed",
            code="METHOD_NOT_ALLOWED",
            status_code=405
        )

# Database Exceptions
class DatabaseError(CustomException):
    def __init__(self, message: str, original_error: Any = None):
        super().__init__(
            message,
            code="DATABASE_ERROR",
            status_code=500,
            details={"original_error": str(original_error) if original_error else None}
        )

class DatabaseConnectionError(DatabaseError):
    def __init__(self, message: str = "Could not connect to database"):
        super().__init__(message, code="DB_CONNECTION_ERROR")

# Service Specific Exceptions
class ThirdPartyServiceError(CustomException):
    """Base for external service failures"""
    def __init__(self, service_name: str, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"{service_name} Error: {message}",
            code=f"{service_name.upper()}_ERROR",
            status_code=status_code,
            details=details
        )

class VeoError(ThirdPartyServiceError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("Veo", message, details=details)

class ImagenError(ThirdPartyServiceError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("Imagen", message, details=details)

class VertexAIError(ThirdPartyServiceError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("VertexAI", message, details=details)

class StorageError(ThirdPartyServiceError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("Storage", message, details=details)

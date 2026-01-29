"""
API Response Schemas
Standardized response formats for all API endpoints.
"""
from typing import TypeVar, Generic, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field: Optional[str] = None  # For validation errors


class APIResponse(BaseModel, Generic[T]):
    """
    Generic API response wrapper.
    
    Success example:
    {
        "data": {...},
        "status": "success",
        "timestamp": "2026-01-28T14:00:00Z"
    }
    
    Error example:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid input",
            "details": {...}
        },
        "timestamp": "2026-01-28T14:00:00Z"
    }
    """
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def success(cls, data: T) -> "APIResponse[T]":
        """Create a success response"""
        return cls(data=data, status="success")
    
    @classmethod
    def error(cls, code: str, message: str, details: Dict = None, status_code: int = 400) -> "APIResponse":
        """Create an error response"""
        return cls(
            error=ErrorDetail(code=code, message=message, details=details),
            status="error",
            data=None
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size


class BatchStatusResponse(BaseModel):
    """Batch processing status response"""
    batch_id: str
    status: str
    total_items: int
    completed: int
    failed: int
    pending: int
    errors: list[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]] = {}
    circuit_breakers: Dict[str, Dict[str, Any]] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

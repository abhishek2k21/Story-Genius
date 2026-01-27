"""
Request Context Management
Context propagation for request tracking across components.
"""
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
import uuid


# Context variable for request tracking
_request_context: ContextVar[Optional["RequestContext"]] = ContextVar(
    "request_context", default=None
)


@dataclass
class RequestContext:
    """Context that flows through a request lifecycle"""
    request_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    job_id: Optional[str] = None
    batch_id: Optional[str] = None
    user_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "start_time": self.start_time.isoformat(),
            "job_id": self.job_id,
            "batch_id": self.batch_id,
            "user_id": self.user_id,
            **self.extra
        }
    
    def with_job(self, job_id: str) -> "RequestContext":
        """Return new context with job_id"""
        self.job_id = job_id
        return self
    
    def with_batch(self, batch_id: str) -> "RequestContext":
        """Return new context with batch_id"""
        self.batch_id = batch_id
        return self
    
    def with_user(self, user_id: str) -> "RequestContext":
        """Return new context with user_id"""
        self.user_id = user_id
        return self
    
    def with_extra(self, key: str, value: Any) -> "RequestContext":
        """Add extra context data"""
        self.extra[key] = value
        return self


def get_context() -> Optional[RequestContext]:
    """Get current request context"""
    return _request_context.get()


def set_context(context: RequestContext) -> None:
    """Set request context"""
    _request_context.set(context)


def clear_context() -> None:
    """Clear request context"""
    _request_context.set(None)


def create_context(
    request_id: str = None,
    job_id: str = None,
    batch_id: str = None,
    user_id: str = None
) -> RequestContext:
    """Create and set a new request context"""
    context = RequestContext(
        request_id=request_id or str(uuid.uuid4()),
        job_id=job_id,
        batch_id=batch_id,
        user_id=user_id
    )
    set_context(context)
    return context


class ContextManager:
    """Context manager for request lifecycle"""
    
    def __init__(self, request_id: str = None, **kwargs):
        self.context = RequestContext(
            request_id=request_id or str(uuid.uuid4()),
            **kwargs
        )
        self._previous = None
    
    def __enter__(self) -> RequestContext:
        self._previous = get_context()
        set_context(self.context)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_context(self._previous)
        return False


def get_request_id() -> Optional[str]:
    """Get current request ID"""
    ctx = get_context()
    return ctx.request_id if ctx else None


def get_job_id() -> Optional[str]:
    """Get current job ID"""
    ctx = get_context()
    return ctx.job_id if ctx else None


def get_context_dict() -> Dict:
    """Get context as dict for logging"""
    ctx = get_context()
    if ctx:
        return ctx.to_dict()
    return {}

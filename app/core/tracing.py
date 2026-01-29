"""
Distributed Tracing with Trace ID Propagation
"""
import uuid
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

# Context variables for async propagation
_trace_context: ContextVar[Optional['TraceContext']] = ContextVar('trace_context', default=None)


@dataclass
class TraceContext:
    """Trace context for distributed tracing"""
    trace_id: str
    request_id: str
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    batch_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "batch_id": self.batch_id,
            "parent_span_id": self.parent_span_id
        }


def generate_trace_id() -> str:
    """Generate a new trace ID"""
    return f"trace_{uuid.uuid4().hex[:16]}"


def generate_request_id() -> str:
    """Generate a new request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def generate_span_id() -> str:
    """Generate a new span ID"""
    return f"span_{uuid.uuid4().hex[:8]}"


def get_trace_context() -> Optional[TraceContext]:
    """Get current trace context from context variable"""
    return _trace_context.get()


def set_trace_context(context: TraceContext):
    """Set trace context in context variable"""
    _trace_context.set(context)


def clear_trace_context():
    """Clear trace context"""
    _trace_context.set(None)


def create_trace_context(
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    batch_id: Optional[str] = None
) -> TraceContext:
    """Create a new trace context"""
    return TraceContext(
        trace_id=generate_trace_id(),
        request_id=generate_request_id(),
        user_id=user_id,
        job_id=job_id,
        batch_id=batch_id
    )


def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    context = get_trace_context()
    return context.trace_id if context else None


def get_request_id() -> Optional[str]:
    """Get current request ID"""
    context = get_trace_context()
    return context.request_id if context else None


def enrich_trace_context(**kwargs):
    """
    Enrich current trace context with additional fields.
    
    Args:
        **kwargs: Fields to add (user_id, job_id, batch_id, etc.)
    """
    context = get_trace_context()
    if context:
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)


# FastAPI Middleware for trace injection
class TracingMiddleware:
    """
    FastAPI middleware to inject trace ID into requests.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create trace context
        trace_id = generate_trace_id()
        request_id = generate_request_id()
        
        context = TraceContext(
            trace_id=trace_id,
            request_id=request_id
        )
        
        set_trace_context(context)
        
        # Inject trace_id into response headers
        async def send_with_trace_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_with_trace_id)
        finally:
            clear_trace_context()

"""
Audit Logging Middleware.
Logs all API requests and data access for GDPR compliance.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.models.privacy import AuditLog
from app.database import get_db
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all data access for GDPR compliance.
    Records who accessed what data, when, and from where.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log audit trail."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user info
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
        
        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Start time
        start_time = datetime.utcnow()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine if this is a data access operation
        is_data_access = self._is_data_access_operation(request.method, request.url.path)
        
        if is_data_access:
            # Log to database asynchronously
            try:
                await self._log_to_database(
                    request_id=request_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms
                )
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _is_data_access_operation(self, method: str, path: str) -> bool:
        """
        Determine if request is a data access operation.
        
        Args:
            method: HTTP method
            path: Request path
            
        Returns:
            True if data access operation
        """
        # Skip health checks, metrics, static files
        skip_paths = ["/health", "/metrics", "/static", "/favicon.ico"]
        if any(path.startswith(p) for p in skip_paths):
            return False
        
        # Log all data modifications
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True
        
        # Log GET requests to sensitive endpoints
        sensitive_paths = ["/api/users", "/api/videos", "/api/payments", "/gdpr"]
        if any(path.startswith(p) for p in sensitive_paths):
            return True
        
        return False
    
    async def _log_to_database(
        self,
        request_id: str,
        user_id: str,
        ip_address: str,
        user_agent: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float
    ):
        """Write audit log to database."""
        db = next(get_db())
        
        try:
            # Determine action from method
            action_map = {
                "GET": "read",
                "POST": "create",
                "PUT": "update",
                "PATCH": "update",
                "DELETE": "delete"
            }
            action = action_map.get(method, "unknown")
            
            # Extract resource type from path
            resource_type = self._extract_resource_type(path)
            
            # Create audit log
            audit_log = AuditLog(
                request_id=request_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                method=method,
                path=path,
                status_code=str(status_code),
                action=action,
                resource_type=resource_type,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
        
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _extract_resource_type(self, path: str) -> str:
        """Extract resource type from path."""
        # /api/users/123 -> users
        # /api/videos/456 -> videos
        parts = path.strip("/").split("/")
        
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1]
        
        return "unknown"

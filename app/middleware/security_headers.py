"""
Security Headers Middleware.
Adds comprehensive security headers to all HTTP responses.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Implements OWASP security header best practices:
    - X-Content-Type-Options (prevent MIME sniffing)
    - X-Frame-Options (prevent clickjacking)
    - X-XSS-Protection (XSS filtering)
    - Content-Security-Policy (XSS/injection prevention)
    - Strict-Transport-Security (HTTPS enforcement)
    - Referrer-Policy (referrer control)
    - Permissions-Policy (feature control)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response: Response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking (frame embedding)
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy, but defense in depth)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        # Restricts sources for scripts, styles, images, etc.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # HSTS (HTTP Strict Transport Security)
        # Force HTTPS for 1 year, including subdomains
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Referrer Policy
        # Control what referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature-Policy)
        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        # Remove server header (information disclosure)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Remove X-Powered-By (information disclosure)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        # Cache control for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        else:
            # Allow caching for public endpoints
            response.headers["Cache-Control"] = "public, max-age=3600"
        
        return response
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is sensitive (should not be cached).
        
        Args:
            path: Request path
            
        Returns:
            True if sensitive endpoint
        """
        sensitive_paths = [
            "/api/",
            "/oauth/",
            "/gdpr/",
            "/admin/",
            "/compliance/"
        ]
        
        return any(path.startswith(p) for p in sensitive_paths)


# Integration with FastAPI
# Add to main.py:
# from app.middleware.security_headers import SecurityHeadersMiddleware
# app.add_middleware(SecurityHeadersMiddleware)

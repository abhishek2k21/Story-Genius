"""
API Middleware for Request Context and Error Handling.
"""
import time
import uuid
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.context import clear_context, create_context, get_context
from app.core.logging import get_logger
from app.core.exceptions import CustomException
from app.observability.errors import error_tracker

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to initialize request context and log request details.
    """
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Initialize context
        create_context(request_id=request_id)
        
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        logger.info(f"Request started: {method} {path}", extra={"method": method, "path": path})
        
        try:
            response = await call_next(request)
            
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Request completed: {method} {path} {response.status_code}",
                duration_ms=duration_ms,
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code
                }
            )
            
            # Add Request-ID header to response
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {method} {path}",
                exc_info=True,
                duration_ms=duration_ms
            )
            raise e  # Allow ExceptionMiddleware to handle it (or GlobalHandler)
        finally:
            clear_context()


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch all exceptions and return structured JSON responses.
    Ensures no 500 Internal Server Error crashes without logging.
    """
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except CustomException as e:
            # Handle known custom exceptions
            logger.warning(f"CustomException: {e.message}", extra=e.to_dict())
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
            
            # Track error in observability
            error_tracker.capture(e, context={"path": request.url.path})
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                        "details": {"request_id": request.headers.get("X-Request-ID")}
                    }
                }
            )

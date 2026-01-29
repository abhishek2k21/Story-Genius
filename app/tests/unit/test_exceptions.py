"""
Unit Tests for Custom Exceptions
"""
import pytest
from app.core.exceptions import (
    CustomException, ValidationError, NotFoundError, 
    UnauthorizedError, RateLimitError, DatabaseError, VeoError
)

def test_custom_exception_base():
    exc = CustomException("Base error", code="BASE", status_code=500, details={"foo": "bar"})
    assert exc.message == "Base error"
    assert exc.code == "BASE"
    assert exc.status_code == 500
    assert exc.details == {"foo": "bar"}
    
    data = exc.to_dict()
    assert data["error"]["code"] == "BASE"
    assert data["error"]["message"] == "Base error"
    assert data["error"]["details"]["foo"] == "bar"

def test_validation_error():
    exc = ValidationError("Invalid input", details={"field": "email"})
    assert exc.status_code == 422
    assert exc.code == "VALIDATION_ERROR"
    assert exc.details["field"] == "email"

def test_not_found_error():
    exc = NotFoundError("User not found", resource="User")
    assert exc.status_code == 404
    assert exc.code == "NOT_FOUND"
    assert exc.details["resource"] == "User"

def test_unauthorized_error():
    exc = UnauthorizedError()
    assert exc.status_code == 401
    assert exc.code == "UNAUTHORIZED"

def test_rate_limit_error():
    exc = RateLimitError()
    assert exc.status_code == 429
    assert exc.code == "RATE_LIMIT_EXCEEDED"
    assert "retry_after" in exc.details

def test_database_error():
    exc = DatabaseError("Connection failed", original_error="Timeout")
    assert exc.status_code == 500
    assert exc.code == "DATABASE_ERROR"
    assert exc.details["original_error"] == "Timeout"

def test_service_error_veo():
    exc = VeoError("API unreachable")
    assert exc.status_code == 502
    assert exc.code == "VEO_ERROR"
    assert "Veo Error: API unreachable" in exc.message

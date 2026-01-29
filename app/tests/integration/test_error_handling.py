"""
Integration Tests for Global Error Handling
"""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.exceptions import CustomException, NotFoundError

client = TestClient(app)

# Dummy endpoint for testing
@app.get("/test/error/custom")
def trigger_custom_error():
    raise CustomException("Test custom error", code="TEST_ERROR", status_code=418)

@app.get("/test/error/unhandled")
def trigger_unhandled_error():
    raise ValueError("Unexpected failure")

@app.get("/test/error/notfound")
def trigger_not_found():
    raise NotFoundError("Item missing")

def test_404_handler():
    # Test standard 404 (route not found)
    response = client.get("/non-existent-route")
    assert response.status_code == 404
    # FastAPI default 404 is plain JSON {"detail": "Not Found"}
    # Our middleware only catches Exceptions raised during processing, 
    # but 404 for missing route is handled by Starlette's exception handler mechanism.
    # If we want custom JSON for 404, we need to register exception handler for 404 status or exception.
    # For now, we assume standard behavior or check if our middleware intercepts 404s (it usually doesn't for route resolution failures unless caught).
    assert response.json() == {"detail": "Not Found"}

def test_custom_exception_handler():
    response = client.get("/test/error/custom")
    assert response.status_code == 418
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TEST_ERROR"
    assert data["error"]["message"] == "Test custom error" 
    # Verify Middleware Added Headers
    assert "X-Request-ID" in response.headers

def test_manual_not_found_exception():
    response = client.get("/test/error/notfound")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"

def test_unhandled_exception_middleware():
    # This tests GlobalExceptionMiddleware capturing generic Exception
    response = client.get("/test/error/unhandled")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Ensure details are hidden in production but we return generic message
    assert data["error"]["message"] == "An unexpected error occurred."
    assert "X-Request-ID" in response.headers

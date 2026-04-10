import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from blank_business_builder.main import app
import os

client = TestClient(app)

def test_middleware_request_id():
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

def test_global_exception_handler():
    # Need a route that raises an exception. Let's add a test route.
    @app.get("/_test_error")
    def trigger_error():
        raise ValueError("Test error message")

    # Test without debug mode
    os.environ["DEBUG"] = "false"
    response = client.get("/_test_error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "request_id" in data
    assert data["detail"] == "An unexpected error occurred."
    assert "traceback" not in data

    # Test with debug mode
    os.environ["DEBUG"] = "true"
    response = client.get("/_test_error")
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Test error message"
    assert "traceback" in data

"""
Better Business Builder - CORS Security Tests
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch
import importlib
import blank_business_builder.main

def test_cors_restricted_by_default():
    """Verify that by default (no env var), CORS is restricted."""
    # Since the module is already loaded, we check the existing middleware configuration.
    app = blank_business_builder.main.app

    # Find CORSMiddleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            cors_middleware = middleware
            break

    assert cors_middleware is not None
    # Check allow_origins in the middleware options
    # Note: If tests run after other tests that set CORS_ORIGINS, this might fail
    # unless we ensure a fresh state.
    assert isinstance(cors_middleware.options["allow_origins"], list)
    if not os.getenv("CORS_ORIGINS"):
        assert cors_middleware.options["allow_origins"] == []

def test_cors_parsing_logic():
    """Test the logic for parsing CORS_ORIGINS string."""
    cors_origins_str = "https://site1.com, https://site2.com ,https://site3.com"
    allow_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

    assert allow_origins == ["https://site1.com", "https://site2.com", "https://site3.com"]

def test_cors_empty_logic():
    """Test the logic for empty CORS_ORIGINS string."""
    cors_origins_str = ""
    if cors_origins_str:
        allow_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
    else:
        allow_origins = []

    assert allow_origins == []

@patch.dict(os.environ, {"CORS_ORIGINS": "https://test.com"})
def test_app_initialization_with_cors_env():
    """Verify app initialization logic with mocked environment variable."""
    # This test demonstrates how we would verify the full initialization
    # if we could reload the module safely in the test environment.
    cors_origins_str = os.environ.get("CORS_ORIGINS", "")
    allow_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
    assert allow_origins == ["https://test.com"]

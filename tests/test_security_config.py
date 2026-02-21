import os
import pytest
import importlib
from unittest import mock

def test_random_secret_key_generation_in_dev():
    """Verify that a random secret key is generated in development if not provided."""
    # Mock environment to ensure no secret key is set and it's not production
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
        # We need to reload the module to trigger the logic
        from blank_business_builder import config
        importlib.reload(config)

        key1 = config.settings.SECRET_KEY
        assert key1 is not None
        assert len(key1) >= 32
        assert key1 != "your-secret-key-change-in-production"
        assert key1 != "your-secret-key-please-change-in-production"

        # Another reload should generate a different key
        importlib.reload(config)
        key2 = config.settings.SECRET_KEY
        assert key2 != key1

def test_production_fails_without_secret_key():
    """Verify that a RuntimeError is raised if no secret key is provided in production."""
    # Clear all relevant env vars
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
        from blank_business_builder import config
        with pytest.raises(RuntimeError) as excinfo:
            importlib.reload(config)
        assert "SECURITY ERROR" in str(excinfo.value)
        assert "must be set in production" in str(excinfo.value)

def test_production_works_with_secret_key():
    """Verify that the provided secret key is used in production."""
    my_secret = "very-secret-key-12345"
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production", "JWT_SECRET_KEY": my_secret}, clear=True):
        from blank_business_builder import config
        importlib.reload(config)
        assert config.settings.SECRET_KEY == my_secret

def test_prefers_jwt_secret_key():
    """Verify that JWT_SECRET_KEY is preferred over SECRET_KEY."""
    with mock.patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "JWT_SECRET_KEY": "jwt-key",
        "SECRET_KEY": "general-key"
    }, clear=True):
        from blank_business_builder import config
        importlib.reload(config)
        assert config.settings.SECRET_KEY == "jwt-key"

def test_falls_back_to_secret_key():
    """Verify that it falls back to SECRET_KEY if JWT_SECRET_KEY is missing."""
    with mock.patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "SECRET_KEY": "general-key"
    }, clear=True):
        from blank_business_builder import config
        importlib.reload(config)
        assert config.settings.SECRET_KEY == "general-key"

"""
Tests for BufferService Integration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
import sys
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies for initial import
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.status"] = MagicMock()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder import integrations

class TestBufferService:
    """Test BufferService functionality."""

    def setup_method(self):
        # Mock dependencies
        self.mock_requests = MagicMock()
        sys.modules["requests"] = self.mock_requests

        # Mock FastAPI
        class MockHTTPException(Exception):
            def __init__(self, status_code, detail):
                self.status_code = status_code
                self.detail = detail

        mock_fastapi = MagicMock()
        mock_fastapi.HTTPException = MockHTTPException
        mock_fastapi.status = MagicMock()
        mock_fastapi.status.HTTP_501_NOT_IMPLEMENTED = 501
        mock_fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
        sys.modules["fastapi"] = mock_fastapi
        sys.modules["fastapi.status"] = mock_fastapi.status

        # Reload module
        importlib.reload(integrations)
        self.BufferService = integrations.BufferService
        self.IntegrationFactory = integrations.IntegrationFactory
        self.MockHTTPException = MockHTTPException

    def test_initialization(self):
        """Test initialization with and without API key."""
        with patch.dict('os.environ', {'BUFFER_ACCESS_TOKEN': 'test_token'}):
            service = self.BufferService()
            assert service.access_token == 'test_token'

    def test_get_profiles_success(self):
        """Test getting profiles successfully."""
        with patch.dict('os.environ', {'BUFFER_ACCESS_TOKEN': 'test_token'}):
            service = self.BufferService()

            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": "p1"}]
            self.mock_requests.get.return_value = mock_response

            profiles = service.get_profiles()

            assert profiles == [{"id": "p1"}]
            self.mock_requests.get.assert_called_once()
            kwargs = self.mock_requests.get.call_args[1]
            assert kwargs['params']['access_token'] == 'test_token'

    def test_get_profiles_not_configured(self):
        """Test getting profiles when not configured."""
        with patch.dict('os.environ', {}, clear=True):
            service = self.BufferService()

            with pytest.raises(self.MockHTTPException) as excinfo:
                service.get_profiles()

            assert excinfo.value.status_code == 501
            assert "not configured" in excinfo.value.detail

    def test_get_profiles_failure(self):
        """Test getting profiles failure."""
        with patch.dict('os.environ', {'BUFFER_ACCESS_TOKEN': 'test_token'}):
            service = self.BufferService()

            self.mock_requests.get.side_effect = Exception("Buffer API Error")

            with pytest.raises(self.MockHTTPException) as excinfo:
                service.get_profiles()

            assert excinfo.value.status_code == 500
            assert "Buffer API Error" in excinfo.value.detail

    def test_create_post_success(self):
        """Test creating a post successfully."""
        with patch.dict('os.environ', {'BUFFER_ACCESS_TOKEN': 'test_token'}):
            service = self.BufferService()

            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True}
            self.mock_requests.post.return_value = mock_response

            result = service.create_post("p1", "Hello World")

            assert result == {"success": True}
            self.mock_requests.post.assert_called_once()

    def test_schedule_post(self):
        """Test scheduling a post."""
        with patch.dict('os.environ', {'BUFFER_ACCESS_TOKEN': 'test_token'}):
            service = self.BufferService()

            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True}
            self.mock_requests.post.return_value = mock_response

            result = service.schedule_post(
                "p1", "Hello Future", 1234567890, "http://image.com"
            )

            assert result == {"success": True}
            self.mock_requests.post.assert_called_once()
            kwargs = self.mock_requests.post.call_args[1]
            assert kwargs['data']['scheduled_at'] == 1234567890

    def test_factory_method(self):
        """Test IntegrationFactory creates BufferService."""
        service = self.IntegrationFactory.get_buffer_service()
        assert isinstance(service, self.BufferService)

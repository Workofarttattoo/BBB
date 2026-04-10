"""
Tests for SendGridService Integration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
import sys
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies for initial import
sys.modules["sendgrid"] = MagicMock()
sys.modules["sendgrid.helpers.mail"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.status"] = MagicMock()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder import integrations

class TestSendGridService:
    """Test SendGridService functionality."""

    def setup_method(self):
        # Mock dependencies
        self.mock_sendgrid = MagicMock()
        sys.modules["sendgrid"] = self.mock_sendgrid
        sys.modules["sendgrid.helpers.mail"] = MagicMock()
        sys.modules["requests"] = MagicMock()

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
        self.SendGridService = integrations.SendGridService
        self.IntegrationFactory = integrations.IntegrationFactory
        self.MockHTTPException = MockHTTPException

        # Reset mocks
        self.mock_client_instance = self.mock_sendgrid.SendGridAPIClient.return_value
        self.mock_client_instance.reset_mock()
        self.mock_client_instance.send.side_effect = None

    def test_initialization(self):
        """Test initialization with and without API key."""
        # With API Key
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'SG.test_key'}):
            service = self.SendGridService()
            assert service.client is not None
            self.mock_sendgrid.SendGridAPIClient.assert_called_with('SG.test_key')

        # Without API Key
        with patch.dict('os.environ', {}, clear=True):
            service = self.SendGridService()
            assert service.client is None

    def test_send_email_success(self):
        """Test sending a single email successfully."""
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'SG.test_key'}):
            service = self.SendGridService()

            # Mock successful send
            mock_response = MagicMock()
            mock_response.status_code = 202
            service.client.send.return_value = mock_response

            result = service.send_email(
                "test@example.com", "Subject", "Content", use_queue=False
            )

            assert result is True
            service.client.send.assert_called_once()

    def test_send_email_not_configured(self):
        """Test sending email when not configured."""
        with patch.dict('os.environ', {}, clear=True):
            service = self.SendGridService()

            with pytest.raises(self.MockHTTPException) as excinfo:
                service.send_email("test@example.com", "Subject", "Content", use_queue=False)

            assert excinfo.value.status_code == 501
            assert "not configured" in excinfo.value.detail

    def test_send_email_failure(self):
        """Test sending email failure."""
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'SG.test_key'}):
            service = self.SendGridService()

            # Mock failure
            service.client.send.side_effect = Exception("SendGrid Error")

            with pytest.raises(Exception) as excinfo:
                service.send_email("test@example.com", "Subject", "Content", use_queue=False)

            assert "SendGrid Error" in str(excinfo.value)

    def test_send_bulk_email(self):
        """Test sending bulk emails."""
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'SG.test_key'}):
            service = self.SendGridService()

            # Mock send
            mock_response = MagicMock()
            mock_response.status_code = 202
            service.client.send.return_value = mock_response

            # send_bulk_email uses send_email, which by default uses task_queue
            # we need to mock task_queue or make send_bulk_email use use_queue=False
            # Wait, send_bulk_email in integration.py does self.send_email(email, subject, html_content, from_name)
            # which adds it to task queue. It returns early, meaning success_count always increments
            # unless task_queue raises an error.
            # But the test tests service.client.send.call_count == 2. So we need to mock send_email.
            with patch.object(service, 'send_email') as mock_send_email:
                emails = ["u1@example.com", "u2@example.com"]
                result = service.send_bulk_email(
                    emails, "Subject", "Content"
                )

                assert result["success"] == 2
                assert result["failed"] == 0
                assert mock_send_email.call_count == 2

    def test_send_transactional_email(self):
        """Test sending transactional email."""
        with patch.dict('os.environ', {'SENDGRID_API_KEY': 'SG.test_key'}):
            service = self.SendGridService()

            mock_response = MagicMock()
            mock_response.status_code = 202
            service.client.send.return_value = mock_response

            result = service.send_transactional_email(
                "u1@example.com", "template-id", {"name": "User"}
            )

            assert result is True
            service.client.send.assert_called_once()

    def test_factory_method(self):
        """Test IntegrationFactory creates SendGridService."""
        service = self.IntegrationFactory.get_sendgrid_service()
        assert isinstance(service, self.SendGridService)

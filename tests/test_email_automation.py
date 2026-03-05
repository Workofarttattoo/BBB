import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.getcwd())

# Create a mock for the entire IntegrationFactory module to avoid import issues
# since requests is missing and would be imported by integrations.py
mock_integrations = MagicMock()
sys.modules['src.blank_business_builder.integrations'] = mock_integrations
mock_factory = mock_integrations.IntegrationFactory

# Mock other missing modules
sys.modules['requests'] = MagicMock()
sys.modules['httpx'] = MagicMock()

# Import early to avoid issues later
from ech0_autonomous_business import EmailAutomation, ECH0AutonomousCore

class TestEmailAutomation(unittest.TestCase):
    def setUp(self):
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.config = {
            'owner': {
                'emails': {
                    'primary': 'test@example.com'
                }
            },
            'email': {
                'sendgrid_api_key': 'fake_key' # Enable SendGrid to test that it's NOT called
            }
        }
        # Mock log_activity to track calls
        self.mock_core.log_activity = MagicMock()
        self.email_automation = EmailAutomation(self.mock_core)

        # Reset the factory mock before each test
        mock_factory.reset_mock()

    @patch('smtplib.SMTP')
    def test_send_email_blacklisted_email(self, mock_smtp):
        """Test that a blacklisted email address is blocked immediately."""
        blacklisted_email = 'dfeldman@feldmanattorneys.com'
        result = self.email_automation.send_email(to=blacklisted_email, subject="Test", body="Hello")

        self.assertFalse(result, "Should return False for blacklisted email")
        self.mock_core.log_activity.assert_called_with(
            "email", "BLACKLIST_BLOCKED", f"Blocked contact to {blacklisted_email} (FORBIDDEN)"
        )

        # Verify SendGrid and SMTP were NOT called
        mock_factory.get_sendgrid_service.assert_not_called()
        mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_send_email_blacklisted_domain(self, mock_smtp):
        """Test that an email from a blacklisted domain is blocked immediately."""
        blacklisted_email = 'any.one@feldmanattorneys.com'
        result = self.email_automation.send_email(to=blacklisted_email, subject="Test", body="Hello")

        self.assertFalse(result, "Should return False for blacklisted domain")
        self.mock_core.log_activity.assert_called_with(
            "email", "BLACKLIST_BLOCKED", f"Blocked contact to {blacklisted_email} (FORBIDDEN)"
        )

        # Verify SendGrid and SMTP were NOT called
        mock_factory.get_sendgrid_service.assert_not_called()
        mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_send_email_case_insensitivity(self, mock_smtp):
        """Test that blacklist check is case-insensitive."""
        blacklisted_email = 'DFELDMAN@FELDMANATTORNEYS.COM'
        result = self.email_automation.send_email(to=blacklisted_email, subject="Test", body="Hello")

        self.assertFalse(result, "Should return False for blacklisted email regardless of case")
        self.mock_core.log_activity.assert_called_with(
            "email", "BLACKLIST_BLOCKED", f"Blocked contact to {blacklisted_email} (FORBIDDEN)"
        )

        # Verify SendGrid and SMTP were NOT called
        mock_factory.get_sendgrid_service.assert_not_called()
        mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_send_email_not_blacklisted_proceeds(self, mock_smtp):
        """Test that a non-blacklisted email proceeds to sending logic."""
        non_blacklisted_email = 'legit@example.com'

        # Configure SendGrid mock to return True (sent)
        mock_service = MagicMock()
        mock_service.send_email_direct.return_value = True
        mock_factory.get_sendgrid_service.return_value = mock_service

        result = self.email_automation.send_email(to=non_blacklisted_email, subject="Test", body="Hello")

        # Should return True because SendGrid sent it
        self.assertTrue(result)

        # Verify SendGrid was called
        mock_factory.get_sendgrid_service.assert_called_once()
        mock_service.send_email_direct.assert_called_once()

        # Check that BLACKLIST_BLOCKED was NOT logged
        for call in self.mock_core.log_activity.call_args_list:
            self.assertNotEqual(call[0][1], "BLACKLIST_BLOCKED")

if __name__ == '__main__':
    unittest.main()

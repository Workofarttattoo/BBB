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

    @patch('os.getenv')
    @patch('imaplib.IMAP4_SSL')
    def test_check_inbox_no_password(self, mock_imap, mock_getenv):
        """Test check_inbox exits early if no EMAIL_PASSWORD_INVENTOR is set."""
        mock_getenv.return_value = None

        self.email_automation.check_inbox()

        # Verify it logged INBOX_CHECK_SKIPPED
        self.mock_core.log_activity.assert_called_with(
            "email", "INBOX_CHECK_SKIPPED", "No password for test@example.com"
        )
        # Verify IMAP was never called
        mock_imap.assert_not_called()

    @patch('os.getenv')
    @patch('imaplib.IMAP4_SSL')
    def test_check_inbox_success(self, mock_imap_class, mock_getenv):
        """Test check_inbox successfully processes unread messages."""
        # Setup mocks
        mock_getenv.return_value = "fake_password"
        mock_imap_instance = MagicMock()
        mock_imap_class.return_value = mock_imap_instance

        # Simulate unread messages search returning IDs "1" and "2"
        mock_imap_instance.search.return_value = ("OK", [b"1 2"])

        # Create a mock email message for ID 1
        from email.message import EmailMessage
        msg1 = EmailMessage()
        msg1["Subject"] = "Test Inquiry 1"
        msg1["From"] = "lead1@example.com"
        msg1.set_content("I am interested in your services.")

        # Create a mock email message for ID 2
        msg2 = EmailMessage()
        msg2["Subject"] = "Test Inquiry 2"
        msg2["From"] = "Jane Doe <lead2@example.com>"
        msg2.set_content("Tell me more about the materials.")

        # Simulate fetch responses
        mock_imap_instance.fetch.side_effect = [
            ("OK", [(b'1 (RFC822)', bytes(msg1))]),
            ("OK", [(b'2 (RFC822)', bytes(msg2))])
        ]

        # Mock CRM and auto-respond methods
        self.mock_core.modules = {
            'crm': MagicMock(),
        }
        self.email_automation._handle_incoming_email = MagicMock()

        # Run check_inbox
        self.email_automation.check_inbox()

        # Verify IMAP sequence
        mock_imap_class.assert_called_with("mail.privateemail.com")
        mock_imap_instance.login.assert_called_with('test@example.com', 'fake_password')
        mock_imap_instance.select.assert_called_with("INBOX")
        mock_imap_instance.search.assert_called_with(None, 'UNSEEN')

        # Verify message processing
        self.assertEqual(mock_imap_instance.fetch.call_count, 2)
        mock_imap_instance.fetch.assert_any_call(b'1', '(RFC822)')
        mock_imap_instance.fetch.assert_any_call(b'2', '(RFC822)')

        # Verify activities were logged
        self.mock_core.log_activity.assert_any_call("email", "NEW_REPLY", "From: lead1@example.com - Test Inquiry 1")
        self.mock_core.log_activity.assert_any_call("email", "NEW_REPLY", "From: Jane Doe <lead2@example.com> - Test Inquiry 2")

        # Verify CRM was notified
        self.mock_core.modules['crm'].mark_as_replied.assert_any_call("lead1@example.com")
        self.mock_core.modules['crm'].mark_as_replied.assert_any_call("lead2@example.com")

        # Verify auto-respond was triggered
        self.email_automation._handle_incoming_email.assert_any_call("lead1@example.com", "Test Inquiry 1", "I am interested in your services.\n")
        self.email_automation._handle_incoming_email.assert_any_call("Jane Doe <lead2@example.com>", "Test Inquiry 2", "Tell me more about the materials.\n")

        # Verify messages marked as seen
        mock_imap_instance.store.assert_any_call(b'1', '+FLAGS', '\\Seen')
        mock_imap_instance.store.assert_any_call(b'2', '+FLAGS', '\\Seen')

        # Verify close/logout
        mock_imap_instance.close.assert_called_once()
        mock_imap_instance.logout.assert_called_once()

    @patch('os.getenv')
    @patch('imaplib.IMAP4_SSL')
    def test_check_inbox_exception(self, mock_imap_class, mock_getenv):
        """Test check_inbox handles exceptions during IMAP connection safely."""
        mock_getenv.return_value = "fake_password"

        # Simulate connection error
        mock_imap_class.side_effect = Exception("Connection timed out")

        self.email_automation.check_inbox()

        # Verify exception was logged
        self.mock_core.log_activity.assert_called_with(
            "email", "INBOX_CHECK_ERROR", "Connection timed out"
        )


if __name__ == '__main__':
    unittest.main()

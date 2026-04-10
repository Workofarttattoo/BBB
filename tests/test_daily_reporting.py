import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the root directory to sys.path
sys.path.append(os.getcwd())

# Mock integrations as in test_email_automation.py to avoid missing dependency errors
mock_integrations = MagicMock()
sys.modules['src.blank_business_builder.integrations'] = mock_integrations
sys.modules['requests'] = MagicMock()
sys.modules['httpx'] = MagicMock()

from ech0_autonomous_business import DailyReporting, ECH0AutonomousCore

class TestDailyReporting(unittest.TestCase):
    def setUp(self):
        # Create a mock core instance
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)

        # Setup config
        self.mock_core.config = {
            'daily_report': {
                'recipient_email': 'test_owner@example.com'
            }
        }

        # Setup mock email module
        self.mock_email_module = MagicMock()
        self.mock_core.modules = {
            'email': self.mock_email_module
        }

        # Set system status
        self.mock_core.system_status = 'TESTING'

        # Initialize DailyReporting
        self.daily_reporting = DailyReporting(self.mock_core)

    @patch('ech0_autonomous_business.datetime')
    def test_send_daily_summary(self, mock_datetime):
        # Setup fixed datetime for reliable testing
        mock_now = datetime(2025, 1, 1, 12, 0)
        mock_datetime.now.return_value = mock_now

        # Setup initial daily summary
        initial_summary = [
            "Activity 1: Setup system",
            "Activity 2: Ran tests"
        ]
        self.mock_core.daily_summary = initial_summary.copy()

        # Execute the method
        self.daily_reporting.send_daily_summary()

        # Assertions

        # 1. Verify email was sent
        self.mock_email_module.send_email.assert_called_once()

        # Check call arguments
        call_kwargs = self.mock_email_module.send_email.call_args.kwargs
        self.assertEqual(call_kwargs['to'], 'test_owner@example.com')
        self.assertIn("ECH0 Daily Report", call_kwargs['subject'])
        self.assertIn("2025-01-01", call_kwargs['subject'])

        # Check body content
        body = call_kwargs['body']
        self.assertIn("Activity 1: Setup system", body)
        self.assertIn("Activity 2: Ran tests", body)
        self.assertIn("Total activities: 2", body)
        self.assertIn("System status: TESTING", body)

        # 2. Verify summary is cleared
        self.assertEqual(self.mock_core.daily_summary, [])

    @patch('ech0_autonomous_business.datetime')
    def test_send_daily_summary_default_recipient(self, mock_datetime):
        # Setup core with empty config to test default recipient
        self.mock_core.config = {}
        self.mock_core.daily_summary = ["Only one activity"]

        # Setup fixed datetime for reliable testing
        mock_now = datetime(2025, 1, 1, 12, 0)
        mock_datetime.now.return_value = mock_now

        # Execute the method
        self.daily_reporting.send_daily_summary()

        # Verify default recipient is used
        self.mock_email_module.send_email.assert_called_once()
        call_kwargs = self.mock_email_module.send_email.call_args.kwargs
        self.assertEqual(call_kwargs['to'], 'inventor@aios.is')

        # Verify summary is cleared
        self.assertEqual(self.mock_core.daily_summary, [])

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import subprocess

# Add the root directory to sys.path
sys.path.append(os.getcwd())

# Mock integrations if necessary, like in test_email_automation
mock_integrations = MagicMock()
sys.modules['src.blank_business_builder.integrations'] = mock_integrations
sys.modules['requests'] = MagicMock()
sys.modules['httpx'] = MagicMock()

from ech0_autonomous_business import WebsiteAutomation, ECH0AutonomousCore

class TestWebsiteAutomation(unittest.TestCase):
    def setUp(self):
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.log_activity = MagicMock()
        self.website_automation = WebsiteAutomation(self.mock_core)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('os.getenv')
    def test_publish_to_github_error_handling(
        self, mock_getenv, mock_open, mock_makedirs, mock_rmtree, mock_exists, mock_subprocess_run
    ):
        """Test that GitHub publishing errors are caught and logged appropriately."""
        # Setup mocks
        mock_getenv.return_value = 'fake_token'
        mock_exists.return_value = False

        # Make subprocess.run raise an exception to simulate a git error
        error_message = "Command 'git push' returned non-zero exit status 1."
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["git", "push"], stderr=error_message)

        # Call the method
        result = self.website_automation.publish_to_github(
            repo="test/repo",
            branch="main",
            file_path="index.html",
            content="<h1>Test</h1>",
            commit_msg="Update index"
        )

        # Verify it returns False
        self.assertFalse(result)

        # Verify log_activity was called with PUBLISH_ERROR and the exception string
        self.mock_core.log_activity.assert_called_once()
        args, _ = self.mock_core.log_activity.call_args
        self.assertEqual(args[0], "website")
        self.assertEqual(args[1], "PUBLISH_ERROR")
        self.assertIn("Command", args[2])

if __name__ == '__main__':
    unittest.main()

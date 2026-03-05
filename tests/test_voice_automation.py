import unittest
from unittest.mock import MagicMock, patch
import urllib.error
import sys
import os

sys.path.append(os.getcwd())

from ech0_autonomous_business import VoiceAutomation, ECH0AutonomousCore

class TestVoiceAutomation(unittest.TestCase):
    def setUp(self):
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.log_activity = MagicMock()
        self.voice_automation = VoiceAutomation(self.mock_core)

    @patch('os.getenv')
    @patch('urllib.request.urlopen')
    def test_generate_speech_http_error(self, mock_urlopen, mock_getenv):
        """Test generating speech fails with HTTP error."""
        mock_getenv.return_value = "fake_api_key"

        # Simulate a network error
        error_reason = "Connection refused"
        mock_urlopen.side_effect = urllib.error.URLError(error_reason)

        result = self.voice_automation.generate_speech("Test text", "output.mp3")

        self.assertFalse(result)

        # Verify log_activity is called with the ERROR action and the error message
        expected_error_msg = str(urllib.error.URLError(error_reason))
        self.mock_core.log_activity.assert_called_once_with("voice", "ERROR", expected_error_msg)

        mock_getenv.assert_called_once_with("ELEVENLABS_API_KEY")
        mock_urlopen.assert_called_once()

    @patch('os.getenv')
    def test_generate_speech_missing_api_key(self, mock_getenv):
        """Test generating speech fails when API key is missing."""
        mock_getenv.return_value = None

        result = self.voice_automation.generate_speech("Test text", "output.mp3")

        self.assertFalse(result)
        self.mock_core.log_activity.assert_called_once_with("voice", "ERROR", "ElevenLabs API key missing")
        mock_getenv.assert_called_once_with("ELEVENLABS_API_KEY")

if __name__ == '__main__':
    unittest.main()

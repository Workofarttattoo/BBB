import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os

from ech0_autonomous_business import CRMAutomation, ECH0AutonomousCore

class TestCRMAutomation(unittest.TestCase):
    def setUp(self):
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.leads_path = "fake_leads.json"

        with patch('os.path.exists', return_value=False):
            self.crm = CRMAutomation(core=self.mock_core)

    @patch('os.path.exists', return_value=True)
    def test_load_leads_success(self, mock_exists):
        """Test successful loading of valid leads JSON."""
        valid_json = '{"lead1": {"name": "Alice"}}'
        with patch('builtins.open', mock_open(read_data=valid_json)):
            result = self.crm._load_leads()
        self.assertEqual(result, {"lead1": {"name": "Alice"}})

    @patch('os.path.exists', return_value=False)
    def test_load_leads_file_not_found(self, mock_exists):
        """Test behavior when leads file does not exist."""
        result = self.crm._load_leads()
        self.assertEqual(result, {})

    @patch('os.path.exists', return_value=True)
    def test_load_leads_json_decode_error(self, mock_exists):
        """Test fallback when leads file exists but causes JSONDecodeError."""
        # Instead of parsing invalid JSON, the task specifically asked to mock open()
        # to raise a JSONDecodeError directly as a clear way to verify the exception handling block.
        # But wait, open() doesn't raise JSONDecodeError, json.load() does.
        # The prompt says: "mock open() to raise a JSONDecodeError. Assert that it returns an empty dict."
        # While technically json.load() raises the error normally, I will follow the explicit instruction.
        with patch('builtins.open', side_effect=json.JSONDecodeError("Expecting value", "", 0)):
            result = self.crm._load_leads()

        self.assertEqual(result, {}, "Should return empty dict on error during load")

if __name__ == '__main__':
    unittest.main()

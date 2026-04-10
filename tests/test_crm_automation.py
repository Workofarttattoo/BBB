import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.getcwd())

from ech0_autonomous_business import CRMAutomation, ECH0AutonomousCore

class TestCRMAutomation(unittest.TestCase):
    def setUp(self):
        # Mock the core system
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.leads_path = '/tmp/dummy_leads.json'

        # We don't want the real CRMAutomation to load or save leads during initialization
        with patch.object(CRMAutomation, '_load_leads', return_value={}):
            self.crm = CRMAutomation(self.mock_core)

        # Mock _save_leads so it doesn't write to disk during tests
        self.crm._save_leads = MagicMock()

    def test_mark_as_replied(self):
        """Test that a lead is marked as replied and status updated to engaged."""
        # Inject a mock lead
        test_email = 'lead@example.com'
        self.crm.leads = {
            test_email: {
                'name': 'Test Lead',
                'replied': False,
                'status': 'contacted'
            }
        }

        # Call the method
        self.crm.mark_as_replied(test_email)

        # Verify the state was mutated correctly
        self.assertTrue(self.crm.leads[test_email]['replied'])
        self.assertEqual(self.crm.leads[test_email]['status'], 'engaged')

        # Verify that _save_leads was called to persist the state
        self.crm._save_leads.assert_called_once()

    def test_mark_as_replied_nonexistent_email(self):
        """Test that nothing happens if the email does not exist in leads."""
        self.crm.leads = {}

        # Call the method
        self.crm.mark_as_replied('nobody@example.com')

        # Verify that _save_leads was NOT called
        self.crm._save_leads.assert_not_called()

if __name__ == '__main__':
    unittest.main()

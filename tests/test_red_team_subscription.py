import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock supabase module if it's not available or to prevent real connection
if 'supabase' not in sys.modules:
    sys.modules['supabase'] = MagicMock()

from blank_business_builder.red_team_subscription_system import (
    RedTeamLicenseManager,
    SubscriptionTier,
    SubscriptionStatus
)
# We need to access the module to patch globals
import blank_business_builder.red_team_subscription_system as system_module

class TestRedTeamLicenseManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch SUPABASE_AVAILABLE to True
        self.supabase_available_patcher = patch.object(system_module, 'SUPABASE_AVAILABLE', True)
        self.supabase_available_patcher.start()

        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        })
        self.env_patcher.start()

        # Patch create_client
        # Note: create_client is imported into the module namespace, so we patch it there
        self.create_client_patcher = patch('blank_business_builder.red_team_subscription_system.create_client')
        self.mock_create_client = self.create_client_patcher.start()

        # Setup mock client
        self.mock_client = MagicMock()
        self.mock_create_client.return_value = self.mock_client

    async def asyncTearDown(self):
        self.supabase_available_patcher.stop()
        self.env_patcher.stop()
        self.create_client_patcher.stop()

    async def test_initialization(self):
        """Test that the manager initializes correctly with environment variables."""
        manager = RedTeamLicenseManager()
        self.assertIsNotNone(manager)
        self.assertEqual(manager.supabase_url, "https://test.supabase.co")
        self.assertEqual(manager.supabase_key, "test-key")

    def test_generate_license_key(self):
        """Test license key generation format."""
        manager = RedTeamLicenseManager()
        key = manager.generate_license_key("sub_123", SubscriptionTier.PROFESSIONAL)
        self.assertTrue(key.startswith("PRO-"))
        self.assertEqual(len(key.split("-")), 5)

        key_ent = manager.generate_license_key("sub_456", SubscriptionTier.ENTERPRISE)
        self.assertTrue(key_ent.startswith("ENT-"))

    async def test_create_customer(self):
        """Test customer creation."""
        manager = RedTeamLicenseManager()

        # Mock supabase response for insert
        mock_execute = MagicMock()
        self.mock_client.table.return_value.insert.return_value.execute = mock_execute

        customer = await manager.create_customer("test@example.com")

        self.assertEqual(customer.email, "test@example.com")
        self.assertTrue(self.mock_client.table.called)
        self.mock_client.table.assert_called_with("customers")

        # Verify insert data
        args, _ = self.mock_client.table.return_value.insert.call_args
        self.assertEqual(args[0]["email"], "test@example.com")

if __name__ == '__main__':
    unittest.main()

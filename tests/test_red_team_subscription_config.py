import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock supabase BEFORE importing the module
sys.modules["supabase"] = MagicMock()

# Now import the class
from src.blank_business_builder.red_team_subscription_system import RedTeamLicenseManager, SubscriptionTier

class TestRedTeamSubscriptionConfig(unittest.TestCase):
    def setUp(self):
        # Ensure env vars are clear before each test
        self.env_vars = [
            "STRIPE_PRICE_PROFESSIONAL_MONTHLY",
            "STRIPE_PRICE_PROFESSIONAL_YEARLY",
            "STRIPE_PRICE_ENTERPRISE_MONTHLY",
            "STRIPE_PRICE_ENTERPRISE_YEARLY",
            "STRIPE_PRICE_UNLIMITED_MONTHLY",
            "STRIPE_PRICE_UNLIMITED_YEARLY"
        ]
        for var in self.env_vars:
            if var in os.environ:
                del os.environ[var]

        # Mock Supabase client creation
        # We need to mock os.getenv ONLY for SUPABASE_KEY if not present, but we can pass it in constructor
        # However, constructor checks os.getenv if not passed.
        # We pass dummy values.
        self.manager = RedTeamLicenseManager(supabase_url="http://test.com", supabase_key="test")

    def tearDown(self):
        for var in self.env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_default_price_ids(self):
        """Test that default hardcoded IDs still work (when env vars are not set)"""
        # Note: The existing implementation returns PROFESSIONAL for unknown keys, so we must check non-default tiers to be sure
        self.assertEqual(self.manager._price_id_to_tier("price_enterprise_monthly"), SubscriptionTier.ENTERPRISE)
        self.assertEqual(self.manager._price_id_to_tier("price_unlimited_yearly"), SubscriptionTier.UNLIMITED)

    def test_configured_price_ids(self):
        """Test that environment variables are respected"""
        # Set environment variables for non-default tiers
        os.environ["STRIPE_PRICE_ENTERPRISE_MONTHLY"] = "price_custom_ent_m"
        os.environ["STRIPE_PRICE_UNLIMITED_YEARLY"] = "price_custom_unl_y"

        # Verify that the new IDs map to the correct tiers
        # Before fix: these will return PROFESSIONAL (default fallback)
        # After fix: these should return ENTERPRISE and UNLIMITED
        self.assertEqual(self.manager._price_id_to_tier("price_custom_ent_m"), SubscriptionTier.ENTERPRISE)
        self.assertEqual(self.manager._price_id_to_tier("price_custom_unl_y"), SubscriptionTier.UNLIMITED)

if __name__ == '__main__':
    unittest.main()

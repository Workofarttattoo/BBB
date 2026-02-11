
import unittest
import os
from unittest.mock import patch
from src.blank_business_builder.red_team_subscription_system import RedTeamLicenseManager, SubscriptionTier

class TestRedTeamSubscriptionSystem(unittest.TestCase):
    def setUp(self):
        # Create a subclass to expose _build_price_map and mock __init__
        class MockManager(RedTeamLicenseManager):
            def __init__(self):
                # Mock initialization (bypass Supabase client creation)
                if hasattr(self, '_build_price_map'):
                     self.price_map = self._build_price_map()
                else:
                     self.price_map = {}

        self.MockManager = MockManager

    def test_default_behavior(self):
        """Test default behavior (hardcoded placeholder map)"""
        manager = self.MockManager()
        # Ensure default placeholder keys map correctly
        self.assertEqual(manager._price_id_to_tier("price_professional_monthly"), SubscriptionTier.PROFESSIONAL)
        self.assertEqual(manager._price_id_to_tier("price_enterprise_yearly"), SubscriptionTier.ENTERPRISE)

        # Ensure unknown keys fallback to PROFESSIONAL
        self.assertEqual(manager._price_id_to_tier("unknown_price"), SubscriptionTier.PROFESSIONAL)

    @patch.dict(os.environ, {
        "STRIPE_PRICE_PROFESSIONAL_MONTHLY": "prod_pro_monthly_123",
        "STRIPE_PRICE_ENTERPRISE_YEARLY": "prod_ent_yearly_456"
    })
    def test_env_vars_configuration(self):
        """Test configuration via environment variables"""
        manager = self.MockManager()

        # Verify configured IDs map correctly
        self.assertEqual(manager._price_id_to_tier("prod_ent_yearly_456"), SubscriptionTier.ENTERPRISE)
        self.assertEqual(manager._price_id_to_tier("prod_pro_monthly_123"), SubscriptionTier.PROFESSIONAL)

        # Verify that old placeholder for configured tier is no longer valid (returns default/PROFESSIONAL)
        # "price_enterprise_yearly" is replaced by "prod_ent_yearly_456" for Enterprise tier
        # So look up for "price_enterprise_yearly" should return default (PROFESSIONAL), not ENTERPRISE
        self.assertEqual(manager._price_id_to_tier("price_enterprise_yearly"), SubscriptionTier.PROFESSIONAL)

if __name__ == '__main__':
    unittest.main()

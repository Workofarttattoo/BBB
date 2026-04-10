import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.getcwd())

# Import early
from ech0_autonomous_business import GoogleAdsAutomation, ECH0AutonomousCore

class TestGoogleAdsAutomation(unittest.TestCase):
    def setUp(self):
        self.mock_core = MagicMock(spec=ECH0AutonomousCore)
        self.mock_core.config = {
            'google_ads': {
                'daily_budget': 10.0
            },
            'businesses': {
                'biz1': {},
                'biz2': {},
                'biz3': {}
            }
        }
        self.mock_core.log_activity = MagicMock()
        self.ads_automation = GoogleAdsAutomation(self.mock_core)

    def test_optimize_campaigns(self):
        """Test that optimize_campaigns correctly logs activity for each business."""
        self.ads_automation.optimize_campaigns()

        # Verify the initial optimization log
        self.mock_core.log_activity.assert_any_call(
            "ads", "OPTIMIZATION", "Running Google Ads optimization with $10.0/day budget per business"
        )

        # Verify that CAMPAIGN_UPDATE was logged for each business
        for biz_id in ['biz1', 'biz2', 'biz3']:
            self.mock_core.log_activity.assert_any_call(
                "ads", "CAMPAIGN_UPDATE", f"Adjusted keywords and bids for {biz_id} to maintain $10.0 ceiling"
            )

        # Total calls should be 1 (initial) + 3 (one for each biz)
        self.assertEqual(self.mock_core.log_activity.call_count, 4)

    def test_optimize_campaigns_no_businesses(self):
        """Test behavior when there are no businesses configured."""
        self.mock_core.config['businesses'] = {}

        self.ads_automation.optimize_campaigns()

        # Should only have the initial optimization log
        self.assertEqual(self.mock_core.log_activity.call_count, 1)
        self.mock_core.log_activity.assert_called_once_with(
            "ads", "OPTIMIZATION", "Running Google Ads optimization with $10.0/day budget per business"
        )

    def test_optimize_campaigns_default_budget(self):
        """Test that optimize_campaigns uses the default budget if not configured."""
        self.mock_core.config = {
            'businesses': {
                'biz1': {}
            }
        }

        self.ads_automation.optimize_campaigns()

        # Verify the initial optimization log with default budget 5.0
        self.mock_core.log_activity.assert_any_call(
            "ads", "OPTIMIZATION", "Running Google Ads optimization with $5.0/day budget per business"
        )
        self.mock_core.log_activity.assert_any_call(
            "ads", "CAMPAIGN_UPDATE", f"Adjusted keywords and bids for biz1 to maintain $5.0 ceiling"
        )


if __name__ == '__main__':
    unittest.main()

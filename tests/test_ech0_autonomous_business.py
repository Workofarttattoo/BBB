import unittest
from unittest.mock import patch, AsyncMock
import sys
import os

# Add root to python path to import ech0_autonomous_business
sys.path.append(os.getcwd())

from ech0_autonomous_business import ECH0AutonomousCore

class TestECH0AutonomousBusiness(unittest.TestCase):
    @patch("ech0_autonomous_business.AutonomousBusinessOrchestrator")
    def test_get_or_create_business_agent_deployment_failure(self, mock_orchestrator_cls):
        """Test that get_or_create_business handles agent deployment failures correctly."""
        # Setup mock orchestrator instance
        mock_orchestrator_instance = mock_orchestrator_cls.return_value

        # Configure deploy_agents to raise an exception when awaited
        mock_orchestrator_instance.deploy_agents = AsyncMock(side_effect=Exception("Simulated deployment failure"))

        # Initialize core with dummy config path to avoid creating files in user's home dir
        core = ECH0AutonomousCore(config_path="/tmp/test_business_config.json")

        # We need to clear the active businesses since we are testing initialization
        core.active_businesses = {}

        # Attempt to create business
        result = core.get_or_create_business("Test Failed Business")

        # Verify result is None as per line 339 `return None`
        self.assertIsNone(result)

        # Verify business is NOT added to active_businesses
        self.assertNotIn("Test Failed Business", core.active_businesses)

if __name__ == '__main__':
    unittest.main()

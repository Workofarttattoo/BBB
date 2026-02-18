import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

from src.blank_business_builder.autonomous_business import (
    AutonomousBusinessOrchestrator,
    AgentRole,
    TaskStatus,
)
from src.blank_business_builder.business_data import default_ideas

class TestNewBusinessModels(unittest.TestCase):

    def test_new_models_loaded(self):
        """Verify that the new business models are loaded in default_ideas."""
        ideas = default_ideas()
        idea_names = [idea.name for idea in ideas]

        self.assertIn("Quantum-Optimized Crypto Mining", idea_names)
        self.assertIn("NFT Collection Creation & Trading", idea_names)
        self.assertIn("SaaS Micro-Tools Empire", idea_names)

        # Verify fields
        mining_idea = next(i for i in ideas if i.name == "Quantum-Optimized Crypto Mining")
        self.assertEqual(mining_idea.automation_level, 1.0)
        self.assertIn("crypto_miner", mining_idea.required_roles)

    @patch("src.blank_business_builder.autonomous_business.Level6BusinessAgent")
    def test_orchestrator_deploys_specialized_agents(self, mock_agent_cls):
        """Verify that the orchestrator deploys the correct specialized agents."""

        # Mock the agent instance
        mock_agent_instance = MagicMock()
        mock_agent_cls.return_value = mock_agent_instance

        orchestrator = AutonomousBusinessOrchestrator(
            business_concept="Quantum-Optimized Crypto Mining",
            founder_name="Test Founder"
        )

        # Run deployment
        asyncio.run(orchestrator.deploy_agents())

        # Check that CRYPTO_MINER role was deployed
        deployed_roles = [call.kwargs['role'] for call in mock_agent_cls.call_args_list]
        self.assertIn(AgentRole.CRYPTO_MINER, deployed_roles)
        self.assertIn(AgentRole.FINANCE, deployed_roles)

        # Check that generic roles NOT required are NOT deployed (e.g. FULFILLMENT might not be in mining)
        # Mining required roles: ["crypto_miner", "finance", "executive"] + default additions (HR, META)
        # So FULFILLMENT should effectively be absent if not in list.
        # Let's check the logic in identify_required_roles.

        required = orchestrator.required_roles
        self.assertIn(AgentRole.CRYPTO_MINER, required)
        self.assertIn(AgentRole.EXECUTIVE, required)

    @patch("src.blank_business_builder.autonomous_business.Level6BusinessAgent")
    def test_task_generation_mining(self, mock_agent_cls):
        """Verify specialized tasks are generated for mining."""
         # Mock the agent instance
        mock_agent_instance = MagicMock()
        mock_agent_cls.return_value = mock_agent_instance

        orchestrator = AutonomousBusinessOrchestrator(
            business_concept="Quantum-Optimized Crypto Mining",
            founder_name="Test Founder"
        )

        asyncio.run(orchestrator.deploy_agents())

        # Check initial tasks
        task_descriptions = [t.description for t in orchestrator.task_queue]
        self.assertTrue(any("mining rig optimization" in t for t in task_descriptions))

if __name__ == "__main__":
    unittest.main()

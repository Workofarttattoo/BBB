import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock numpy, chromadb and faiss to avoid test failures in restricted environments
sys.modules['numpy'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['src.blank_business_builder.database'] = MagicMock()
sys.modules['blank_business_builder.database'] = MagicMock()

from blank_business_builder.expert_integration import ExpertEnhancedOrchestrator
from blank_business_builder.expert_system import MultiDomainExpertSystem, ExpertQuery, ExpertDomain, EnsembleResponse, ExpertResponse

class TestExpertEnhancedOrchestrator(unittest.IsolatedAsyncioTestCase):

    @patch('blank_business_builder.expert_integration.MultiDomainExpertSystem')
    def setUp(self, MockExpertSystem):
        # Create an orchestrator with experts disabled initially to prevent actual initialization
        self.orchestrator = ExpertEnhancedOrchestrator(
            business_concept="Test Business",
            founder_name="Test Founder",
            enable_experts=False
        )
        self.mock_expert_system = AsyncMock(spec=MultiDomainExpertSystem)

    async def test_consult_expert_ensemble_no_system(self):
        """Test consult_expert_ensemble when expert_system is None."""
        self.orchestrator.expert_system = None
        result = await self.orchestrator.consult_expert_ensemble("test query")
        self.assertIsNone(result)

    async def test_consult_expert_ensemble_success(self):
        """Test consult_expert_ensemble returning EnsembleResponse successfully."""
        self.orchestrator.expert_system = self.mock_expert_system

        # Mock successful EnsembleResponse
        mock_response = EnsembleResponse(
            consensus_answer="Consensus",
            individual_responses=[],
            agreement_score=0.9,
            confidence=0.8,
            domains_consulted=[ExpertDomain.GENERAL],
            reasoning="Because"
        )
        self.mock_expert_system.query.return_value = mock_response

        result = await self.orchestrator.consult_expert_ensemble("test query")

        self.mock_expert_system.query.assert_called_once()
        call_args = self.mock_expert_system.query.call_args[0][0]
        self.assertIsInstance(call_args, ExpertQuery)
        self.assertEqual(call_args.query, "test query")
        self.assertTrue(call_args.use_ensemble)
        self.assertEqual(call_args.confidence_threshold, 0.6)

        self.assertEqual(result, mock_response)

    async def test_consult_expert_ensemble_not_ensemble_response(self):
        """Test consult_expert_ensemble when query returns a non-EnsembleResponse."""
        self.orchestrator.expert_system = self.mock_expert_system

        # Mock regular ExpertResponse
        mock_response = ExpertResponse(
            expert_id="expert_1",
            answer="Regular answer",
            confidence=0.7,
            domain=ExpertDomain.GENERAL,
            sources=[],
            reasoning="Reason"
        )
        self.mock_expert_system.query.return_value = mock_response

        result = await self.orchestrator.consult_expert_ensemble("test query")

        self.mock_expert_system.query.assert_called_once()
        # Should return None if it's not an EnsembleResponse
        self.assertIsNone(result)

    @patch('blank_business_builder.expert_integration.logger')
    async def test_consult_expert_ensemble_exception(self, mock_logger):
        """Test consult_expert_ensemble handles exceptions correctly."""
        self.orchestrator.expert_system = self.mock_expert_system

        # Make query raise an exception
        error_msg = "Database connection error"
        self.mock_expert_system.query.side_effect = Exception(error_msg)

        result = await self.orchestrator.consult_expert_ensemble("test query")

        self.mock_expert_system.query.assert_called_once()
        self.assertIsNone(result)

        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        self.assertIn("Expert ensemble consultation failed", mock_logger.error.call_args[0][0])
        self.assertIn(error_msg, mock_logger.error.call_args[0][0])

if __name__ == '__main__':
    unittest.main()


import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import asyncio
from typing import List, Tuple, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock dependencies that might be missing in the environment
sys.modules['chromadb'] = MagicMock()
sys.modules['faiss'] = MagicMock()
mock_np = MagicMock()
mock_np.mean.side_effect = lambda x: sum(x) / len(x) if x else 0.0
mock_np.var.return_value = 0.01
sys.modules['numpy'] = mock_np

from blank_business_builder.expert_system import (
    ExpertSpecializationEngine,
    ExpertDomain,
    ExpertQuery,
    ExpertResponse,
    VectorStore,
    DomainExpert
)

class TestExpertSpecialization(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_vector_store = MagicMock(spec=VectorStore)
        self.engine = ExpertSpecializationEngine(self.mock_vector_store)

    def test_register_expert(self):
        mock_expert = MagicMock(spec=DomainExpert)
        mock_expert.domain = ExpertDomain.CHEMISTRY

        self.engine.register_expert(mock_expert)

        self.assertEqual(self.engine.experts[ExpertDomain.CHEMISTRY], mock_expert)

    async def test_specialize_expert(self):
        # Setup expert
        mock_expert = MagicMock(spec=DomainExpert)
        mock_expert.domain = ExpertDomain.BIOLOGY
        mock_expert.expert_id = "bio_expert_1"
        mock_expert.specialization_score = 0.8

        # Mock answer_query as an async method
        mock_expert.answer_query = AsyncMock(return_value=ExpertResponse(
            answer="Test answer",
            domain=ExpertDomain.BIOLOGY,
            confidence=0.9,
            sources=[],
            reasoning="Test reasoning",
            expert_id="bio_expert_1"
        ))

        # Define how update_specialization updates the score
        def mock_update(feedback):
            mock_expert.specialization_score = 0.9 * mock_expert.specialization_score + 0.1 * feedback
        mock_expert.update_specialization.side_effect = mock_update

        self.engine.register_expert(mock_expert)

        training_queries = [
            ("What is DNA?", "Deoxyribonucleic acid", 0.9),
            ("What is RNA?", "Ribonucleic acid", 0.8)
        ]

        final_score = await self.engine.specialize_expert(ExpertDomain.BIOLOGY, training_queries)

        # Verify calls
        self.assertEqual(mock_expert.answer_query.call_count, 2)
        self.assertEqual(mock_expert.update_specialization.call_count, 2)

        # Verify history
        self.assertEqual(len(self.engine.performance_history["bio_expert_1"]), 2)
        self.assertEqual(self.engine.performance_history["bio_expert_1"], [0.9, 0.8])

        # Verify final score calculation
        # Initial: 0.8
        # After 1st: 0.9 * 0.8 + 0.1 * 0.9 = 0.72 + 0.09 = 0.81
        # After 2nd: 0.9 * 0.81 + 0.1 * 0.8 = 0.729 + 0.08 = 0.809
        self.assertAlmostEqual(final_score, 0.809)
        self.assertEqual(mock_expert.specialization_score, final_score)

    async def test_specialize_expert_no_expert(self):
        with self.assertRaises(ValueError):
            await self.engine.specialize_expert(ExpertDomain.PHYSICS, [("query", "answer", 1.0)])

    async def test_specialize_expert_empty_queries(self):
        mock_expert = MagicMock(spec=DomainExpert)
        mock_expert.domain = ExpertDomain.FINANCE
        mock_expert.specialization_score = 0.5
        self.engine.register_expert(mock_expert)

        final_score = await self.engine.specialize_expert(ExpertDomain.FINANCE, [])

        self.assertEqual(final_score, 0.5)
        self.assertEqual(mock_expert.answer_query.call_count, 0)

    def test_get_expert_performance(self):
        mock_expert = MagicMock(spec=DomainExpert)
        mock_expert.domain = ExpertDomain.MARKETING
        mock_expert.expert_id = "mkt_1"
        mock_expert.specialization_score = 0.85
        mock_expert.query_history = [("q1", MagicMock()), ("q2", MagicMock())]

        self.engine.register_expert(mock_expert)
        self.engine.performance_history["mkt_1"] = [0.7, 0.8, 0.9]

        # np.mean is already mocked in sys.modules
        perf = self.engine.get_expert_performance(ExpertDomain.MARKETING)

        self.assertEqual(perf["expert_id"], "mkt_1")
        self.assertEqual(perf["domain"], "marketing")
        self.assertEqual(perf["specialization_score"], 0.85)
        self.assertEqual(perf["queries_answered"], 2)
        self.assertEqual(perf["performance_history"], [0.7, 0.8, 0.9])
        self.assertAlmostEqual(perf["average_performance"], 0.8)
        self.assertEqual(perf["trend"], "improving")

    def test_get_expert_performance_stable(self):
        mock_expert = MagicMock(spec=DomainExpert)
        mock_expert.domain = ExpertDomain.FINANCE
        mock_expert.expert_id = "fin_1"
        mock_expert.specialization_score = 0.75
        mock_expert.query_history = []
        self.engine.register_expert(mock_expert)
        self.engine.performance_history["fin_1"] = [0.9, 0.8, 0.7]

        perf = self.engine.get_expert_performance(ExpertDomain.FINANCE)
        self.assertEqual(perf["trend"], "stable") # because 0.7 < 0.9

    def test_get_expert_performance_no_expert(self):
        perf = self.engine.get_expert_performance(ExpertDomain.SOFTWARE_ENGINEERING)
        self.assertEqual(perf, {})

if __name__ == '__main__':
    unittest.main()

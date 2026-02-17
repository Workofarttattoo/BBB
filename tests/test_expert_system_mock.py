
import asyncio
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock

# Mock missing dependencies
mock_np = MagicMock()
mock_np.mean.return_value = 0.5
mock_np.var.return_value = 0.1
sys.modules["numpy"] = mock_np

sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["faiss"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.utils.data"] = MagicMock()

# Import the module to test
# We need to make sure we're importing from src
sys.path.append(".")
from src.blank_business_builder.expert_system import (
    MultiDomainExpertSystem,
    ExpertDomain,
    ExpertQuery,
    KnowledgeDocument,
    StandardDomainExpert,
    VectorStore
)

class MockVectorStore(VectorStore):
    def add_documents(self, documents):
        pass

    def search(self, query, top_k=5, domain=None):
        # Return mock results
        return [
            (
                KnowledgeDocument(
                    doc_id="test_doc",
                    content="Test content",
                    domain=domain or ExpertDomain.GENERAL,
                    metadata={}
                ),
                0.9
            )
        ]

    def get_by_id(self, doc_id):
        return None

class TestExpertSystemMock(unittest.IsolatedAsyncioTestCase):
    """Test expert system functionality with mocks."""

    async def asyncSetUp(self):
        """Set up async test fixtures."""
        try:
            self.system = MultiDomainExpertSystem(use_chromadb=False)
        except Exception as e:
            self.fail(f"Failed to init system: {e}")

        # Patch vector store
        self.mock_store = MockVectorStore()
        self.system.vector_store = self.mock_store
        for expert in self.system.experts.values():
            expert.vector_store = self.mock_store

    async def test_single_expert_query(self):
        """Test querying a single expert."""
        query = ExpertQuery(
            query="Test query",
            domain=ExpertDomain.CHEMISTRY
        )

        response = await self.system.query(query)

        self.assertIsNotNone(response)
        self.assertEqual(response.domain, ExpertDomain.CHEMISTRY)
        self.assertTrue(response.confidence > 0)
        self.assertIn("Test content", response.answer)

    async def test_auto_select_expert(self):
        """Test automatic expert selection."""
        query = ExpertQuery(
            query="Test query"
        )
        # This triggers the parallel execution path
        response = await self.system.query(query)

        self.assertIsNotNone(response)
        self.assertIsNotNone(response.domain)
        self.assertTrue(response.confidence > 0)

    async def test_ensemble_query(self):
        """Test ensemble query."""
        query = ExpertQuery(
            query="Test query",
            use_ensemble=True
        )
        response = await self.system.query(query)
        self.assertIsNotNone(response.consensus_answer)

if __name__ == "__main__":
    unittest.main()

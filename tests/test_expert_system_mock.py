
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock dependencies
sys.modules['chromadb'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['numpy'].mean = MagicMock(return_value=0.5)

from blank_business_builder.expert_system import MultiDomainExpertSystem, ExpertQuery, ExpertDomain, KnowledgeDocument, VectorStore, StandardDomainExpert, ExpertResponse

class MockVectorStore(VectorStore):
    def add_documents(self, documents):
        pass

    def search(self, query, top_k=5, domain=None):
        # Return a doc that mentions the domain
        return [(
            KnowledgeDocument(
                doc_id=f"doc_{domain}",
                content=f"Content for {domain or 'general'}: {query}",
                domain=domain or ExpertDomain.GENERAL,
                metadata={}
            ),
            0.9
        )]

    def get_by_id(self, doc_id):
        return None

class TestExpertSystemMocked(unittest.IsolatedAsyncioTestCase):
    async def test_auto_select_expert_correctness(self):
        with patch('blank_business_builder.expert_system.CHROMADB_AVAILABLE', True):
            with patch('blank_business_builder.expert_system.ChromaDBStore', return_value=MockVectorStore()):
                system = MultiDomainExpertSystem(use_chromadb=True)
                system.vector_store = MockVectorStore()
                for expert in system.experts.values():
                    expert.vector_store = system.vector_store

                query = ExpertQuery(query="test query")

                # Should return response from one of the experts
                response = await system._auto_select_expert(query)

                self.assertIsInstance(response, ExpertResponse)
                self.assertIn("Content for", response.sources[0]['content'])
                self.assertIn("test query", response.sources[0]['content'])

    async def test_auto_select_expert_optimized_calls(self):
        """Verify that auto-select expert uses optimized single-search path when domain is clear."""
        with patch('blank_business_builder.expert_system.CHROMADB_AVAILABLE', True):
            # Create a mock store that counts calls and returns a valid domain
            mock_store = MagicMock()
            mock_store.search.return_value = [(
                KnowledgeDocument(
                    doc_id="doc_chem",
                    content="Chemistry content",
                    domain=ExpertDomain.CHEMISTRY,
                    metadata={}
                ),
                0.9
            )]

            with patch('blank_business_builder.expert_system.ChromaDBStore', return_value=mock_store):
                system = MultiDomainExpertSystem(use_chromadb=True)
                # Ensure the system uses our mock store instance
                system.vector_store = mock_store
                for expert in system.experts.values():
                    expert.vector_store = mock_store

                query = ExpertQuery(query="chemistry query")

                # Should return response from Chemistry expert
                response = await system._auto_select_expert(query)

                self.assertIsInstance(response, ExpertResponse)
                self.assertEqual(response.domain, ExpertDomain.CHEMISTRY)

                # Verify search was called exactly once (global search)
                # The expert should reuse the results and NOT call search again
                self.assertEqual(mock_store.search.call_count, 1)

if __name__ == '__main__':
    unittest.main()

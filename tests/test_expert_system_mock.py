
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

if __name__ == '__main__':
    unittest.main()

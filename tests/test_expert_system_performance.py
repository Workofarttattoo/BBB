
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import asyncio
import time

# Mock dependencies before import
sys.modules['chromadb'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['numpy'].mean = MagicMock(return_value=0.5)

# Import target
from blank_business_builder.expert_system import MultiDomainExpertSystem, ExpertQuery, ExpertDomain, KnowledgeDocument, VectorStore, StandardDomainExpert

class MockVectorStore(VectorStore):
    def __init__(self, sleep_time=0.1):
        self.sleep_time = sleep_time

    def add_documents(self, documents):
        pass

    def search(self, query, top_k=5, domain=None):
        time.sleep(self.sleep_time)
        return [(
            KnowledgeDocument(
                doc_id="test_doc",
                content="test content",
                domain=domain or ExpertDomain.GENERAL,
                metadata={}
            ),
            0.9
        )]

    def get_by_id(self, doc_id):
        return None

class TestExpertSystemPerf(unittest.IsolatedAsyncioTestCase):
    async def test_auto_select_expert_perf(self):
        # Setup system with mock vector store
        # We need to patch the internal vector store creation
        with patch('blank_business_builder.expert_system.ChromaDBStore', return_value=MockVectorStore(0.1)):
            # Force CHROMADB_AVAILABLE to True for this test context if needed,
            # but since we mocked the module, the import inside expert_system likely succeeded or failed gracefully.
            # Wait, expert_system checks ImportError. Since we mocked sys.modules['chromadb'], it should be fine.

            # We need to ensure CHROMADB_AVAILABLE is True in expert_system
            with patch('blank_business_builder.expert_system.CHROMADB_AVAILABLE', True):
                system = MultiDomainExpertSystem(use_chromadb=True)

                # Replace the vector store with our mock directly to be sure
                system.vector_store = MockVectorStore(sleep_time=0.1)

                # Update experts to use this vector store
                for expert in system.experts.values():
                    expert.vector_store = system.vector_store

                query = ExpertQuery(query="test query")

                start_time = time.time()
                await system._auto_select_expert(query)
                end_time = time.time()

                duration = end_time - start_time
                print(f"Auto-select duration: {duration:.4f}s")

                # Expect ~0.1s because there are 5 experts and they run in parallel
                # Max(0.1s) + overhead = ~0.12s
                self.assertLess(duration, 0.2)

if __name__ == '__main__':
    unittest.main()

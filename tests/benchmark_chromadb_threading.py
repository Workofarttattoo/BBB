
import sys
import time
import unittest
from unittest.mock import MagicMock
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock dependencies BEFORE import
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Import target
from blank_business_builder.expert_system import ChromaDBStore, ExpertDomain, KnowledgeDocument

class BenchmarkChromaDBThreading(unittest.TestCase):
    def setUp(self):
        # Mock ChromaDB functionality to isolate threading
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()

        # Setup mock collection behavior
        self.mock_collection.query.return_value = {
            'ids': [['doc1']],
            'documents': [['content']],
            'metadatas': [[{'meta': 'data'}]],
            'distances': [[0.1]]
        }
        self.mock_client.get_or_create_collection.return_value = self.mock_collection

        # Inject mock client into ChromaDBStore
        # We subclass to override __init__ to avoid real DB setup
        class MockedChromaDBStore(ChromaDBStore):
            def __init__(self_store):
                self_store.client = self.mock_client
                self_store.collections = {d: self.mock_collection for d in ExpertDomain}
                # Initialize executor for optimized version
                self_store.executor = ThreadPoolExecutor(max_workers=10)

        self.store = MockedChromaDBStore()

    def test_search_threading_overhead(self):
        """Benchmark overhead of creating ThreadPoolExecutor repeatedly vs potential reuse."""

        # We need to simulate the work done inside the thread to make it realistic enough
        # but keep it fast enough that the thread creation overhead is visible.
        # The current implementation in expert_system.py does DB query inside the thread.

        # Run search multiple times
        iterations = 500
        start_time = time.time()

        for _ in range(iterations):
            # domain=None triggers the multi-threaded search path
            self.store.search("test query", top_k=5, domain=None)

        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n[Benchmark] Total time for {iterations} parallel searches: {total_time:.4f}s")
        print(f"[Benchmark] Avg time per search: {total_time/iterations*1000:.4f}ms")

if __name__ == '__main__':
    unittest.main()

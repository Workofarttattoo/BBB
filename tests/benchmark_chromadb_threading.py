import asyncio
import time
import sys
import os
from unittest.mock import MagicMock

# Add src to path if needed
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock chromadb so we can test the threading logic
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()

from blank_business_builder.expert_system import ChromaDBStore, ExpertDomain

def benchmark_chroma_search(store, num_searches=1000):
    # Mock the collection query to be fast but simulate some work
    for domain in ExpertDomain:
        store.collections[domain] = MagicMock()
        store.collections[domain].query.return_value = {
            'documents': [['doc1', 'doc2']],
            'ids': [['id1', 'id2']],
            'metadatas': [[{'meta': '1'}, {'meta': '2'}]],
            'distances': [[0.1, 0.2]]
        }

    start_time = time.perf_counter()
    for _ in range(num_searches):
        store.search("test query", top_k=5, domain=None) # search all domains

    end_time = time.perf_counter()
    return end_time - start_time

if __name__ == "__main__":
    store = ChromaDBStore()

    # Warmup
    benchmark_chroma_search(store, 100)

    print("Running benchmark...")
    t = benchmark_chroma_search(store, 5000)
    print(f"Time for 5000 multi-domain searches: {t:.4f}s")

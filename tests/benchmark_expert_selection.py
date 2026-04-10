
import sys
import asyncio
import unittest
from unittest.mock import MagicMock
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any

# Mock dependencies
sys.modules['chromadb'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['numpy'].mean = MagicMock(return_value=0.5)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.expert_system import MultiDomainExpertSystem, ExpertQuery, ExpertDomain, VectorStore, KnowledgeDocument

class CountingMockVectorStore(VectorStore):
    def __init__(self):
        self.search_count = 0

    def add_documents(self, documents):
        pass

    def search(self, query, top_k=5, domain=None):
        self.search_count += 1
        # Return a doc that mentions the domain
        return [(
            KnowledgeDocument(
                doc_id=f"doc_{domain}",
                content=f"Content for {domain or 'general'}: {query}",
                domain=domain or ExpertDomain.CHEMISTRY, # Default to Chemistry to force a match
                metadata={}
            ),
            0.9
        )]

    def get_by_id(self, doc_id):
        return None

async def run_benchmark():
    system = MultiDomainExpertSystem(use_chromadb=True)
    mock_store = CountingMockVectorStore()
    system.vector_store = mock_store

    # Mock experts with the counting store
    for expert in system.experts.values():
        expert.vector_store = mock_store

    query = ExpertQuery(query="test query")

    print("Running auto-select expert...")
    await system._auto_select_expert(query)

    print(f"Search calls: {mock_store.search_count}")

    # Assert optimized behavior: 1 call (1 global, reused by expert)
    if mock_store.search_count == 1:
        print("OPTIMIZATION PASS: Search count is 1")
        return True
    else:
        print(f"OPTIMIZATION FAIL: Expected 1, got {mock_store.search_count}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_benchmark())
    if not success:
        sys.exit(1)

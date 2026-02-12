import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import asyncio
from datetime import datetime

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Mock dependencies before import
mock_numpy = MagicMock()
mock_numpy.mean.return_value = 0.8
sys.modules["numpy"] = mock_numpy
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["faiss"] = MagicMock()

# Set up mocks for chromadb client
mock_chroma_client = MagicMock()
sys.modules["chromadb"].PersistentClient.return_value = mock_chroma_client
mock_collection = MagicMock()
mock_chroma_client.get_or_create_collection.return_value = mock_collection

# Now import the module under test
from blank_business_builder.expert_system import (
    MultiDomainExpertSystem, ExpertQuery, ExpertDomain, KnowledgeDocument,
    ExpertResponse, StandardDomainExpert
)

class TestExpertSystemOptimized(unittest.TestCase):
    def setUp(self):
        # Initialize system
        self.system = MultiDomainExpertSystem(use_chromadb=True)

        # We want to spy on vector_store.search
        # But vector_store is an instance of ChromaDBStore (which is using mocks)
        # Let's replace search with a MagicMock wrapper that calls the original (or a fake original)

        # Actually, simpler: just mock search to return something valid
        self.system.vector_store.search = MagicMock()

        # Setup a default return value for search
        # It returns List[Tuple[KnowledgeDocument, float]]

        self.doc_chem = KnowledgeDocument(
            doc_id="chem_1", content="Chemistry content", domain=ExpertDomain.CHEMISTRY, metadata={}
        )
        self.doc_bio = KnowledgeDocument(
            doc_id="bio_1", content="Biology content", domain=ExpertDomain.BIOLOGY, metadata={}
        )

        # Default behavior: return chemistry doc
        self.system.vector_store.search.return_value = [(self.doc_chem, 0.9)]

    def test_auto_select_expert_calls_count(self):
        query = ExpertQuery(query="Chemistry question")

        # Run _auto_select_expert
        # Since it's async, we use asyncio.run
        response = asyncio.run(self.system._auto_select_expert(query))

        # Currently, it calls answer_query on ALL experts.
        # Each expert calls retrieve_context, which calls vector_store.search(domain=expert.domain)
        # There are at least 5 experts initialized in _initialize_experts (chem, bio, phys, matsci, legal)

        print(f"Vector store search call count: {self.system.vector_store.search.call_count}")

        # Verify it called search fewer times (optimized behavior)
        # We expect 2 calls: 1 global search + 1 expert search
        self.assertEqual(self.system.vector_store.search.call_count, 2)

        # Verify response comes from chemistry expert (since we returned chem doc)
        # Wait, if we return chem doc for ALL searches (including biology domain search),
        # then biology expert will see chem doc?
        # Real search would filter by domain.
        # But here we mocked search to always return doc_chem.
        # StandardDomainExpert.answer_query uses whatever docs are returned.
        # So BiologyExpert will receive doc_chem, and say "Based on ... sources".
        # But answer_query returns ExpertResponse with domain=self.domain.
        # So BiologyExpert returns response with domain=BIOLOGY.
        # The system picks max confidence.
        # If we return same score (0.9) for all, max() picks first one or arbitrary.

        # To make it deterministic and realistic, we should make side_effect depend on domain arg.

        def search_side_effect(query, top_k=5, domain=None):
            if domain is None:
                # Global search finds chemistry doc as best
                return [(self.doc_chem, 0.95)]
            elif domain == ExpertDomain.CHEMISTRY:
                return [(self.doc_chem, 0.95)]
            elif domain == ExpertDomain.BIOLOGY:
                return [(self.doc_bio, 0.8)]
            else:
                return []

        self.system.vector_store.search.side_effect = search_side_effect
        self.system.vector_store.search.reset_mock()

        response = asyncio.run(self.system._auto_select_expert(query))

        print(f"Vector store search call count (deterministic): {self.system.vector_store.search.call_count}")
        # Identify best domain (1 call) -> returns CHEM -> CHEM expert search (1 call) -> Total 2
        self.assertEqual(self.system.vector_store.search.call_count, 2)
        self.assertEqual(response.domain, ExpertDomain.CHEMISTRY)

if __name__ == '__main__':
    unittest.main()

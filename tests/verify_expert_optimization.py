import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock dependencies before import
sys.modules["numpy"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["faiss"] = MagicMock()
sys.modules["torch"] = MagicMock()

# Adjust path to find src
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from blank_business_builder.expert_system import (
        MultiDomainExpertSystem,
        ExpertDomain,
        KnowledgeDocument,
        ExpertQuery,
        ExpertResponse
    )
except ImportError as e:
    # If standard import fails, try direct import from file path or different structure
    print(f"Import failed: {e}")
    # Try alternate structure
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.blank_business_builder.expert_system import (
        MultiDomainExpertSystem,
        ExpertDomain,
        KnowledgeDocument,
        ExpertQuery,
        ExpertResponse
    )

async def test_optimization():
    print("Testing MultiDomainExpertSystem optimization...")

    # Mock VectorStore
    mock_vector_store = MagicMock()

    # Mock search results for identify_best_domain
    # Suppose query is about Chemistry
    mock_doc = KnowledgeDocument(
        doc_id="chem_doc",
        content="Chemistry stuff",
        domain=ExpertDomain.CHEMISTRY,
        metadata={}
    )
    # search returns list of (doc, score)
    mock_vector_store.search.return_value = [(mock_doc, 0.95)]

    # Create system with mock vector store
    # We need to bypass __init__ which tries to init real stores
    system = MultiDomainExpertSystem.__new__(MultiDomainExpertSystem)
    system.vector_store = mock_vector_store
    system.experts = {}

    # Mock Experts
    chem_expert = AsyncMock()
    chem_expert.answer_query.return_value = ExpertResponse(
        answer="Chemistry answer",
        domain=ExpertDomain.CHEMISTRY,
        confidence=0.9,
        sources=[],
        reasoning="",
        expert_id="chem_expert"
    )

    bio_expert = AsyncMock()
    bio_expert.answer_query.return_value = ExpertResponse(
        answer="Biology answer",
        domain=ExpertDomain.BIOLOGY,
        confidence=0.1,
        sources=[],
        reasoning="",
        expert_id="bio_expert"
    )

    system.experts[ExpertDomain.CHEMISTRY] = chem_expert
    system.experts[ExpertDomain.BIOLOGY] = bio_expert

    # Test identify_best_domain
    print("  Verifying identify_best_domain...")
    domain = await system.identify_best_domain("chemistry query")
    assert domain == ExpertDomain.CHEMISTRY, f"Expected CHEMISTRY, got {domain}"
    print("  identify_best_domain passed.")

    # Test _auto_select_expert
    print("  Verifying _auto_select_expert routing...")
    query = ExpertQuery(query="chemistry query")

    # Reset mocks
    chem_expert.answer_query.reset_mock()
    bio_expert.answer_query.reset_mock()
    # Ensure search is called again
    mock_vector_store.search.reset_mock()
    mock_vector_store.search.return_value = [(mock_doc, 0.95)]

    # We need to set return values again because reset_mock might clear them depending on how it's used (AsyncMock usually keeps return_value)
    chem_expert.answer_query.return_value = ExpertResponse(
        answer="Chemistry answer",
        domain=ExpertDomain.CHEMISTRY,
        confidence=0.9,
        sources=[],
        reasoning="",
        expert_id="chem_expert"
    )

    response = await system._auto_select_expert(query)

    assert response.domain == ExpertDomain.CHEMISTRY
    # Verify ONLY Chemistry expert was called
    chem_expert.answer_query.assert_called_once()
    bio_expert.answer_query.assert_not_called()
    print("  Routing optimization passed: Only relevant expert queried.")

    # Test Fallback (No domain identified)
    print("  Verifying fallback behavior...")
    mock_vector_store.search.return_value = [] # No results
    chem_expert.answer_query.reset_mock()
    bio_expert.answer_query.reset_mock()

    # Prepare responses for fallback
    chem_expert.answer_query.return_value = ExpertResponse(
        answer="Chem fallback", domain=ExpertDomain.CHEMISTRY, confidence=0.5, sources=[], reasoning="", expert_id="chem"
    )
    bio_expert.answer_query.return_value = ExpertResponse(
        answer="Bio fallback", domain=ExpertDomain.BIOLOGY, confidence=0.6, sources=[], reasoning="", expert_id="bio"
    )

    response = await system._auto_select_expert(query)

    # Should pick highest confidence (Bio)
    assert response.domain == ExpertDomain.BIOLOGY
    # Should call BOTH
    chem_expert.answer_query.assert_called_once()
    bio_expert.answer_query.assert_called_once()
    print("  Fallback behavior passed.")

    # Test Low Confidence Fallback
    print("  Verifying low confidence fallback...")
    # Return low score result
    mock_vector_store.search.return_value = [(mock_doc, 0.4)]
    chem_expert.answer_query.reset_mock()
    bio_expert.answer_query.reset_mock()

    # Same fallback setup
    chem_expert.answer_query.return_value = ExpertResponse(
        answer="Chem fallback", domain=ExpertDomain.CHEMISTRY, confidence=0.5, sources=[], reasoning="", expert_id="chem"
    )
    bio_expert.answer_query.return_value = ExpertResponse(
        answer="Bio fallback", domain=ExpertDomain.BIOLOGY, confidence=0.6, sources=[], reasoning="", expert_id="bio"
    )

    response = await system._auto_select_expert(query)

    # Should fallback because 0.4 < 0.6
    assert response.domain == ExpertDomain.BIOLOGY
    chem_expert.answer_query.assert_called_once()
    bio_expert.answer_query.assert_called_once()
    print("  Low confidence fallback passed.")

if __name__ == "__main__":
    asyncio.run(test_optimization())


import asyncio
import time
import sys
from unittest.mock import MagicMock

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
from src.blank_business_builder.expert_system import MultiDomainExpertSystem, ExpertQuery, VectorStore, KnowledgeDocument, ExpertDomain, StandardDomainExpert

# Mock VectorStore with a blocking delay
class MockBlockingVectorStore(VectorStore):
    def add_documents(self, documents):
        pass

    def search(self, query, top_k=5, domain=None):
        # Simulate blocking search (e.g., 100ms)
        time.sleep(0.1)
        # Return empty list to avoid processing logic
        return []

    def get_by_id(self, doc_id):
        return None

async def run_benchmark():
    print("Initializing system with mock blocking VectorStore...")

    # We need to patch the vector store class used by the system
    # Since we can't easily inject it into __init__ without changing code,
    # we'll instantiate it and then replace the store.

    # The constructor tries to init ChromaDB or FAISS.
    # Since we mocked them, it should succeed.
    try:
        system = MultiDomainExpertSystem(use_chromadb=False)
    except Exception as e:
        print(f"Failed to init system: {e}")
        return

    # Create our blocking store
    mock_store = MockBlockingVectorStore()

    # Replace the store in the system
    system.vector_store = mock_store

    # Replace the store in all experts
    for expert in system.experts.values():
        expert.vector_store = mock_store

    query = ExpertQuery(query="Test query")

    num_experts = len(system.experts)
    print(f"Running auto-select query (queries all {num_experts} experts)...")

    start_time = time.time()

    # This calls _auto_select_expert, which gathers answer_query from all experts
    try:
        await system.query(query)
    except Exception as e:
        print(f"Query failed (expected due to mocks?): {e}")
        # Even if it fails, we want to see the timing of the calls made

    end_time = time.time()
    duration = end_time - start_time

    print(f"Total duration: {duration:.4f} seconds")

    expected_serial_time = num_experts * 0.1
    print(f"Expected Serial Time: >{expected_serial_time:.4f}s")

    # Check if it was serial or parallel
    if duration >= expected_serial_time * 0.9: # Allow some jitter
        print("RESULT: Execution was SERIAL (Blocking)")
    else:
        print("RESULT: Execution was PARALLEL (Non-blocking)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())

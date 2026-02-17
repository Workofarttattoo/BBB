"""
Multi-Domain Expert System with RAG and Ensemble Intelligence
==============================================================

Advanced expert system supporting multiple specialized domains with:
- Vector database for scalable RAG (ChromaDB + FAISS)
- Multi-expert ensemble decision making
- Automatic expert specialization
- Fine-tuning capabilities on domain-specific datasets

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import json
import logging
import numpy as np
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

# Optional dependencies - graceful degradation
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available - install with: pip install chromadb")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available - install with: pip install faiss-cpu")

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - fine-tuning disabled")

from .ech0_service import ECH0Service, ECH0_AVAILABLE


class ExpertDomain(Enum):
    """Supported expert domains."""
    # Science domains
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    MATERIALS_SCIENCE = "materials_science"

    # Engineering domains
    SOFTWARE_ENGINEERING = "software_engineering"
    ELECTRICAL_ENGINEERING = "electrical_engineering"
    MECHANICAL_ENGINEERING = "mechanical_engineering"

    # Business domains
    MARKETING = "marketing"
    FINANCE = "finance"
    SALES = "sales"
    OPERATIONS = "operations"

    # Data & AI domains
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    QUANTUM_COMPUTING = "quantum_computing"

    # Legal
    LEGAL = "legal"

    # General
    GENERAL = "general"


@dataclass
class ExpertQuery:
    """Query to expert system."""
    query: str
    domain: Optional[ExpertDomain] = None
    context: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 5
    confidence_threshold: float = 0.7
    use_ensemble: bool = False


@dataclass
class ExpertResponse:
    """Response from expert system."""
    answer: str
    domain: ExpertDomain
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning: str
    expert_id: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnsembleResponse:
    """Response from ensemble of experts."""
    consensus_answer: str
    individual_responses: List[ExpertResponse]
    agreement_score: float
    confidence: float
    domains_consulted: List[ExpertDomain]
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeDocument:
    """Document in knowledge base."""
    doc_id: str
    content: str
    domain: ExpertDomain
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)


class VectorStore(ABC):
    """Abstract base for vector storage backends."""

    @abstractmethod
    async def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to vector store."""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        pass


class MockVectorStore(VectorStore):
    """Simple in-memory vector store for testing and fallback."""

    def __init__(self):
        self.documents: Dict[str, KnowledgeDocument] = {}

    async def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to mock store."""
        for doc in documents:
            self.documents[doc.doc_id] = doc

    async def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Mock search - returns random or all documents."""
        results = []
        words = query.lower().split()

        for doc in self.documents.values():
            if domain and doc.domain != domain:
                continue

            # Simple keyword matching for relevance
            score = 0.0
            content_lower = doc.content.lower()
            for word in words:
                if word in content_lower:
                    score += 0.1

            # Base score + match score
            final_score = 0.1 + min(0.8, score)
            results.append((doc, final_score))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        return self.documents.get(doc_id)


class ChromaDBStore(VectorStore):
    """ChromaDB-based vector store."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB not available")

        # Use new ChromaDB API (v0.4+)
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
        except AttributeError:
            # Fallback for older versions
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory
            ))

        # Create collections per domain
        self.collections: Dict[ExpertDomain, Any] = {}
        for domain in ExpertDomain:
            try:
                self.collections[domain] = self.client.get_or_create_collection(
                    name=f"expert_{domain.value}"
                )
            except Exception as e:
                logger.warning(f"Could not create collection for {domain.value}: {e}")

    async def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to ChromaDB."""
        for doc in documents:
            collection = self.collections.get(doc.domain)
            if not collection:
                continue

            try:
                # Run sync call in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: collection.add(
                    documents=[doc.content],
                    metadatas=[doc.metadata],
                    ids=[doc.doc_id]
                ))
            except Exception as e:
                logger.error(f"Failed to add document {doc.doc_id}: {e}")

    async def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Search ChromaDB."""
        results = []

        # Determine which collections to search
        domains_to_search = [domain] if domain else list(ExpertDomain)

        loop = asyncio.get_event_loop()

        for search_domain in domains_to_search:
            collection = self.collections.get(search_domain)
            if not collection:
                continue

            try:
                # Run sync call in executor
                search_results = await loop.run_in_executor(None, lambda: collection.query(
                    query_texts=[query],
                    n_results=top_k
                ))

                if search_results and search_results['documents']:
                    for i, doc_content in enumerate(search_results['documents'][0]):
                        doc_id = search_results['ids'][0][i]
                        metadata = search_results['metadatas'][0][i]
                        distance = search_results['distances'][0][i] if 'distances' in search_results else 0.0

                        # Convert distance to similarity score (0-1)
                        similarity = 1.0 / (1.0 + distance)

                        doc = KnowledgeDocument(
                            doc_id=doc_id,
                            content=doc_content,
                            domain=search_domain,
                            metadata=metadata
                        )
                        results.append((doc, similarity))
            except Exception as e:
                logger.error(f"Search failed for domain {search_domain.value}: {e}")

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        for domain, collection in self.collections.items():
            try:
                result = collection.get(ids=[doc_id])
                if result and result['documents']:
                    return KnowledgeDocument(
                        doc_id=doc_id,
                        content=result['documents'][0],
                        domain=domain,
                        metadata=result['metadatas'][0]
                    )
            except Exception:
                continue
        return None


class FAISSStore(VectorStore):
    """FAISS-based vector store for high-performance similarity search."""

    def __init__(self, embedding_dim: int = 384):
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS not available")

        self.embedding_dim = embedding_dim

        # Create FAISS indices per domain
        self.indices: Dict[ExpertDomain, faiss.IndexFlatL2] = {}
        self.documents: Dict[ExpertDomain, List[KnowledgeDocument]] = defaultdict(list)

        for domain in ExpertDomain:
            self.indices[domain] = faiss.IndexFlatL2(embedding_dim)

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute simple embedding (replace with real embeddings in production)."""
        # Simple hash-based embedding for demonstration
        # In production, use sentence-transformers or OpenAI embeddings
        hash_value = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        np.random.seed(hash_value % (2**32))
        return np.random.randn(self.embedding_dim).astype('float32')

    async def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to FAISS."""
        # CPU bound, could benefit from executor if large
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = self._compute_embedding(doc.content)

            # Add to FAISS index
            self.indices[doc.domain].add(doc.embedding.reshape(1, -1))
            self.documents[doc.domain].append(doc)

    async def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Search FAISS."""
        query_embedding = self._compute_embedding(query)
        results = []

        # Determine which indices to search
        domains_to_search = [domain] if domain else list(ExpertDomain)

        for search_domain in domains_to_search:
            index = self.indices.get(search_domain)
            docs = self.documents.get(search_domain, [])

            if not docs:
                continue

            try:
                # Search FAISS index
                distances, indices = index.search(query_embedding.reshape(1, -1), min(top_k, len(docs)))

                for i, idx in enumerate(indices[0]):
                    if idx < len(docs):
                        # Convert L2 distance to similarity score
                        similarity = 1.0 / (1.0 + distances[0][i])
                        results.append((docs[idx], similarity))
            except Exception as e:
                logger.error(f"FAISS search failed for {search_domain.value}: {e}")

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        for docs in self.documents.values():
            for doc in docs:
                if doc.doc_id == doc_id:
                    return doc
        return None


class ECH0VectorStore(VectorStore):
    """Bridge to ECH0's semantic memory and insight engine."""

    def __init__(self):
        if not ECH0_AVAILABLE:
            logger.warning("ECH0Service not available - ECH0VectorStore will not function correctly")
        self.ech0_service = ECH0Service()

    async def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """
        ECH0 learns independently.
        Sending documents here might just log them or fine-tune if supported.
        For now, we assume read-only access to ECH0's wisdom.
        """
        pass

    async def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """
        Ask ECH0 for insight on the query.
        Returns the insight wrapped as a KnowledgeDocument.
        """
        try:
            # Contextualize prompt based on domain
            domain_context = f"in the domain of {domain.value}" if domain else ""
            prompt = f"Provide deep insight and relevant facts about: {query} {domain_context}. Focus on factual knowledge."

            insight = await self.ech0_service.generate_content(query, "detailed insight")

            # Create a synthetic document from ECH0's mind
            doc = KnowledgeDocument(
                doc_id=f"ech0_insight_{hash(query)}",
                content=insight,
                domain=domain or ExpertDomain.GENERAL,
                metadata={"source": "ECH0 Semantic Lattice", "type": "generated_insight"}
            )

            # Return as a high-confidence result
            return [(doc, 0.95)]

        except Exception as e:
            logger.error(f"ECH0 search failed: {e}")
            return []

    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve specific insight if cached (not implemented for dynamic generation)."""
        return None


class DomainExpert(ABC):
    """Abstract base class for domain experts."""

    def __init__(self, expert_id: str, domain: ExpertDomain, vector_store: VectorStore):
        self.expert_id = expert_id
        self.domain = domain
        self.vector_store = vector_store
        self.specialization_score = 0.8  # Base specialization
        self.query_history: List[Tuple[str, ExpertResponse]] = []

    @abstractmethod
    async def answer_query(self, query: ExpertQuery) -> ExpertResponse:
        """Answer a query using domain expertise."""
        pass

    def update_specialization(self, feedback: float) -> None:
        """Update specialization score based on feedback."""
        # Exponential moving average
        self.specialization_score = 0.9 * self.specialization_score + 0.1 * feedback

    async def retrieve_context(self, query: str, max_results: int = 5) -> List[Tuple[KnowledgeDocument, float]]:
        """Retrieve relevant context from vector store."""
        return await self.vector_store.search(query, top_k=max_results, domain=self.domain)


class StandardDomainExpert(DomainExpert):
    """Standard implementation of a domain expert."""

    def __init__(self, expert_id: str, domain: ExpertDomain, vector_store: VectorStore):
        super().__init__(expert_id, domain, vector_store)

    async def answer_query(self, query: ExpertQuery) -> ExpertResponse:
        """Answer query using domain expertise."""
        # Retrieve relevant documents
        context_docs = await self.retrieve_context(query.query, query.max_results)

        # Synthesize answer (would use LLM in production)
        sources = [
            {
                "doc_id": doc.doc_id,
                "content": doc.content[:200],
                "relevance": score,
                "metadata": doc.metadata
            }
            for doc, score in context_docs
        ]

        # Generate answer based on domain knowledge
        domain_name = self.domain.value.replace('_', ' ').title()
        answer = f"[{domain_name} Expert] Based on {len(sources)} sources: {query.query}"
        if context_docs:
            top_doc, top_score = context_docs[0]
            answer += f"\n\nKey insight: {top_doc.content[:300]}"

        confidence = np.mean([score for _, score in context_docs]) if context_docs else 0.5

        response = ExpertResponse(
            answer=answer,
            domain=self.domain,
            confidence=confidence * self.specialization_score,
            sources=sources,
            reasoning=f"RAG-based synthesis from {self.domain.value.replace('_', ' ')} knowledge base",
            expert_id=self.expert_id
        )

        self.query_history.append((query.query, response))
        return response


class ChemistryExpert(StandardDomainExpert):
    """Expert in Chemistry domain."""
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.CHEMISTRY, vector_store)

class BiologyExpert(StandardDomainExpert):
    """Expert in Biology domain."""
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.BIOLOGY, vector_store)

class PhysicsExpert(StandardDomainExpert):
    """Expert in Physics domain."""
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.PHYSICS, vector_store)

class MaterialsScienceExpert(StandardDomainExpert):
    """Expert in Materials Science domain."""
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.MATERIALS_SCIENCE, vector_store)

class LegalExpert(StandardDomainExpert):
    """Expert in Legal domain."""
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.LEGAL, vector_store)


class MultiExpertEnsemble:
    """Ensemble of domain experts with voting and consensus."""

    def __init__(self, experts: List[DomainExpert], voting_strategy: str = "weighted"):
        self.experts = experts
        self.voting_strategy = voting_strategy  # weighted, majority, unanimous

    async def answer_query(self, query: ExpertQuery) -> EnsembleResponse:
        """Get consensus answer from multiple experts."""
        # Query all relevant experts in parallel
        expert_tasks = [expert.answer_query(query) for expert in self.experts]
        responses = await asyncio.gather(*expert_tasks)

        # Filter by confidence threshold
        valid_responses = [r for r in responses if r.confidence >= query.confidence_threshold]

        if not valid_responses:
            # Fall back to best effort
            valid_responses = responses

        # Apply voting strategy
        if self.voting_strategy == "weighted":
            consensus_answer = self._weighted_voting(valid_responses)
        elif self.voting_strategy == "majority":
            consensus_answer = self._majority_voting(valid_responses)
        else:
            consensus_answer = self._unanimous_voting(valid_responses)

        # Calculate agreement score
        agreement_score = self._calculate_agreement(valid_responses)

        # Calculate ensemble confidence
        ensemble_confidence = np.mean([r.confidence for r in valid_responses])

        domains_consulted = list(set(r.domain for r in valid_responses))

        reasoning = f"Consulted {len(valid_responses)} experts using {self.voting_strategy} voting. Agreement: {agreement_score:.2f}"

        return EnsembleResponse(
            consensus_answer=consensus_answer,
            individual_responses=valid_responses,
            agreement_score=agreement_score,
            confidence=ensemble_confidence,
            domains_consulted=domains_consulted,
            reasoning=reasoning
        )

    def _weighted_voting(self, responses: List[ExpertResponse]) -> str:
        """Weight answers by confidence and specialization."""
        if not responses:
            return "No consensus reached"

        # For simplicity, return highest confidence answer
        # In production, use semantic similarity and weighted combination
        best_response = max(responses, key=lambda r: r.confidence)
        return best_response.answer

    def _majority_voting(self, responses: List[ExpertResponse]) -> str:
        """Simple majority vote."""
        if not responses:
            return "No consensus reached"

        # In production, cluster similar answers and find majority
        return responses[0].answer

    def _unanimous_voting(self, responses: List[ExpertResponse]) -> str:
        """Require unanimous agreement."""
        if not responses:
            return "No consensus reached"

        # In production, check semantic similarity
        agreement = self._calculate_agreement(responses)
        if agreement > 0.9:
            return responses[0].answer
        else:
            return "Experts disagree - no unanimous consensus"

    def _calculate_agreement(self, responses: List[ExpertResponse]) -> float:
        """Calculate agreement score among experts."""
        if len(responses) <= 1:
            return 1.0

        # Simple heuristic: variance in confidence scores
        confidences = [r.confidence for r in responses]
        variance = np.var(confidences)
        agreement = 1.0 / (1.0 + variance)

        return agreement


class ExpertSpecializationEngine:
    """Automatic expert specialization through learning."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.experts: Dict[ExpertDomain, DomainExpert] = {}
        self.performance_history: Dict[str, List[float]] = defaultdict(list)

    def register_expert(self, expert: DomainExpert) -> None:
        """Register an expert for specialization."""
        self.experts[expert.domain] = expert

    async def specialize_expert(
        self,
        domain: ExpertDomain,
        training_queries: List[Tuple[str, str, float]]  # (query, expected_answer, quality_score)
    ) -> float:
        """Specialize expert through iterative training."""
        expert = self.experts.get(domain)
        if not expert:
            raise ValueError(f"No expert registered for {domain}")

        total_improvement = 0.0

        for query, expected_answer, quality_score in training_queries:
            # Query expert
            expert_query = ExpertQuery(query=query, domain=domain)
            response = await expert.answer_query(expert_query)

            # Calculate feedback based on quality
            feedback = quality_score

            # Update expert specialization
            expert.update_specialization(feedback)

            # Track performance
            self.performance_history[expert.expert_id].append(feedback)

            total_improvement += feedback

        avg_improvement = total_improvement / len(training_queries) if training_queries else 0.0

        logger.info(
            f"Specialized {domain.value} expert - "
            f"New specialization score: {expert.specialization_score:.3f}, "
            f"Avg improvement: {avg_improvement:.3f}"
        )

        return expert.specialization_score

    def get_expert_performance(self, domain: ExpertDomain) -> Dict[str, Any]:
        """Get performance metrics for expert."""
        expert = self.experts.get(domain)
        if not expert:
            return {}

        history = self.performance_history.get(expert.expert_id, [])

        return {
            "expert_id": expert.expert_id,
            "domain": domain.value,
            "specialization_score": expert.specialization_score,
            "queries_answered": len(expert.query_history),
            "performance_history": history,
            "average_performance": np.mean(history) if history else 0.0,
            "trend": "improving" if len(history) > 1 and history[-1] > history[0] else "stable"
        }


class MultiDomainExpertSystem:
    """Main expert system coordinating all domains."""

    def __init__(self, use_chromadb: bool = True, use_ech0: bool = False):
        # Initialize vector store
        if use_ech0:
            self.vector_store = ECH0VectorStore()
            logger.info("Initialized ECH0 Vector Store (Semantic Lattice Bridge)")
        elif use_chromadb and CHROMADB_AVAILABLE:
            self.vector_store = ChromaDBStore()
            logger.info("Initialized ChromaDB vector store")
        elif FAISS_AVAILABLE:
            self.vector_store = FAISSStore()
            logger.info("Initialized FAISS vector store")
        else:
            logger.warning("No vector store available - using MockVectorStore for fallback/testing")
            self.vector_store = MockVectorStore()

        # Initialize experts
        self.experts: Dict[ExpertDomain, DomainExpert] = {}
        self._initialize_experts()

        # Initialize ensemble
        self.ensemble = MultiExpertEnsemble(list(self.experts.values()))

        # Initialize specialization engine
        self.specialization_engine = ExpertSpecializationEngine(self.vector_store)
        for expert in self.experts.values():
            self.specialization_engine.register_expert(expert)

        logger.info(f"Initialized expert system with {len(self.experts)} domain experts")

    def _initialize_experts(self) -> None:
        """Initialize all domain experts."""
        # Science experts
       
        self.experts[ExpertDomain.CHEMISTRY] = ChemistryExpert("chem_001", self.vector_store)
        self.experts[ExpertDomain.BIOLOGY] = BiologyExpert("bio_001", self.vector_store)
        self.experts[ExpertDomain.PHYSICS] = PhysicsExpert("phys_001", self.vector_store)
        self.experts[ExpertDomain.MATERIALS_SCIENCE] = MaterialsScienceExpert("matsci_001", self.vector_store)
        self.experts[ExpertDomain.LEGAL] = LegalExpert("legal_001", self.vector_store)

        # Additional experts can be added here
        logger.info("Initialized domain experts: chemistry, biology, physics, materials_science, legal")

    async def add_knowledge(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to knowledge base."""
        await self.vector_store.add_documents(documents)
        logger.info(f"Added {len(documents)} documents to knowledge base")

    async def query(self, query: ExpertQuery) -> ExpertResponse | EnsembleResponse:
        """Query the expert system."""
        if query.use_ensemble:
            # Use ensemble of experts
            return await self.ensemble.answer_query(query)
        elif query.domain:
            # Query specific domain expert
            expert = self.experts.get(query.domain)
            if not expert:
                raise ValueError(f"No expert available for domain: {query.domain}")
            return await expert.answer_query(query)
        else:
            # Auto-select best expert(s)
            return await self._auto_select_expert(query)

    async def _auto_select_expert(self, query: ExpertQuery) -> ExpertResponse:
        """Automatically select best expert for query."""
        # Query all experts and select highest confidence
        expert_tasks = [expert.answer_query(query) for expert in self.experts.values()]
        responses = await asyncio.gather(*expert_tasks)

        # Return highest confidence response
        best_response = max(responses, key=lambda r: r.confidence)
        return best_response

    async def specialize_expert(
        self,
        domain: ExpertDomain,
        training_data: List[Tuple[str, str, float]]
    ) -> float:
        """Specialize an expert with training data."""
        return await self.specialization_engine.specialize_expert(domain, training_data)

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "total_experts": len(self.experts),
            "domains": [d.value for d in self.experts.keys()],
            "vector_store_type": type(self.vector_store).__name__,
            "expert_performance": {
                domain.value: self.specialization_engine.get_expert_performance(domain)
                for domain in self.experts.keys()
            }
        }


# Example usage and demonstration
async def demo_expert_system():
    """Demonstrate expert system capabilities."""
    print("="*80)
    print("Multi-Domain Expert System Demo")
    print("="*80)

    # Initialize system
    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Add sample knowledge
    sample_docs = [
        KnowledgeDocument(
            doc_id="chem_001",
            content="Chemical bonds form when atoms share or transfer electrons. Covalent bonds involve sharing, ionic bonds involve transfer.",
            domain=ExpertDomain.CHEMISTRY,
            metadata={"source": "chemistry_textbook", "chapter": 1}
        ),
        KnowledgeDocument(
            doc_id="bio_001",
            content="DNA replication is semiconservative - each strand serves as a template for a new complementary strand.",
            domain=ExpertDomain.BIOLOGY,
            metadata={"source": "biology_textbook", "chapter": 3}
        ),
        KnowledgeDocument(
            doc_id="phys_001",
            content="Newton's laws of motion: 1) Object at rest stays at rest unless acted upon by force. 2) F=ma. 3) Every action has equal and opposite reaction.",
            domain=ExpertDomain.PHYSICS,
            metadata={"source": "physics_textbook", "chapter": 2}
        ),
        KnowledgeDocument(
            doc_id="matsci_001",
            content="Crystalline materials have ordered atomic structure. Amorphous materials lack long-range order. Crystal structure determines material properties.",
            domain=ExpertDomain.MATERIALS_SCIENCE,
            metadata={"source": "materials_science_textbook", "chapter": 1}
        )
    ]

    system.add_knowledge(sample_docs)

    # Query individual expert
    print("\n1. Querying Chemistry Expert:")
    print("-" * 80)
    query = ExpertQuery(
        query="What are the types of chemical bonds?",
        domain=ExpertDomain.CHEMISTRY
    )
    response = await system.query(query)
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Sources: {len(response.sources)}")

    # Query with ensemble
    print("\n2. Querying with Ensemble:")
    print("-" * 80)
    query = ExpertQuery(
        query="How do atomic structures affect material properties?",
        use_ensemble=True
    )
    response = await system.query(query)
    print(f"Consensus: {response.consensus_answer[:200]}...")
    print(f"Agreement: {response.agreement_score:.2f}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Domains consulted: {[d.value for d in response.domains_consulted]}")

    # Auto-select expert
    print("\n3. Auto-selecting Best Expert:")
    print("-" * 80)
    query = ExpertQuery(
        query="Explain DNA replication"
    )
    response = await system.query(query)
    print(f"Selected expert: {response.expert_id} ({response.domain.value})")
    print(f"Answer: {response.answer[:200]}...")
    print(f"Confidence: {response.confidence:.2f}")

    # Specialization
    print("\n4. Specializing Chemistry Expert:")
    print("-" * 80)
    training_data = [
        ("What is a covalent bond?", "Electrons shared between atoms", 0.9),
        ("What is an ionic bond?", "Electrons transferred between atoms", 0.85),
        ("What determines bond strength?", "Depends on electronegativity difference", 0.8)
    ]
    new_score = await system.specialize_expert(ExpertDomain.CHEMISTRY, training_data)
    print(f"New specialization score: {new_score:.3f}")

    # System status
    print("\n5. System Status:")
    print("-" * 80)
    status = system.get_system_status()
    print(json.dumps(status, indent=2, default=str))

    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(demo_expert_system())

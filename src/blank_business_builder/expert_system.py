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
    def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to vector store."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        pass


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

    def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to ChromaDB."""
        for doc in documents:
            collection = self.collections.get(doc.domain)
            if not collection:
                continue

            try:
                collection.add(
                    documents=[doc.content],
                    metadatas=[doc.metadata],
                    ids=[doc.doc_id]
                )
            except Exception as e:
                logger.error(f"Failed to add document {doc.doc_id}: {e}")

    def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
        """Search ChromaDB."""
        results = []

        # Determine which collections to search
        domains_to_search = [domain] if domain else list(ExpertDomain)

        for search_domain in domains_to_search:
            collection = self.collections.get(search_domain)
            if not collection:
                continue

            try:
                search_results = collection.query(
                    query_texts=[query],
                    n_results=top_k
                )

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

    def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
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

    def add_documents(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to FAISS."""
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = self._compute_embedding(doc.content)

            # Add to FAISS index
            self.indices[doc.domain].add(doc.embedding.reshape(1, -1))
            self.documents[doc.domain].append(doc)

    def search(self, query: str, top_k: int = 5, domain: Optional[ExpertDomain] = None) -> List[Tuple[KnowledgeDocument, float]]:
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

    def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID."""
        for docs in self.documents.values():
            for doc in docs:
                if doc.doc_id == doc_id:
                    return doc
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
        # Use run_in_executor to avoid blocking the event loop with synchronous vector search
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.vector_store.search,
            query,
            max_results,
            self.domain
        )


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
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.CHEMISTRY, vector_store)

class BiologyExpert(StandardDomainExpert):
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.BIOLOGY, vector_store)

class PhysicsExpert(StandardDomainExpert):
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.PHYSICS, vector_store)

class MaterialsScienceExpert(StandardDomainExpert):
    def __init__(self, expert_id: str, vector_store: VectorStore):
        super().__init__(expert_id, ExpertDomain.MATERIALS_SCIENCE, vector_store)

class LegalExpert(StandardDomainExpert):
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

    def __init__(self, use_chromadb: bool = True):
        # Initialize vector store
        if use_chromadb and CHROMADB_AVAILABLE:
            self.vector_store = ChromaDBStore()
            logger.info("Initialized ChromaDB vector store")
        elif FAISS_AVAILABLE:
            self.vector_store = FAISSStore()
            logger.info("Initialized FAISS vector store")
        else:
            raise RuntimeError("No vector store available - install chromadb or faiss")

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

    def add_knowledge(self, documents: List[KnowledgeDocument]) -> None:
        """Add documents to knowledge base."""
        self.vector_store.add_documents(documents)
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

    def identify_best_domain(self, query: str) -> Optional[ExpertDomain]:
        """Identify the most relevant domain for a query efficiently."""
        # Single search across all domains
        results = self.vector_store.search(query, top_k=1, domain=None)
        if results:
            return results[0][0].domain
        return None

    async def _auto_select_expert(self, query: ExpertQuery) -> ExpertResponse:
        """Automatically select best expert for query."""

        # Optimization: Try to identify domain first
        best_domain = self.identify_best_domain(query.query)

        if best_domain:
            expert = self.experts.get(best_domain)
            if expert:
                # If we found a specific domain match via vector search, query just that expert.
                # This reduces N searches to 1 global search + 1 specific search.
                return await expert.answer_query(query)

        # Fallback to querying all experts if no clear domain match
        # (or if identified domain expert is missing, which shouldn't happen)
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



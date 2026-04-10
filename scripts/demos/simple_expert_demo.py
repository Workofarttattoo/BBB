#!/usr/bin/env python3
"""
Simple Expert System Demonstration
==================================

Simple demo of the multi-domain expert system extracted from the library file.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from blank_business_builder.expert_system import (
    MultiDomainExpertSystem,
    ExpertDomain,
    ExpertQuery,
    KnowledgeDocument,
    CHROMADB_AVAILABLE
)


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

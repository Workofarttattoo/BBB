#!/usr/bin/env python3
"""
Expert System Demonstration
============================

Comprehensive demo of the multi-domain expert system with:
- Domain expert consultation
- Vector RAG retrieval
- Multi-expert ensemble
- Automatic specialization
- Fine-tuning capabilities

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
    CHROMADB_AVAILABLE,
    FAISS_AVAILABLE
)
from blank_business_builder.expert_finetuning import (
    ExpertFineTuner,
    TrainingStrategy,
    DatasetGenerator
)
from blank_business_builder.expert_integration import (
    launch_expert_enhanced_business
)


async def demo_1_basic_queries():
    """Demo 1: Basic expert queries."""
    print("\n" + "="*80)
    print("DEMO 1: Basic Expert Queries")
    print("="*80)

    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Add knowledge
    docs = [
        KnowledgeDocument(
            doc_id="chem_bonds",
            content="Chemical bonds: covalent (electron sharing), ionic (electron transfer), metallic (electron sea). Bond strength depends on electronegativity difference.",
            domain=ExpertDomain.CHEMISTRY,
            metadata={"topic": "bonding"}
        ),
        KnowledgeDocument(
            doc_id="bio_cell",
            content="Cell theory: all organisms are made of cells, cells come from pre-existing cells, cells are the basic unit of life.",
            domain=ExpertDomain.BIOLOGY,
            metadata={"topic": "cell_biology"}
        )
    ]
    system.add_knowledge(docs)

    # Query chemistry expert
    print("\n[Query 1] What are the types of chemical bonds?")
    query = ExpertQuery(
        query="What are the types of chemical bonds?",
        domain=ExpertDomain.CHEMISTRY
    )
    response = await system.query(query)
    print(f"Expert: {response.expert_id} ({response.domain.value})")
    print(f"Confidence: {response.confidence:.2%}")
    print(f"Answer: {response.answer[:300]}...")

    # Query biology expert
    print("\n[Query 2] What is cell theory?")
    query = ExpertQuery(
        query="What is cell theory?",
        domain=ExpertDomain.BIOLOGY
    )
    response = await system.query(query)
    print(f"Expert: {response.expert_id} ({response.domain.value})")
    print(f"Confidence: {response.confidence:.2%}")
    print(f"Answer: {response.answer[:300]}...")

    print("\n✓ Demo 1 complete")


async def demo_2_ensemble_voting():
    """Demo 2: Multi-expert ensemble with voting."""
    print("\n" + "="*80)
    print("DEMO 2: Multi-Expert Ensemble")
    print("="*80)

    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Add interdisciplinary knowledge
    docs = [
        KnowledgeDocument(
            doc_id="quantum_chem",
            content="Quantum chemistry applies quantum mechanics to chemical systems. Wave functions describe electron behavior in atoms and molecules.",
            domain=ExpertDomain.CHEMISTRY,
            metadata={"topic": "quantum"}
        ),
        KnowledgeDocument(
            doc_id="quantum_phys",
            content="Quantum mechanics describes behavior at atomic scale. Key principles: superposition, entanglement, wave-particle duality.",
            domain=ExpertDomain.PHYSICS,
            metadata={"topic": "quantum"}
        )
    ]
    system.add_knowledge(docs)

    # Query with ensemble
    print("\n[Ensemble Query] How does quantum mechanics apply to chemistry?")
    query = ExpertQuery(
        query="How does quantum mechanics apply to chemistry?",
        use_ensemble=True
    )
    response = await system.query(query)

    print(f"Consensus Answer: {response.consensus_answer[:400]}...")
    print(f"\nEnsemble Stats:")
    print(f"  - Agreement Score: {response.agreement_score:.2%}")
    print(f"  - Confidence: {response.confidence:.2%}")
    print(f"  - Domains Consulted: {', '.join(d.value for d in response.domains_consulted)}")
    print(f"  - Individual Experts: {len(response.individual_responses)}")

    for i, expert_resp in enumerate(response.individual_responses, 1):
        print(f"\n  Expert {i} ({expert_resp.domain.value}):")
        print(f"    Confidence: {expert_resp.confidence:.2%}")
        print(f"    Sources: {len(expert_resp.sources)}")

    print("\n✓ Demo 2 complete")


async def demo_3_auto_specialization():
    """Demo 3: Automatic expert specialization."""
    print("\n" + "="*80)
    print("DEMO 3: Automatic Expert Specialization")
    print("="*80)

    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Check initial specialization
    chem_expert = system.experts[ExpertDomain.CHEMISTRY]
    initial_score = chem_expert.specialization_score
    print(f"\nInitial Chemistry Expert Specialization: {initial_score:.3f}")

    # Create training data
    training_data = [
        ("What is an acid?", "Substance that donates protons (H+)", 0.95),
        ("What is a base?", "Substance that accepts protons", 0.95),
        ("What is pH scale?", "Logarithmic scale of acidity from 0-14", 0.90),
        ("What is neutralization?", "Reaction between acid and base producing salt and water", 0.92)
    ]

    # Specialize expert
    print("\nSpecializing chemistry expert...")
    new_score = await system.specialize_expert(
        domain=ExpertDomain.CHEMISTRY,
        training_data=training_data
    )

    print(f"Final Chemistry Expert Specialization: {new_score:.3f}")
    print(f"Improvement: {new_score - initial_score:+.3f}")

    # Get performance metrics
    performance = system.specialization_engine.get_expert_performance(ExpertDomain.CHEMISTRY)
    print(f"\nPerformance Metrics:")
    print(f"  - Queries Answered: {performance['queries_answered']}")
    print(f"  - Average Performance: {performance['average_performance']:.2%}")
    print(f"  - Trend: {performance['trend']}")

    print("\n✓ Demo 3 complete")


async def demo_4_fine_tuning():
    """Demo 4: Expert fine-tuning with different strategies."""
    print("\n" + "="*80)
    print("DEMO 4: Expert Fine-Tuning")
    print("="*80)

    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Generate datasets
    print("\nGenerating training datasets...")
    datasets = {
        ExpertDomain.CHEMISTRY: DatasetGenerator.generate_chemistry_dataset(40),
        ExpertDomain.BIOLOGY: DatasetGenerator.generate_biology_dataset(40),
        ExpertDomain.PHYSICS: DatasetGenerator.generate_physics_dataset(40)
    }

    results = []

    # Fine-tune with different strategies
    strategies = [
        (ExpertDomain.CHEMISTRY, TrainingStrategy.SUPERVISED_LEARNING),
        (ExpertDomain.BIOLOGY, TrainingStrategy.BEHAVIORAL_CLONING),
        (ExpertDomain.PHYSICS, TrainingStrategy.REINFORCEMENT_LEARNING)
    ]

    for domain, strategy in strategies:
        print(f"\n[Fine-tuning {domain.value}] Strategy: {strategy.value}")

        finetuner = ExpertFineTuner(system, strategy=strategy)
        result = await finetuner.fine_tune_expert(
            domain=domain,
            dataset=datasets[domain],
            epochs=3,
            batch_size=8,
            learning_rate=0.01
        )

        results.append(result)

        print(f"✓ Initial: {result.initial_performance:.3f}")
        print(f"✓ Final: {result.final_performance:.3f}")
        print(f"✓ Improvement: {result.improvement:+.3f}")
        print(f"✓ Time: {result.training_time:.1f}s")

    # Save results
    output_path = "expert_finetuning_results.json"
    results[0].__class__.__module__ = "demo"  # Hack for JSON serialization
    with open(output_path, 'w') as f:
        json.dump({
            "results": [
                {
                    "domain": r.domain.value,
                    "initial": r.initial_performance,
                    "final": r.final_performance,
                    "improvement": r.improvement,
                    "time": r.training_time,
                    "examples": r.total_examples
                }
                for r in results
            ]
        }, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")
    print("\n✓ Demo 4 complete")


async def demo_5_business_integration():
    """Demo 5: Integration with autonomous business."""
    print("\n" + "="*80)
    print("DEMO 5: Business Integration")
    print("="*80)

    print("\nLaunching expert-enhanced autonomous business...")
    print("Business: AI-Powered Scientific Research Service")
    print("Duration: 0.05 hours (3 minutes)")

    result = await launch_expert_enhanced_business(
        business_concept="AI-Powered Scientific Research Service",
        founder_name="Joshua Cole",
        duration_hours=0.05,
        enable_experts=True
    )

    print("\n" + "-"*80)
    print("BUSINESS RESULTS")
    print("-"*80)

    # Business metrics
    print(f"\nRevenue:")
    print(f"  - Total: ${result['metrics']['revenue']['total']:,.2f}")
    print(f"  - Monthly: ${result['metrics']['revenue']['monthly']:,.2f}")

    print(f"\nOperations:")
    print(f"  - Tasks Completed: {result['metrics']['operations']['tasks_completed']}")
    print(f"  - Success Rate: {result['metrics']['operations']['success_rate']:.2%}")

    # Expert system metrics
    if 'expert_system' in result and result['expert_system']['enabled']:
        expert_metrics = result['expert_system']
        print(f"\nExpert System:")
        print(f"  - Total Consultations: {expert_metrics['total_consultations']}")
        print(f"  - Domains Available: {len(expert_metrics['expert_system_status']['domains'])}")
        print(f"  - Active Experts: {expert_metrics['expert_system_status']['total_experts']}")

    # Agent performance
    print(f"\nAgent Performance:")
    for agent in result['agents'][:3]:  # Show first 3 agents
        print(f"  - {agent['role']}: {agent['performance']['tasks_completed']} tasks, "
              f"{agent['performance']['success_rate']:.2%} success")

    print("\n✓ Demo 5 complete")


async def demo_6_system_status():
    """Demo 6: System status and diagnostics."""
    print("\n" + "="*80)
    print("DEMO 6: System Status & Diagnostics")
    print("="*80)

    system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    # Add some knowledge
    docs = [
        KnowledgeDocument(
            doc_id=f"doc_{i}",
            content=f"Sample document {i} for {domain.value}",
            domain=domain,
            metadata={"index": i}
        )
        for i, domain in enumerate([
            ExpertDomain.CHEMISTRY,
            ExpertDomain.BIOLOGY,
            ExpertDomain.PHYSICS,
            ExpertDomain.MATERIALS_SCIENCE
        ])
    ]
    system.add_knowledge(docs)

    # Get status
    status = system.get_system_status()

    print("\nSystem Configuration:")
    print(f"  - Total Experts: {status['total_experts']}")
    print(f"  - Vector Store: {status['vector_store_type']}")
    print(f"  - Domains: {', '.join(status['domains'])}")

    print("\nExpert Performance:")
    for domain, perf in status['expert_performance'].items():
        print(f"\n  {domain}:")
        print(f"    - Specialization: {perf.get('specialization_score', 0):.3f}")
        print(f"    - Queries Answered: {perf.get('queries_answered', 0)}")

    print("\nDependency Check:")
    print(f"  - ChromaDB: {'✓ Available' if CHROMADB_AVAILABLE else '✗ Not available'}")
    print(f"  - FAISS: {'✓ Available' if FAISS_AVAILABLE else '✗ Not available'}")

    print("\n✓ Demo 6 complete")


async def run_all_demos():
    """Run all demonstration scenarios."""
    print("="*80)
    print("EXPERT SYSTEM COMPREHENSIVE DEMONSTRATION")
    print("="*80)
    print("\nThis demo showcases:")
    print("  1. Basic expert queries with RAG")
    print("  2. Multi-expert ensemble voting")
    print("  3. Automatic expert specialization")
    print("  4. Fine-tuning with multiple strategies")
    print("  5. Integration with autonomous business")
    print("  6. System status and diagnostics")

    demos = [
        demo_1_basic_queries,
        demo_2_ensemble_voting,
        demo_3_auto_specialization,
        demo_4_fine_tuning,
        demo_5_business_integration,
        demo_6_system_status
    ]

    for i, demo in enumerate(demos, 1):
        try:
            await demo()
        except Exception as e:
            print(f"\n✗ Demo {i} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("ALL DEMOS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_all_demos())

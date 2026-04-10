#!/usr/bin/env python3
"""
Expert System Test Suite
=========================

Unit and integration tests for the multi-domain expert system.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import sys
import unittest
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
    DatasetGenerator,
    TrainingExample,
    TrainingDataset
)


class TestExpertSystem(unittest.TestCase):
    """Test expert system core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    def test_system_initialization(self):
        """Test system initializes correctly."""
        self.assertIsNotNone(self.system)
        self.assertGreater(len(self.system.experts), 0)
        self.assertIsNotNone(self.system.vector_store)
        self.assertIsNotNone(self.system.ensemble)

    def test_experts_created(self):
        """Test all domain experts are created."""
        expected_domains = [
            ExpertDomain.CHEMISTRY,
            ExpertDomain.BIOLOGY,
            ExpertDomain.PHYSICS,
            ExpertDomain.MATERIALS_SCIENCE
        ]

        for domain in expected_domains:
            self.assertIn(domain, self.system.experts)
            expert = self.system.experts[domain]
            self.assertEqual(expert.domain, domain)
            self.assertGreater(expert.specialization_score, 0)

    def test_add_knowledge(self):
        """Test adding documents to knowledge base."""
        docs = [
            KnowledgeDocument(
                doc_id="test_001",
                content="Test content for chemistry",
                domain=ExpertDomain.CHEMISTRY,
                metadata={"test": True}
            )
        ]

        # Should not raise exception
        self.system.add_knowledge(docs)

    def test_system_status(self):
        """Test system status retrieval."""
        status = self.system.get_system_status()

        self.assertIn("total_experts", status)
        self.assertIn("domains", status)
        self.assertIn("vector_store_type", status)
        self.assertIn("expert_performance", status)

        self.assertGreater(status["total_experts"], 0)
        self.assertGreater(len(status["domains"]), 0)


class TestExpertQueries(unittest.IsolatedAsyncioTestCase):
    """Test expert query functionality."""

    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

        # Add test knowledge
        docs = [
            KnowledgeDocument(
                doc_id="chem_test",
                content="Chemical bonds include covalent, ionic, and metallic bonds.",
                domain=ExpertDomain.CHEMISTRY,
                metadata={"topic": "bonding"}
            ),
            KnowledgeDocument(
                doc_id="bio_test",
                content="DNA contains genetic information in the form of nucleotide sequences.",
                domain=ExpertDomain.BIOLOGY,
                metadata={"topic": "genetics"}
            )
        ]
        self.system.add_knowledge(docs)

    async def test_single_expert_query(self):
        """Test querying a single expert."""
        query = ExpertQuery(
            query="What are chemical bonds?",
            domain=ExpertDomain.CHEMISTRY
        )

        response = await self.system.query(query)

        self.assertIsNotNone(response)
        self.assertEqual(response.domain, ExpertDomain.CHEMISTRY)
        self.assertGreater(response.confidence, 0)
        self.assertIsNotNone(response.answer)
        self.assertIsInstance(response.sources, list)

    async def test_ensemble_query(self):
        """Test querying ensemble of experts."""
        query = ExpertQuery(
            query="What is the molecular basis of genetics?",
            use_ensemble=True
        )

        response = await self.system.query(query)

        self.assertIsNotNone(response)
        self.assertGreater(response.confidence, 0)
        self.assertGreater(response.agreement_score, 0)
        self.assertIsNotNone(response.consensus_answer)
        self.assertGreater(len(response.individual_responses), 0)
        self.assertGreater(len(response.domains_consulted), 0)

    async def test_auto_select_expert(self):
        """Test automatic expert selection."""
        query = ExpertQuery(
            query="Explain chemical reactions"
            # No domain specified, should auto-select
        )

        response = await self.system.query(query)

        self.assertIsNotNone(response)
        self.assertIsNotNone(response.domain)
        self.assertGreater(response.confidence, 0)


class TestSpecialization(unittest.IsolatedAsyncioTestCase):
    """Test expert specialization."""

    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    async def test_specialize_expert(self):
        """Test expert specialization improves performance."""
        domain = ExpertDomain.CHEMISTRY
        expert = self.system.experts[domain]

        initial_score = expert.specialization_score

        # Train with high-quality examples
        training_data = [
            ("What is water?", "H2O molecule", 0.95),
            ("What is oxygen?", "Element O2", 0.95),
            ("What is hydrogen?", "Element H2", 0.95)
        ]

        final_score = await self.system.specialize_expert(domain, training_data)

        # Should maintain or improve
        self.assertGreaterEqual(final_score, initial_score * 0.9)

    async def test_performance_tracking(self):
        """Test performance metrics tracking."""
        domain = ExpertDomain.CHEMISTRY

        training_data = [
            ("Test query 1", "Answer 1", 0.9),
            ("Test query 2", "Answer 2", 0.85)
        ]

        await self.system.specialize_expert(domain, training_data)

        performance = self.system.specialization_engine.get_expert_performance(domain)

        self.assertIn("expert_id", performance)
        self.assertIn("domain", performance)
        self.assertIn("specialization_score", performance)
        self.assertIn("queries_answered", performance)


class TestFineTuning(unittest.IsolatedAsyncioTestCase):
    """Test fine-tuning functionality."""

    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

    async def test_supervised_finetuning(self):
        """Test supervised learning fine-tuning."""
        dataset = DatasetGenerator.generate_chemistry_dataset(20)

        finetuner = ExpertFineTuner(
            self.system,
            strategy=TrainingStrategy.SUPERVISED_LEARNING
        )

        result = await finetuner.fine_tune_expert(
            domain=ExpertDomain.CHEMISTRY,
            dataset=dataset,
            epochs=2,
            batch_size=10,
            learning_rate=0.01
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.domain, ExpertDomain.CHEMISTRY)
        self.assertGreater(result.final_performance, 0)
        self.assertGreater(len(result.metrics_history), 0)

    async def test_dataset_generation(self):
        """Test training dataset generation."""
        datasets = {
            "chemistry": DatasetGenerator.generate_chemistry_dataset(50),
            "biology": DatasetGenerator.generate_biology_dataset(50),
            "physics": DatasetGenerator.generate_physics_dataset(50)
        }

        for name, dataset in datasets.items():
            self.assertEqual(len(dataset.examples), 50)
            self.assertIsInstance(dataset.examples[0], TrainingExample)
            self.assertGreater(dataset.examples[0].quality_score, 0)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests."""

    async def test_end_to_end_workflow(self):
        """Test complete workflow: add knowledge -> query -> specialize -> query again."""
        system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

        # 1. Add knowledge
        docs = [
            KnowledgeDocument(
                doc_id="integration_test",
                content="Photosynthesis converts light energy into chemical energy in plants.",
                domain=ExpertDomain.BIOLOGY,
                metadata={"test": "integration"}
            )
        ]
        system.add_knowledge(docs)

        # 2. Query before specialization
        query1 = ExpertQuery(
            query="What is photosynthesis?",
            domain=ExpertDomain.BIOLOGY
        )
        response1 = await system.query(query1)
        confidence1 = response1.confidence

        # 3. Specialize expert
        training_data = [
            ("What is photosynthesis?", "Process converting light to energy", 0.95)
        ]
        await system.specialize_expert(ExpertDomain.BIOLOGY, training_data)

        # 4. Query after specialization (should have similar or better confidence)
        response2 = await system.query(query1)
        confidence2 = response2.confidence

        # Confidence should not degrade significantly
        self.assertGreater(confidence2, confidence1 * 0.8)


def run_tests():
    """Run all tests."""
    print("="*80)
    print("EXPERT SYSTEM TEST SUITE")
    print("="*80)

    # Check dependencies
    print("\nDependency Check:")
    print(f"  ChromaDB: {'✓' if CHROMADB_AVAILABLE else '✗'}")
    print(f"  FAISS: {'✓' if FAISS_AVAILABLE else '✗'}")

    if not (CHROMADB_AVAILABLE or FAISS_AVAILABLE):
        print("\n✗ No vector store available. Install chromadb or faiss-cpu.")
        return False

    print("\nRunning tests...\n")

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestExpertSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestExpertQueries))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecialization))
    suite.addTests(loader.loadTestsFromTestCase(TestFineTuning))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*80)
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

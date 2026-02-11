import pytest
import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.all_features_implementation import ABTestingFramework, ABTest

class TestABTestingFramework:
    def test_initialization(self):
        """Test that the framework initializes with no active tests."""
        framework = ABTestingFramework()
        assert framework.active_tests == {}

    def test_create_test(self):
        """Test creating a new A/B test."""
        framework = ABTestingFramework()
        name = "Homepage Redesign"
        variant_a = {"button_color": "blue", "hero_text": "Welcome"}
        variant_b = {"button_color": "green", "hero_text": "Get Started"}

        test = asyncio.run(framework.create_test(name, variant_a, variant_b))

        assert isinstance(test, ABTest)
        assert test.name == name
        assert test.variant_a == variant_a
        assert test.variant_b == variant_b
        assert test.status == "running"
        assert test.id in framework.active_tests
        assert framework.active_tests[test.id] == test

    def test_analyze_results(self):
        """Test analyzing results (mock implementation check)."""
        framework = ABTestingFramework()
        test_id = "test_123"

        results = asyncio.run(framework.analyze_results(test_id))

        assert results["test_id"] == test_id
        assert "variant_a" in results
        assert "variant_b" in results
        # Based on current hardcoded implementation
        assert results["winner"] == "variant_b"
        assert results["confidence"] == 0.95
        assert results["improvement"] == 27.3

    def test_create_test_unique_ids(self):
        """Test that different tests get different IDs."""
        framework = ABTestingFramework()

        async def create_two_tests():
            t1 = await framework.create_test("Test 1", {}, {})
            t2 = await framework.create_test("Test 2", {}, {})
            return t1, t2

        test1, test2 = asyncio.run(create_two_tests())

        assert test1.id != test2.id

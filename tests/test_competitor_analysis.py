"""
Tests for CompetitorAnalysisEngine with mocked dependencies.
"""
import sys
import pytest
import asyncio
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing the module under test
mock_numpy = MagicMock()
sys.modules['numpy'] = mock_numpy

mock_openai = MagicMock()
sys.modules['openai'] = mock_openai
mock_requests = MagicMock()
sys.modules['requests'] = mock_requests
mock_fastapi = MagicMock()
sys.modules['fastapi'] = mock_fastapi
mock_anthropic = MagicMock()
sys.modules['anthropic'] = mock_anthropic
mock_stripe = MagicMock()
sys.modules['stripe'] = mock_stripe
mock_cryptography = MagicMock()
sys.modules['cryptography'] = mock_cryptography
mock_cryptography.fernet = MagicMock()
sys.modules['cryptography.fernet'] = mock_cryptography.fernet

# Now import the class to test
from src.blank_business_builder.all_features_implementation import (
    CompetitorAnalysisEngine,
    CompetitorProfile
)

class TestCompetitorAnalysisEngine:
    """Test suite for CompetitorAnalysisEngine."""

    @pytest.fixture
    def engine(self):
        """Fixture for CompetitorAnalysisEngine instance."""
        return CompetitorAnalysisEngine()

    def test_analyze_competitor_structure(self, engine):
        """Test the structure of the returned CompetitorProfile."""
        async def run_test():
            domain = "example.com"
            profile = await engine.analyze_competitor(domain)

            assert isinstance(profile, CompetitorProfile)
            assert profile.domain == domain
            assert isinstance(profile.name, str)
            assert isinstance(profile.market_share, float)
            assert isinstance(profile.pricing, dict)
            assert isinstance(profile.strengths, list)
            assert isinstance(profile.weaknesses, list)
            assert isinstance(profile.threat_level, float)

            # Check value ranges/validity without asserting specific hardcoded values
            assert 0.0 <= profile.market_share <= 1.0
            assert 0.0 <= profile.threat_level <= 1.0
            assert len(profile.strengths) > 0
            assert len(profile.weaknesses) > 0

        asyncio.run(run_test())

    def test_analyze_competitor_name_extraction(self, engine):
        """Test name extraction from various domain formats."""
        async def run_test():
            test_cases = [
                ("example.com", "Example"),
                ("sub.domain.com", "Sub"),
                ("google.co.uk", "Google"),
                ("localhost", "Localhost"),
                ("my-site.net", "My-Site"),
            ]

            for domain, expected_name in test_cases:
                profile = await engine.analyze_competitor(domain)
                assert profile.name == expected_name, f"Failed for domain: {domain}"

        asyncio.run(run_test())

    def test_generate_competitive_strategy_structure(self, engine):
        """Test the structure of the generated strategy."""
        async def run_test():
            competitors = [
                CompetitorProfile(
                    name="Comp1",
                    domain="comp1.com",
                    market_share=0.2,
                    pricing={"basic": 50.0, "pro": 100.0},
                    strengths=["s1"],
                    weaknesses=["w1"],
                    threat_level=0.5
                ),
                CompetitorProfile(
                    name="Comp2",
                    domain="comp2.com",
                    market_share=0.3,
                    pricing={"basic": 60.0, "pro": 120.0},
                    strengths=["s2"],
                    weaknesses=["w2"],
                    threat_level=0.7
                )
            ]

            strategy = await engine.generate_competitive_strategy(competitors)

            assert isinstance(strategy, dict)
            assert "recommended_pricing" in strategy
            assert "differentiation_opportunities" in strategy
            assert "market_gaps" in strategy

            pricing = strategy["recommended_pricing"]
            assert isinstance(pricing, dict)
            assert "basic" in pricing
            assert "pro" in pricing
            assert "enterprise" in pricing

            # Verify basic pricing logic (should be lower than competitors' min)
            # Min basic is 50.0, so recommended should be 50 * 0.8 = 40.0
            assert pricing["basic"] == 40.0

            assert isinstance(strategy["differentiation_opportunities"], list)
            assert len(strategy["differentiation_opportunities"]) > 0
            assert isinstance(strategy["market_gaps"], list)
            assert len(strategy["market_gaps"]) > 0

        asyncio.run(run_test())

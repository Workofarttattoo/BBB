import pytest
import sys
from pathlib import Path

# Add scripts/tools to path so we can import bbb_real_business_library
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "tools"))

from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

@pytest.fixture
def library():
    return BBBRealBusinessLibrary()

@pytest.fixture
def mock_businesses():
    return [
        RealBusinessModel(
            name="Business 1", website="test", category="test", description="test", startup_cost=0,
            monthly_revenue_potential=1000, automation_level=100, time_commitment_hours_week=0, difficulty="easy",
            tools_required=[], revenue_streams=[], target_market="test", success_probability=0.8,
            time_to_profit_months="0-1", unique_value_prop="test", competitive_advantage="test", scaling_potential="high"
        ), # Score: 800
        RealBusinessModel(
            name="Business 2", website="test", category="test", description="test", startup_cost=0,
            monthly_revenue_potential=2000, automation_level=100, time_commitment_hours_week=0, difficulty="easy",
            tools_required=[], revenue_streams=[], target_market="test", success_probability=0.5,
            time_to_profit_months="0-1", unique_value_prop="test", competitive_advantage="test", scaling_potential="high"
        ), # Score: 1000
        RealBusinessModel(
            name="Business 3", website="test", category="test", description="test", startup_cost=0,
            monthly_revenue_potential=500, automation_level=100, time_commitment_hours_week=0, difficulty="easy",
            tools_required=[], revenue_streams=[], target_market="test", success_probability=0.9,
            time_to_profit_months="0-1", unique_value_prop="test", competitive_advantage="test", scaling_potential="high"
        ), # Score: 450
        RealBusinessModel(
            name="Business 4", website="test", category="test", description="test", startup_cost=0,
            monthly_revenue_potential=5000, automation_level=100, time_commitment_hours_week=0, difficulty="easy",
            tools_required=[], revenue_streams=[], target_market="test", success_probability=0.1,
            time_to_profit_months="0-1", unique_value_prop="test", competitive_advantage="test", scaling_potential="high"
        ), # Score: 500
    ]

def test_get_top_opportunities_sorts_correctly(library, mock_businesses):
    """Test that businesses are sorted by expected value (revenue * probability) descending."""
    library.businesses = mock_businesses

    results = library.get_top_opportunities(limit=4)

    assert len(results) == 4
    assert results[0].name == "Business 2" # 1000
    assert results[1].name == "Business 1" # 800
    assert results[2].name == "Business 4" # 500
    assert results[3].name == "Business 3" # 450

def test_get_top_opportunities_respects_limit(library, mock_businesses):
    """Test that the limit parameter is respected."""
    library.businesses = mock_businesses

    results = library.get_top_opportunities(limit=2)

    assert len(results) == 2
    assert results[0].name == "Business 2"
    assert results[1].name == "Business 1"

def test_get_top_opportunities_empty_list():
    """Test that an empty list is handled correctly."""
    library = BBBRealBusinessLibrary()
    library.businesses = []

    results = library.get_top_opportunities()

    assert results == []

def test_get_top_opportunities_limit_greater_than_businesses(library, mock_businesses):
    """Test when limit is greater than the number of available businesses."""
    library.businesses = mock_businesses

    results = library.get_top_opportunities(limit=10)

    assert len(results) == 4

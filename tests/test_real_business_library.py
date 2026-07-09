import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add the scripts/tools directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "tools"))

from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

@pytest.fixture
def business_library():
    # Setup dummy data for testing filtering logic
    library = BBBRealBusinessLibrary()

    # Overwrite the actual business data with simple dummy data for deterministic testing
    library.businesses = [
        RealBusinessModel(
            name="Alpha Corp",
            website="alpha.com",
            category="Technology",
            description="Alpha",
            startup_cost=1000,
            monthly_revenue_potential=5000,
            automation_level=80,
            revenue_streams=["Software"],
            target_market="B2B",
            success_probability=0.9,
            time_to_profit_months="1-3",
            unique_value_prop="Fast",
            competitive_advantage="Patents",
            scaling_potential="High",
            time_commitment_hours_week=10,
            difficulty="Medium",
            tools_required=["Computer"]
        ),
        RealBusinessModel(
            name="Beta LLC",
            website="beta.com",
            category="Consulting",
            description="Beta",
            startup_cost=500,
            monthly_revenue_potential=3000,
            automation_level=20,
            revenue_streams=["Services"],
            target_market="B2C",
            success_probability=0.7,
            time_to_profit_months="3-6",
            unique_value_prop="Personalized",
            competitive_advantage="Experience",
            scaling_potential="Medium",
            time_commitment_hours_week=40,
            difficulty="Hard",
            tools_required=["Phone"]
        ),
        RealBusinessModel(
            name="Gamma Tech",
            website="gamma.com",
            category="Technology",
            description="Gamma",
            startup_cost=2000,
            monthly_revenue_potential=10000,
            automation_level=95,
            revenue_streams=["Hardware", "Software"],
            target_market="Enterprise",
            success_probability=0.85,
            time_to_profit_months="6-12",
            unique_value_prop="Advanced",
            competitive_advantage="R&D",
            scaling_potential="Very High",
            time_commitment_hours_week=20,
            difficulty="Hard",
            tools_required=["Lab"]
        )
    ]

    return library

def test_get_businesses_by_category_exists(business_library):
    """Test retrieving businesses for an existing category."""
    tech_businesses = business_library.get_businesses_by_category("Technology")

    assert len(tech_businesses) == 2
    assert all(b.category == "Technology" for b in tech_businesses)

    names = {b.name for b in tech_businesses}
    assert "Alpha Corp" in names
    assert "Gamma Tech" in names
    assert "Beta LLC" not in names

def test_get_businesses_by_category_not_exists(business_library):
    """Test retrieving businesses for a non-existent category returns empty list."""
    empty_result = business_library.get_businesses_by_category("Retail")

    assert empty_result == []
    assert len(empty_result) == 0

def test_get_businesses_by_website_exists(business_library):
    """Test retrieving businesses for an existing website."""
    beta_business = business_library.get_businesses_by_website("beta.com")

    assert len(beta_business) == 1
    assert beta_business[0].name == "Beta LLC"
    assert beta_business[0].website == "beta.com"

def test_get_businesses_by_website_not_exists(business_library):
    """Test retrieving businesses for a non-existent website returns empty list."""
    empty_result = business_library.get_businesses_by_website("nonexistent.com")

    assert empty_result == []
    assert len(empty_result) == 0

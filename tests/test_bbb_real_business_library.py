import sys
import os
import pytest

# Add scripts/tools to sys.path to allow importing bbb_real_business_library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/tools')))

from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

def create_mock_business(name: str, time_to_profit_months: str) -> RealBusinessModel:
    return RealBusinessModel(
        name=name,
        website="test.com",
        category="Test",
        description="Test",
        startup_cost=100,
        monthly_revenue_potential=1000,
        automation_level=100,
        time_commitment_hours_week=10,
        difficulty="Easy",
        tools_required=[],
        revenue_streams=[],
        target_market="Test",
        success_probability=0.9,
        time_to_profit_months=time_to_profit_months,
        unique_value_prop="Test",
        competitive_advantage="Test",
        scaling_potential="High"
    )

def test_get_quick_wins():
    """Test that get_quick_wins correctly filters businesses with time_to_profit_months <= 6"""

    # Create dummy businesses with various time_to_profit_months
    businesses = [
        create_mock_business("Quick Win 1", "1-3"),      # First num = 1 (<= 6)
        create_mock_business("Quick Win 2", "6-12"),     # First num = 6 (<= 6)
        create_mock_business("Slow Win 1", "7-12"),      # First num = 7 (> 6)
        create_mock_business("Slow Win 2", "12-24"),     # First num = 12 (> 6)
        create_mock_business("Quick Win 3 Exact", "4"),  # First num = 4 (<= 6)
        create_mock_business("Slow Win 3 Exact", "8"),   # First num = 8 (> 6)
    ]

    # Initialize the library with the dummy businesses
    library = BBBRealBusinessLibrary()
    library.businesses = businesses

    # Call the method
    quick_wins = library.get_quick_wins()

    # Verify the results
    assert len(quick_wins) == 3

    names = [b.name for b in quick_wins]
    assert "Quick Win 1" in names
    assert "Quick Win 2" in names
    assert "Quick Win 3 Exact" in names
    assert "Slow Win 1" not in names
    assert "Slow Win 2" not in names
    assert "Slow Win 3 Exact" not in names

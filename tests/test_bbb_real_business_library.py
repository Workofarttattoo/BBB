import pytest
import sys
from pathlib import Path

# Add the tools directory to the Python path
tools_dir = Path(__file__).parent.parent / "scripts" / "tools"
sys.path.insert(0, str(tools_dir))

from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

def test_get_quick_wins():
    """Test get_quick_wins filters businesses with time_to_profit_months <= 6."""

    # Create an instance of the library
    library = BBBRealBusinessLibrary()

    # Seed with mock data
    mock_businesses = [
        RealBusinessModel(
            name="Quick Profit 1",
            website="quick1.com",
            category="Test",
            description="Test",
            startup_cost=1000,
            monthly_revenue_potential=1000,
            automation_level=50,
            time_commitment_hours_week=10,
            difficulty="Low",
            tools_required=[],
            revenue_streams=[],
            target_market="Test",
            success_probability=0.9,
            time_to_profit_months="2-5", # <= 6
            unique_value_prop="Test",
            competitive_advantage="Test",
            scaling_potential="Test"
        ),
        RealBusinessModel(
            name="Exact Profit 6",
            website="exact6.com",
            category="Test",
            description="Test",
            startup_cost=1000,
            monthly_revenue_potential=1000,
            automation_level=50,
            time_commitment_hours_week=10,
            difficulty="Low",
            tools_required=[],
            revenue_streams=[],
            target_market="Test",
            success_probability=0.9,
            time_to_profit_months="6-12", # <= 6
            unique_value_prop="Test",
            competitive_advantage="Test",
            scaling_potential="Test"
        ),
        RealBusinessModel(
            name="Slow Profit",
            website="slow.com",
            category="Test",
            description="Test",
            startup_cost=1000,
            monthly_revenue_potential=1000,
            automation_level=50,
            time_commitment_hours_week=10,
            difficulty="Low",
            tools_required=[],
            revenue_streams=[],
            target_market="Test",
            success_probability=0.9,
            time_to_profit_months="7-12", # > 6
            unique_value_prop="Test",
            competitive_advantage="Test",
            scaling_potential="Test"
        ),
        RealBusinessModel(
            name="Single Month Profit",
            website="single.com",
            category="Test",
            description="Test",
            startup_cost=1000,
            monthly_revenue_potential=1000,
            automation_level=50,
            time_commitment_hours_week=10,
            difficulty="Low",
            tools_required=[],
            revenue_streams=[],
            target_market="Test",
            success_probability=0.9,
            time_to_profit_months="4", # <= 6
            unique_value_prop="Test",
            competitive_advantage="Test",
            scaling_potential="Test"
        ),
        RealBusinessModel(
            name="Long Term Profit",
            website="long.com",
            category="Test",
            description="Test",
            startup_cost=1000,
            monthly_revenue_potential=1000,
            automation_level=50,
            time_commitment_hours_week=10,
            difficulty="Low",
            tools_required=[],
            revenue_streams=[],
            target_market="Test",
            success_probability=0.9,
            time_to_profit_months="12", # > 6
            unique_value_prop="Test",
            competitive_advantage="Test",
            scaling_potential="Test"
        )
    ]

    library.businesses = mock_businesses

    # Execute
    quick_wins = library.get_quick_wins()

    # Verify
    assert len(quick_wins) == 3
    quick_win_names = [b.name for b in quick_wins]
    assert "Quick Profit 1" in quick_win_names
    assert "Exact Profit 6" in quick_win_names
    assert "Single Month Profit" in quick_win_names
    assert "Slow Profit" not in quick_win_names
    assert "Long Term Profit" not in quick_win_names

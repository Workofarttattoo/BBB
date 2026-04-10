import sys
import os
import pytest

# Add scripts/tools to path so we can import bbb_real_business_library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/tools')))

from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

def create_mock_business(name: str, time_to_profit: str) -> RealBusinessModel:
    """Helper to create a RealBusinessModel with dummy data and specific time_to_profit_months."""
    return RealBusinessModel(
        name=name,
        website="example.com",
        category="Test Category",
        description="A test description.",
        startup_cost=1000,
        monthly_revenue_potential=5000,
        automation_level=80,
        time_commitment_hours_week=10,
        difficulty="Low",
        tools_required=[],
        revenue_streams=[],
        target_market="Test Market",
        success_probability=0.9,
        time_to_profit_months=time_to_profit,
        unique_value_prop="Value",
        competitive_advantage="Advantage",
        scaling_potential="High"
    )

class TestBBBRealBusinessLibrary:
    """Test suite for BBBRealBusinessLibrary."""

    def test_get_quick_wins(self):
        """Test that get_quick_wins returns only businesses with a start time <= 6 months."""
        library = BBBRealBusinessLibrary()

        # Overwrite the default list of businesses with our seeded models
        mock_businesses = [
            create_mock_business("Fast Business 1", "1-3"),     # Quick win (1 <= 6)
            create_mock_business("Fast Business 2", "6-8"),     # Quick win (6 <= 6)
            create_mock_business("Fast Business 3", "6"),       # Quick win (6 <= 6)
            create_mock_business("Slow Business 1", "7-12"),    # Not a quick win (7 > 6)
            create_mock_business("Slow Business 2", "12-24"),   # Not a quick win (12 > 6)
            create_mock_business("Slow Business 3", "8"),       # Not a quick win (8 > 6)
        ]
        library.businesses = mock_businesses

        quick_wins = library.get_quick_wins()
        quick_win_names = [b.name for b in quick_wins]

        # Assert correct number of quick wins
        assert len(quick_wins) == 3

        # Assert the correct businesses are returned
        assert "Fast Business 1" in quick_win_names
        assert "Fast Business 2" in quick_win_names
        assert "Fast Business 3" in quick_win_names

        # Assert slow businesses are excluded
        assert "Slow Business 1" not in quick_win_names
        assert "Slow Business 2" not in quick_win_names
        assert "Slow Business 3" not in quick_win_names

    def test_get_quick_wins_empty(self):
        """Test that get_quick_wins handles an empty list of businesses."""
        library = BBBRealBusinessLibrary()
        library.businesses = []

        assert library.get_quick_wins() == []

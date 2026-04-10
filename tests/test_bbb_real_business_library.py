import pytest
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.tools.bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

class MockRealBusinessLibrary(BBBRealBusinessLibrary):
    def _load_real_businesses(self):
        return [
            RealBusinessModel(
                name="Mock Business 1",
                website="mock1.com",
                category="AI Consulting",
                description="A mock AI consulting business",
                startup_cost=10000,
                monthly_revenue_potential=50000,
                automation_level=80,
                time_commitment_hours_week=20,
                difficulty="Medium",
                tools_required=["tool1", "tool2"],
                revenue_streams=["stream1"],
                target_market="Market 1",
                success_probability=0.8,
                time_to_profit_months="3-6",
                unique_value_prop="UVP 1",
                competitive_advantage="Advantage 1",
                scaling_potential="High"
            ),
            RealBusinessModel(
                name="Mock Business 2",
                website="mock2.com",
                category="Healthcare AI",
                description="A mock Healthcare AI business",
                startup_cost=20000,
                monthly_revenue_potential=100000,
                automation_level=90,
                time_commitment_hours_week=10,
                difficulty="High",
                tools_required=["tool3", "tool4"],
                revenue_streams=["stream2"],
                target_market="Market 2",
                success_probability=0.6,
                time_to_profit_months="12-24",
                unique_value_prop="UVP 2",
                competitive_advantage="Advantage 2",
                scaling_potential="Medium"
            )
        ]

def test_get_business_summary():
    """Verify that get_business_summary calculates statistics correctly using a mock library."""
    # Arrange
    library = MockRealBusinessLibrary()

    # Act
    summary = library.get_business_summary()

    # Assert
    assert summary['total_businesses'] == 2
    assert summary['total_monthly_revenue_potential'] == 150000  # 50k + 100k
    assert summary['average_automation_level'] == 85.0  # (80 + 90) / 2
    assert set(summary['categories']) == {"AI Consulting", "Healthcare AI"}
    assert set(summary['websites']) == {"mock1.com", "mock2.com"}
    assert summary['quick_win_businesses'] == 1  # Mock Business 1 is "3-6", Business 2 is "12-24"
    assert summary['top_opportunity'] == "Mock Business 2"  # 100k * 0.6 = 60k > 50k * 0.8 = 40k

def test_get_business_summary_empty():
    """Verify that get_business_summary correctly handles an empty business list gracefully or raises ZeroDivisionError."""
    # Arrange
    library = BBBRealBusinessLibrary()
    library.businesses = [] # Mock empty state

    # Act & Assert
    with pytest.raises(ZeroDivisionError):
        library.get_business_summary()

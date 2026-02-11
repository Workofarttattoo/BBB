"""
Tests for business data models.
"""

import pytest
from src.blank_business_builder.business_data import BusinessIdea

def test_business_idea_monthly_profit():
    """Test monthly profit calculation."""
    # Test case 1: Positive profit
    idea1 = BusinessIdea(
        name="Test Idea 1",
        industry="Tech",
        ramp_up_months=1,
        startup_cost=1000.0,
        expected_monthly_revenue=5000.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=10,
        description="A test idea"
    )
    assert idea1.monthly_profit == 3000.0

    # Test case 2: Zero profit (Break-even)
    idea2 = BusinessIdea(
        name="Test Idea 2",
        industry="Tech",
        ramp_up_months=1,
        startup_cost=1000.0,
        expected_monthly_revenue=2000.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=10,
        description="A test idea"
    )
    assert idea2.monthly_profit == 0.0

    # Test case 3: Negative profit (Loss)
    idea3 = BusinessIdea(
        name="Test Idea 3",
        industry="Tech",
        ramp_up_months=1,
        startup_cost=1000.0,
        expected_monthly_revenue=1500.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=10,
        description="A test idea"
    )
    assert idea3.monthly_profit == -500.0

    # Test case 4: Floating point precision check
    idea4 = BusinessIdea(
        name="Test Idea 4",
        industry="Tech",
        ramp_up_months=1,
        startup_cost=1000.0,
        expected_monthly_revenue=10.1,
        expected_monthly_expenses=0.1,
        time_commitment_hours_per_week=10,
        description="A test idea"
    )
    assert idea4.monthly_profit == pytest.approx(10.0)

def test_business_idea_initialization():
    """Test that BusinessIdea can be initialized correctly."""
    idea = BusinessIdea(
        name="Valid Idea",
        industry="Valid Industry",
        ramp_up_months=3,
        startup_cost=5000.0,
        expected_monthly_revenue=10000.0,
        expected_monthly_expenses=4000.0,
        time_commitment_hours_per_week=20,
        description="Valid description"
    )

    assert idea.name == "Valid Idea"
    assert idea.industry == "Valid Industry"
    assert idea.ramp_up_months == 3
    assert idea.startup_cost == 5000.0
    assert idea.expected_monthly_revenue == 10000.0
    assert idea.expected_monthly_expenses == 4000.0
    assert idea.time_commitment_hours_per_week == 20
    assert idea.description == "Valid description"

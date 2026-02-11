"""
Tests for the QuantumOptimizer class.
"""

import pytest
from math import sqrt
from src.blank_business_builder.business_data import BusinessIdea
from src.blank_business_builder.quantum_optimizer import QuantumOptimizer, OptimizationResult

@pytest.fixture
def sample_idea_1():
    """A standard business idea with a 3-month ramp-up."""
    return BusinessIdea(
        name="Standard Idea",
        industry="Tech",
        ramp_up_months=3,
        startup_cost=5000.0,
        expected_monthly_revenue=10000.0,
        expected_monthly_expenses=4000.0,
        time_commitment_hours_per_week=20,
        description="Standard description"
    )

@pytest.fixture
def sample_idea_2():
    """A business idea with a short ramp-up (1 month)."""
    return BusinessIdea(
        name="Quick Idea",
        industry="Service",
        ramp_up_months=1,
        startup_cost=1000.0,
        expected_monthly_revenue=5000.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=10,
        description="Quick description"
    )

@pytest.fixture
def sample_idea_3():
    """A business idea with high startup costs (negative initial profit)."""
    return BusinessIdea(
        name="Expensive Idea",
        industry="Manufacturing",
        ramp_up_months=6,
        startup_cost=50000.0,
        expected_monthly_revenue=8000.0,
        expected_monthly_expenses=4000.0,
        time_commitment_hours_per_week=40,
        description="Expensive description"
    )

def test_initialization():
    """Test default and custom initialization."""
    # Default
    optimizer = QuantumOptimizer()
    assert optimizer.monthly_floor == 4500.0
    assert optimizer.quarter_target == 20000.0

    # Custom
    optimizer_custom = QuantumOptimizer(monthly_floor=5000.0, quarter_target=25000.0)
    assert optimizer_custom.monthly_floor == 5000.0
    assert optimizer_custom.quarter_target == 25000.0

def test_project_profit_ramping(sample_idea_1):
    """Test profit projection during ramp-up period."""
    optimizer = QuantumOptimizer()

    # Idea 1: ramp_up=3, monthly_profit=6000, startup=5000
    # Month 1: 1/3 * 6000 = 2000
    # Month 2: 2/3 * 6000 = 4000
    # Month 3: 3/3 * 6000 = 6000
    # Total effective months = 1/3 + 2/3 + 3/3 = 2.0
    # Total revenue = 2.0 * 6000 = 12000
    # Net profit = 12000 - 5000 = 7000

    profit_3_months = optimizer.project_profit(sample_idea_1, months=3)
    assert profit_3_months == pytest.approx(7000.0)

def test_project_profit_steady_state(sample_idea_2):
    """Test profit projection after ramp-up period."""
    optimizer = QuantumOptimizer()

    # Idea 2: ramp_up=1, monthly_profit=3000, startup=1000
    # Month 1: 1/1 * 3000 = 3000
    # Month 2: 1.0 * 3000 = 3000
    # Month 3: 1.0 * 3000 = 3000
    # Total effective months = 3.0
    # Total revenue = 3.0 * 3000 = 9000
    # Net profit = 9000 - 1000 = 8000

    profit_3_months = optimizer.project_profit(sample_idea_2, months=3)
    assert profit_3_months == 8000.0

def test_project_profit_negative_clipped(sample_idea_3):
    """Test that profit is clipped to 0.0 if negative."""
    optimizer = QuantumOptimizer()

    # Idea 3: startup=50000, profit=4000/mo, ramp=6
    # Even after 3 months, it won't cover startup costs.
    # Month 1: 1/6 * 4000 = 666.67
    # Month 2: 2/6 * 4000 = 1333.33
    # Month 3: 3/6 * 4000 = 2000.00
    # Total revenue < 50000 -> Net profit negative -> clipped to 0.0

    profit_3_months = optimizer.project_profit(sample_idea_3, months=3)
    assert profit_3_months == 0.0

def test_evaluate_empty():
    """Test evaluate with empty list."""
    optimizer = QuantumOptimizer()
    results = optimizer.evaluate([])
    assert results == []

def test_evaluate_single(sample_idea_1):
    """Test evaluate with a single idea."""
    optimizer = QuantumOptimizer()
    results = optimizer.evaluate([sample_idea_1])

    assert len(results) == 1
    res = results[0]
    assert res.idea == sample_idea_1
    # Profit calculated earlier as 7000.0 for 3 months
    assert res.three_month_profit == 7000.0
    # Monthly average = 7000 / 3 = 2333.33
    assert res.monthly_average == pytest.approx(2333.33, abs=0.01)
    # Success probability: amplitude^2. Since only 1 idea, amplitude should be 1.0 -> prob 1.0
    assert res.success_probability == 1.0

    # Floor: 2333.33 < 4500 (default) -> False
    assert res.meets_floor is False
    # Target: 7000 < 20000 (default) -> False
    assert res.meets_target is False

def test_evaluate_multiple(sample_idea_1, sample_idea_2):
    """Test evaluate with multiple ideas to check ranking."""
    optimizer = QuantumOptimizer()

    # Idea 1 profit (3mo): 7000
    # Idea 2 profit (3mo): 8000

    results = optimizer.evaluate([sample_idea_1, sample_idea_2])

    assert len(results) == 2
    # Sorting: highest probability/profit first.
    # Profits: [7000, 8000]
    # Amplitudes calculation:
    # total = 15000
    # amp1 = sqrt(7000/15000) = sqrt(0.4666) ≈ 0.683
    # amp2 = sqrt(8000/15000) = sqrt(0.5333) ≈ 0.730
    # norm = sqrt(amp1^2 + amp2^2) = sqrt(0.4666 + 0.5333) = 1.0
    # probabilities = amp^2 -> [0.4666, 0.5333]

    # Idea 2 should be first
    assert results[0].idea == sample_idea_2
    assert results[1].idea == sample_idea_1

    assert results[0].three_month_profit == 8000.0
    assert results[1].three_month_profit == 7000.0

    # Check probabilities roughly sum to 1 (with rounding)
    prob_sum = results[0].success_probability + results[1].success_probability
    assert prob_sum == pytest.approx(1.0, abs=0.01)

def test_evaluate_zero_profit_fallback(sample_idea_3):
    """Test fallback to uniform distribution when all profits are 0."""
    optimizer = QuantumOptimizer()

    # Idea 3 yields 0.0 profit in 3 months.
    # Pass two of them.
    results = optimizer.evaluate([sample_idea_3, sample_idea_3])

    assert len(results) == 2
    # Both should have 0 profit
    assert results[0].three_month_profit == 0.0
    assert results[1].three_month_profit == 0.0

    # Probabilities should be uniform: 1/sqrt(2)^2 = 0.5
    # Wait, implementation says: returns [1.0/sqrt(len) for _ in profits] as amplitudes
    # Then probability = amplitude^2
    # 1/sqrt(2) = 0.707...
    # 0.707^2 = 0.5

    assert results[0].success_probability == 0.5
    assert results[1].success_probability == 0.5

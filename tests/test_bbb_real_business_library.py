import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure scripts/tools is in path to import bbb_real_business_library
sys.path.insert(0, str(Path("scripts/tools")))
from bbb_real_business_library import BBBRealBusinessLibrary, RealBusinessModel

@pytest.fixture
def empty_library():
    library = BBBRealBusinessLibrary()
    library.businesses = []
    return library

def mock_business(name, revenue, prob):
    b = MagicMock(spec=RealBusinessModel)
    b.name = name
    b.monthly_revenue_potential = revenue
    b.success_probability = prob
    return b

def test_get_top_opportunities_sorting(empty_library):
    """Test that businesses are correctly sorted by revenue * probability."""
    b1 = mock_business("B1", 1000, 0.5) # Score: 500
    b2 = mock_business("B2", 2000, 0.8) # Score: 1600
    b3 = mock_business("B3", 3000, 0.4) # Score: 1200
    b4 = mock_business("B4", 500, 1.0)  # Score: 500

    empty_library.businesses = [b1, b2, b3, b4]

    ops = empty_library.get_top_opportunities(limit=4)
    assert len(ops) == 4
    assert ops[0].name == "B2" # 1600
    assert ops[1].name == "B3" # 1200
    # b1 and b4 both have 500, order between them is maintained from original list
    assert ops[2].name == "B1" or ops[2].name == "B4"
    assert ops[3].name == "B4" or ops[3].name == "B1"

def test_get_top_opportunities_limit(empty_library):
    """Test that the limit parameter restricts the number of returned opportunities."""
    b1 = mock_business("B1", 1000, 0.5)
    b2 = mock_business("B2", 2000, 0.8)
    b3 = mock_business("B3", 3000, 0.4)

    empty_library.businesses = [b1, b2, b3]

    # Default limit is 5, shouldn't crash if we have fewer
    ops = empty_library.get_top_opportunities()
    assert len(ops) == 3

    # Custom limit smaller than list
    ops = empty_library.get_top_opportunities(limit=2)
    assert len(ops) == 2
    assert ops[0].name == "B2"
    assert ops[1].name == "B3"

def test_get_top_opportunities_empty(empty_library):
    """Test behavior with an empty business list."""
    ops = empty_library.get_top_opportunities()
    assert len(ops) == 0

def test_get_top_opportunities_limit_exceeds_list(empty_library):
    """Test when the limit is greater than the number of available businesses."""
    b1 = mock_business("B1", 1000, 0.5)
    empty_library.businesses = [b1]

    ops = empty_library.get_top_opportunities(limit=10)
    assert len(ops) == 1
    assert ops[0].name == "B1"

def test_get_top_opportunities_zero_values(empty_library):
    """Test with zero revenue or zero probability."""
    b1 = mock_business("B1", 0, 0.5)    # Score: 0
    b2 = mock_business("B2", 1000, 0.0) # Score: 0
    b3 = mock_business("B3", 100, 0.1)  # Score: 10

    empty_library.businesses = [b1, b2, b3]
    ops = empty_library.get_top_opportunities(limit=3)

    assert len(ops) == 3
    assert ops[0].name == "B3" # Highest score
    # b1 and b2 both have score 0

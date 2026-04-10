import pytest
import sys
import os

# Add root directory to path to allow importing from scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.tools.bbb_real_business_library import BBBRealBusinessLibrary, get_real_business_library, RealBusinessModel

def test_get_all_businesses():
    """Test get_all_businesses returns the expected list of business models."""
    library = get_real_business_library()
    businesses = library.get_all_businesses()

    # Check that businesses is a list
    assert isinstance(businesses, list)

    # Check that it's the exact same list (or at least equal) to library.businesses
    assert businesses == library.businesses

    # Assuming there are businesses initialized
    assert len(businesses) > 0

    # Verify that the returned objects are indeed RealBusinessModel instances
    for business in businesses:
        assert isinstance(business, RealBusinessModel)

def test_get_all_businesses_empty():
    """Test get_all_businesses when the list is empty."""
    library = BBBRealBusinessLibrary()
    # Manually clear the list for this test
    library.businesses = []

    businesses = library.get_all_businesses()

    # Check that businesses is a list
    assert isinstance(businesses, list)

    # Check that it's empty
    assert len(businesses) == 0

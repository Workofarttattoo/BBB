"""
Tests for RevenuePredictor with mocked numpy.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock numpy BEFORE importing the module under test
# This is crucial because numpy is not installed in the environment
mock_numpy = MagicMock()
sys.modules['numpy'] = mock_numpy

# Mock missing dependencies
mock_openai = MagicMock()
sys.modules['openai'] = mock_openai
mock_requests = MagicMock()
sys.modules['requests'] = mock_requests
mock_fastapi = MagicMock()
sys.modules['fastapi'] = mock_fastapi
mock_anthropic = MagicMock()
sys.modules['anthropic'] = mock_anthropic
mock_stripe = MagicMock()
sys.modules['stripe'] = mock_stripe
mock_cryptography = MagicMock()
sys.modules['cryptography'] = mock_cryptography
mock_cryptography.fernet = MagicMock()
sys.modules['cryptography.fernet'] = mock_cryptography.fernet

# Now import the class to test
# We import from the module where RevenuePredictor is defined
from src.blank_business_builder.all_features_implementation import RevenuePredictor

class TestRevenuePredictor:
    """Test suite for RevenuePredictor."""

    @pytest.fixture
    def predictor(self):
        """Fixture for RevenuePredictor instance."""
        return RevenuePredictor()

    def test_predict_revenue_structure(self, predictor):
        """Test the structure of the prediction result."""
        async def run_test():
            # Setup mocks
            historical_data = [100.0, 110.0, 120.0]
            months_ahead = 3

            # Configure numpy mocks
            mock_numpy.arange.return_value = [0, 1, 2] # x values
            mock_numpy.array.side_effect = lambda x: x # simple pass-through for array creation

            # polyfit returns [slope, intercept]
            # Slope 10 means upward trend
            mock_numpy.polyfit.return_value = [10.0, 100.0]

            # polyval returns predicted values for future months
            # Let's say future predictions are 130, 140, 150
            mock_predictions = MagicMock()
            mock_predictions.tolist.return_value = [130.0, 140.0, 150.0]
            mock_predictions.__iter__.return_value = iter([130.0, 140.0, 150.0]) # distinct values
            mock_numpy.polyval.return_value = mock_predictions

            # Standard deviation for confidence interval
            mock_numpy.std.return_value = 5.0

            # Execute
            result = await predictor.predict_revenue(historical_data, months_ahead)

            # Verify
            assert isinstance(result, dict)
            assert "predictions" in result
            assert result["predictions"] == [130.0, 140.0, 150.0]
            assert "confidence_intervals" in result
            assert len(result["confidence_intervals"]) == 3
            assert result["trend"] == "upward" # positive slope
            assert result["growth_rate_monthly"] == 10.0
            assert "confidence_score" in result

            # Verify numpy calls
            mock_numpy.polyfit.assert_called_once()
            mock_numpy.polyval.assert_called_once()
            mock_numpy.std.assert_called_once()

        import asyncio
        asyncio.run(run_test())

    def test_predict_revenue_trend_downward(self, predictor):
        """Test downward trend detection."""
        async def run_test():
            historical_data = [100.0, 90.0, 80.0]

            # Slope -10 means downward trend
            mock_numpy.polyfit.return_value = [-10.0, 100.0]

            mock_predictions = MagicMock()
            mock_predictions.tolist.return_value = [70.0, 60.0, 50.0]
            mock_predictions.__iter__.return_value = iter([70.0, 60.0, 50.0])
            mock_numpy.polyval.return_value = mock_predictions

            result = await predictor.predict_revenue(historical_data, 3)

            assert result["trend"] == "downward"
            assert result["growth_rate_monthly"] == -10.0

        import asyncio
        asyncio.run(run_test())

    def test_predict_revenue_confidence_intervals(self, predictor):
        """Test confidence interval calculation."""
        async def run_test():
            historical_data = [100.0, 100.0, 100.0]

            # Flat trend
            mock_numpy.polyfit.return_value = [0.0, 100.0]

            mock_predictions = MagicMock()
            # Predictions are all 100
            mock_predictions.tolist.return_value = [100.0]
            mock_predictions.__iter__.return_value = iter([100.0])
            mock_numpy.polyval.return_value = mock_predictions

            # Standard deviation is 10
            # Confidence interval width should be 1.96 * 10 = 19.6
            mock_numpy.std.return_value = 10.0

            result = await predictor.predict_revenue(historical_data, 1)

            ci = result["confidence_intervals"][0]
            assert ci["prediction"] == 100.0
            assert ci["lower_bound"] == 100.0 - 19.6
            assert ci["upper_bound"] == 100.0 + 19.6

        import asyncio
        asyncio.run(run_test())

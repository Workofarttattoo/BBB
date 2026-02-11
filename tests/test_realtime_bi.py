import pytest
import asyncio
from datetime import datetime
from src.blank_business_builder.all_features_implementation import RealtimeBI

class TestRealtimeBI:
    """Test the RealtimeBI class."""

    def test_get_live_metrics(self):
        """Test getting live metrics structure and content."""
        bi = RealtimeBI()
        result = asyncio.run(bi.get_live_metrics())

        # Verify result is a dictionary
        assert isinstance(result, dict)

        # Verify timestamp
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)
        # Check if timestamp is valid ISO format
        try:
            datetime.fromisoformat(result["timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

        # Verify metrics
        assert "metrics" in result
        metrics = result["metrics"]
        assert isinstance(metrics, dict)

        # Check specific metrics keys and types
        expected_metrics_keys = {
            "active_users_now": int,
            "revenue_today": int,
            "conversions_today": int,
            "avg_response_time_ms": int,
            "server_health": float
        }

        for key, expected_type in expected_metrics_keys.items():
            assert key in metrics
            assert isinstance(metrics[key], expected_type)

        # Verify metrics values (based on current implementation)
        assert metrics["active_users_now"] == 127
        assert metrics["revenue_today"] == 12500
        assert metrics["conversions_today"] == 45
        assert metrics["avg_response_time_ms"] == 120
        assert metrics["server_health"] == 0.98

        # Verify predictions
        assert "predictions" in result
        predictions = result["predictions"]
        assert isinstance(predictions, dict)

        # Check specific predictions keys and types
        expected_predictions_keys = {
            "revenue_end_of_day": int,
            "conversions_end_of_day": int
        }

        for key, expected_type in expected_predictions_keys.items():
            assert key in predictions
            assert isinstance(predictions[key], expected_type)

        # Verify prediction values (based on current implementation)
        assert predictions["revenue_end_of_day"] == 18750
        assert predictions["conversions_end_of_day"] == 67

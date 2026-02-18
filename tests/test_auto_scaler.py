import sys
import os
import asyncio
import pytest

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.all_features_implementation import AutoScaler

class TestAutoScaler:
    """Tests for the AutoScaler class."""

    def test_scale_based_on_load_scale_up(self):
        """Test scaling up when load is high (> 0.8)."""
        scaler = AutoScaler()

        async def run_test():
            result = await scaler.scale_based_on_load(0.9)
            assert result["action"] == "scale_up"
            assert result["target_instances"] == 5
            # (5 - 3) * 50 = 100
            assert result["estimated_cost_change"] == 100

        asyncio.run(run_test())

    def test_scale_based_on_load_scale_down(self):
        """Test scaling down when load is low (< 0.3)."""
        scaler = AutoScaler()

        async def run_test():
            result = await scaler.scale_based_on_load(0.1)
            assert result["action"] == "scale_down"
            assert result["target_instances"] == 2
            # (2 - 3) * 50 = -50
            assert result["estimated_cost_change"] == -50

        asyncio.run(run_test())

    def test_scale_based_on_load_maintain(self):
        """Test maintaining instances when load is moderate."""
        scaler = AutoScaler()

        async def run_test():
            # 0.5 is between 0.3 and 0.8
            result = await scaler.scale_based_on_load(0.5)
            assert result["action"] == "maintain"
            assert result["target_instances"] == 3
            # (3 - 3) * 50 = 0
            assert result["estimated_cost_change"] == 0

        asyncio.run(run_test())

    def test_scale_based_on_load_boundary_up(self):
        """Test boundary condition for scaling up (0.8)."""
        scaler = AutoScaler()

        async def run_test():
            # 0.8 is not > 0.8, so it should maintain
            result = await scaler.scale_based_on_load(0.8)
            assert result["action"] == "maintain"
            assert result["target_instances"] == 3
            assert result["estimated_cost_change"] == 0

        asyncio.run(run_test())

    def test_scale_based_on_load_boundary_down(self):
        """Test boundary condition for scaling down (0.3)."""
        scaler = AutoScaler()

        async def run_test():
            # 0.3 is not < 0.3, so it should maintain
            result = await scaler.scale_based_on_load(0.3)
            assert result["action"] == "maintain"
            assert result["target_instances"] == 3
            assert result["estimated_cost_change"] == 0

        asyncio.run(run_test())

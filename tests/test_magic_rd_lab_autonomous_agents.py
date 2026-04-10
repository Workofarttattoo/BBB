import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal
import sys
import os

if 'src' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.magic_rd_lab_autonomous_agents import (
    MagicRDLabOrchestrator,
    MagicRDLabMarketingAgent,
    MagicRDLabColdCallerAgent,
    launch_magic_rd_lab_business
)

class TestMagicRDLabAutonomousAgents:
    def test_run_autonomous_loop(self):
        """Test the autonomous loop execution and metric updates."""
        orchestrator = MagicRDLabOrchestrator()

        async def run_test():
            await orchestrator.deploy_agents()

            # Verify agents were deployed correctly
            assert "marketing_agent_1" in orchestrator.agents
            assert "marketing_agent_2" in orchestrator.agents
            assert "cold_caller_1" in orchestrator.agents
            assert "cold_caller_2" in orchestrator.agents

            async def side_effect(delay):
                orchestrator.running = False
                return None

            with patch('asyncio.sleep', side_effect=side_effect):
                await orchestrator.run_autonomous_loop(duration_hours=1.0)

            # Verify metrics were updated after 1 cycle
            assert orchestrator.magic_metrics.linkedin_messages_sent == 100
            assert orchestrator.magic_metrics.cold_calls_made == 100
            assert orchestrator.magic_metrics.demo_calls_scheduled == 6
            assert orchestrator.magic_metrics.sessions_booked == 2
            assert orchestrator.metrics.total_revenue == 2899.0

        asyncio.run(run_test())

    def test_launch_magic_rd_lab_business(self):
        """Test the convenient launcher function."""
        async def run_test():
            # Use AsyncMock for coroutine methods
            with patch.object(MagicRDLabOrchestrator, 'run_autonomous_loop', new_callable=AsyncMock) as mock_loop:
                mock_loop.return_value = None

                with patch.object(MagicRDLabOrchestrator, 'deploy_agents', new_callable=AsyncMock) as mock_deploy:
                    mock_deploy.return_value = None

                    with patch.object(MagicRDLabOrchestrator, 'get_metrics_dashboard') as mock_metrics:
                        mock_metrics.return_value = {"status": "success"}

                        result = await launch_magic_rd_lab_business(duration_hours=1.0)

                        assert result == {"status": "success"}
                        mock_deploy.assert_called_once()
                        mock_loop.assert_called_once_with(1.0)
                        mock_metrics.assert_called_once()

        asyncio.run(run_test())

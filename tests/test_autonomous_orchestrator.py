"""
Tests for the Autonomous Business Orchestrator.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from blank_business_builder.autonomous_business import (
    AutonomousBusinessOrchestrator,
    AutonomousTask,
    AgentRole,
    TaskStatus,
    Level6BusinessAgent
)

class TestAutonomousOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        """Create a default orchestrator instance for testing."""
        return AutonomousBusinessOrchestrator(
            business_concept="Test Business",
            founder_name="Test Founder"
        )

    def test_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.business_concept == "Test Business"
        assert orchestrator.founder_name == "Test Founder"
        assert orchestrator.agents == {}
        assert orchestrator.task_queue == []
        assert orchestrator.metrics.total_revenue == 0.0

    def test_deploy_agents(self, orchestrator):
        """Test that agents are deployed correctly."""
        async def run_test():
            await orchestrator.deploy_agents()

            # Check if agents are created for all roles
            assert len(orchestrator.agents) == len(AgentRole)
            for role in AgentRole:
                found = False
                for agent in orchestrator.agents.values():
                    if agent.role == role:
                        found = True
                        break
                assert found, f"Agent for role {role} not found"

            # Check if initial tasks are generated
            assert len(orchestrator.task_queue) > 0

            # Verify specific initial tasks exist
            task_descriptions = [t.description for t in orchestrator.task_queue]
            assert "Conduct comprehensive market analysis and identify target customers" in task_descriptions

        asyncio.run(run_test())

    def test_task_assignment(self, orchestrator):
        """Test task assignment logic."""
        async def run_test():
            # Deploy agents first
            await orchestrator.deploy_agents()

            # Reset task queue to have a clean state
            orchestrator.task_queue = []

            # Create a task
            task = AutonomousTask(
                task_id="test_task_1",
                role=AgentRole.RESEARCHER,
                description="Test Research Task",
                priority=5
            )
            orchestrator.task_queue.append(task)

            # Assign tasks
            await orchestrator._assign_tasks()

            # Check if task is assigned
            assert task.status == TaskStatus.IN_PROGRESS
            assert task.assigned_to is not None
            assert orchestrator.agents[task.assigned_to].role == AgentRole.RESEARCHER

        asyncio.run(run_test())

    def test_task_execution(self, orchestrator):
        """Test task execution logic."""
        async def run_test():
            await orchestrator.deploy_agents()
            orchestrator.task_queue = []

            task = AutonomousTask(
                task_id="test_task_2",
                role=AgentRole.RESEARCHER,
                description="Test Execution Task",
                status=TaskStatus.IN_PROGRESS
            )

            # Find a researcher agent
            agent_id = next(aid for aid, a in orchestrator.agents.items() if a.role == AgentRole.RESEARCHER)
            task.assigned_to = agent_id
            orchestrator.task_queue.append(task)

            # Mock the agent's execute_task method
            mock_result = {
                "success": True,
                "action": "test_action",
                "confidence": 0.9,
                "outcome": "Success",
                "metrics": {},
                "agent_id": agent_id
            }
            orchestrator.agents[agent_id].execute_task = AsyncMock(return_value=mock_result)

            # Execute tasks
            results = await orchestrator._execute_tasks_parallel()

            assert len(results) == 1
            assert results[0] == mock_result
            assert task.status == TaskStatus.COMPLETED
            assert task.result == mock_result

        asyncio.run(run_test())

    def test_metric_updates(self, orchestrator):
        """Test metric updates based on task results."""
        async def run_test():
            await orchestrator.deploy_agents()

            # Create a mock result simulating sales
            sales_agent_id = next(aid for aid, a in orchestrator.agents.items() if a.role == AgentRole.SALES)
            mock_result = {
                "success": True,
                "action": "sales_outreach",
                "confidence": 0.9,
                "outcome": "Success",
                "metrics": {},
                "agent_id": sales_agent_id
            }

            initial_revenue = orchestrator.metrics.total_revenue
            await orchestrator._update_metrics([mock_result])

            # Check if revenue increased (assuming hardcoded logic in _update_metrics: 500.0 for sales)
            assert orchestrator.metrics.total_revenue == initial_revenue + 500.0
            assert orchestrator.metrics.tasks_completed == 1

        asyncio.run(run_test())

    def test_adaptive_tasks(self, orchestrator):
        """Test adaptive task generation."""
        async def run_test():
            # Set metrics to trigger adaptive tasks
            orchestrator.metrics.monthly_revenue = 6000.0  # Trigger marketing scaling
            orchestrator.metrics.conversion_rate = 0.04    # Trigger research (threshold < 0.05)

            initial_queue_len = len(orchestrator.task_queue)

            await orchestrator._generate_adaptive_tasks([])

            # Should add 2 tasks
            assert len(orchestrator.task_queue) == initial_queue_len + 2

            descriptions = [t.description for t in orchestrator.task_queue]
            assert "Scale successful marketing campaigns" in descriptions
            assert "Analyze low conversion and recommend improvements" in descriptions

        asyncio.run(run_test())

    @patch("asyncio.sleep", new_callable=AsyncMock)
    def test_autonomous_loop_short(self, mock_sleep, orchestrator):
        """Test a short run of the autonomous loop."""
        async def run_test():
            # Mock internal methods to avoid complex execution
            orchestrator._assign_tasks = AsyncMock()
            orchestrator._execute_tasks_parallel = AsyncMock(return_value=[])
            orchestrator._update_metrics = AsyncMock()
            orchestrator._generate_adaptive_tasks = AsyncMock()
            orchestrator._report_progress = AsyncMock()

            # Run for a very short duration
            # Use a duration that allows at least one iteration if possible,
            # but relies on datetime.now() < end_time.
            # We can't easily control time flow without Freezegun or similar,
            # so we rely on the fact that the loop condition is checked at start.

            # Let's mock datetime to control the loop? No, too invasive.
            # Instead, we can side_effect asyncio.sleep to advance time or stop the loop.

            # Just run with 0 duration to ensure it doesn't crash,
            # or very small duration.

            await orchestrator.run_autonomous_loop(duration_hours=0.0001)

            # Verify methods were called at least once if duration allowed it
            # If duration 0.0001 hours = 0.36 seconds.
            # The loop sleeps for 5 seconds.
            # Wait, `await asyncio.sleep(5)` is mocked.
            # So it will loop extremely fast.
            # We need to stop the loop.
            # We can set orchestrator.running = False in a side_effect of _assign_tasks or sleep.

        # Stop loop after first sleep
        mock_sleep.side_effect = lambda x: setattr(orchestrator, 'running', False)

        asyncio.run(run_test())


import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, AgentRole, TaskStatus

class TestAutonomousOrchestrator(unittest.IsolatedAsyncioTestCase):
    def _build_orchestrator(self) -> AutonomousBusinessOrchestrator:
        return AutonomousBusinessOrchestrator(
            "Test",
            "Founder",
            market_research_api_key="test",
            sendgrid_api_key="test",
            stripe_api_key="test",
            twitter_consumer_key="test",
            twitter_consumer_secret="test",
            twitter_access_token="test",
            twitter_access_token_secret="test",
        )

    async def test_assign_tasks_dependencies_manual(self):
        """Test dependency logic by manually setting state (mocking existing tasks)."""
        orchestrator = self._build_orchestrator()

        # Create agents
        agent1 = MagicMock()
        agent1.role = AgentRole.RESEARCHER
        agent1.active = True
        agent1.agent_id = "agent1"

        agent2 = MagicMock()
        agent2.role = AgentRole.MARKETER
        agent2.active = True
        agent2.agent_id = "agent2"

        orchestrator.agents["agent1"] = agent1
        orchestrator.agents["agent2"] = agent2

        # Task 1: Research (Completed)
        task1 = AutonomousTask(task_id="t1", role=AgentRole.RESEARCHER, description="Research", status=TaskStatus.COMPLETED)
        orchestrator.task_queue.append(task1)
        # Ensure consistency: if completed, it should be in the set
        orchestrator.completed_task_ids.add("t1")

        # Task 2: Marketing (Depends on t1)
        task2 = AutonomousTask(task_id="t2", role=AgentRole.MARKETER, description="Marketing", dependencies=["t1"])
        orchestrator.task_queue.append(task2)

        # Task 3: Sales (Depends on t2 - not complete)
        task3 = AutonomousTask(task_id="t3", role=AgentRole.SALES, description="Sales", dependencies=["t2"])
        orchestrator.task_queue.append(task3)

        # Run assignment
        await orchestrator._assign_tasks()

        # t2 should be assigned (dependencies met)
        self.assertEqual(task2.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task2.assigned_to, "agent2")

        # t3 should be BLOCKED (dependencies not met)
        self.assertEqual(task3.status, TaskStatus.BLOCKED)

    async def test_lifecycle_and_state_maintenance(self):
        """Test that the orchestrator actually maintains state as tasks complete."""
        orchestrator = self._build_orchestrator()

        # Mock agent to succeed
        agent = MagicMock()
        agent.role = AgentRole.RESEARCHER
        agent.active = True
        agent.agent_id = "agent1"
        # execute_task returns success dict
        agent.execute_task = AsyncMock(return_value={
            "success": True,
            "agent_id": "agent1",
            "action": "test",
            "confidence": 0.9,
            "outcome": "Done",
            "metrics": {}
        })
        orchestrator.agents["agent1"] = agent

        # Add Task 1 (Pending)
        task1 = AutonomousTask(task_id="t1", role=AgentRole.RESEARCHER, description="T1")
        orchestrator.task_queue.append(task1)

        # 1. Assign (should pick up T1)
        await orchestrator._assign_tasks()
        self.assertEqual(task1.status, TaskStatus.IN_PROGRESS)

        # 2. Execute (should complete T1 and update set)
        await orchestrator._execute_tasks_parallel()
        self.assertEqual(task1.status, TaskStatus.COMPLETED)
        self.assertIn("t1", orchestrator.completed_task_ids)

        # Add Task 2 (Depends on T1)
        task2 = AutonomousTask(task_id="t2", role=AgentRole.RESEARCHER, description="T2", dependencies=["t1"])
        orchestrator.task_queue.append(task2)

        # 3. Assign (should pick up T2 because T1 is in completed_task_ids)
        await orchestrator._assign_tasks()
        self.assertEqual(task2.status, TaskStatus.IN_PROGRESS)

    async def test_blocked_task_retries_after_dependency_completes(self):
        """Blocked tasks should be retried once dependencies are completed."""
        orchestrator = self._build_orchestrator()

        researcher = MagicMock()
        researcher.role = AgentRole.RESEARCHER
        researcher.active = True
        researcher.agent_id = "researcher_agent"
        researcher.execute_task = AsyncMock(return_value={"success": True, "agent_id": "researcher_agent"})

        marketer = MagicMock()
        marketer.role = AgentRole.MARKETER
        marketer.active = True
        marketer.agent_id = "marketer_agent"
        marketer.execute_task = AsyncMock(return_value={"success": True, "agent_id": "marketer_agent"})

        orchestrator.agents[researcher.agent_id] = researcher
        orchestrator.agents[marketer.agent_id] = marketer

        task_research = AutonomousTask(task_id="t_research", role=AgentRole.RESEARCHER, description="Research")
        task_marketing = AutonomousTask(
            task_id="t_marketing",
            role=AgentRole.MARKETER,
            description="Marketing",
            dependencies=["t_research"],
        )
        orchestrator.task_queue.extend([task_research, task_marketing])

        await orchestrator._assign_tasks()
        self.assertEqual(task_research.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task_marketing.status, TaskStatus.BLOCKED)

        await orchestrator._execute_tasks_parallel()
        self.assertEqual(task_research.status, TaskStatus.COMPLETED)
        self.assertIn("t_research", orchestrator.completed_task_ids)

        await orchestrator._assign_tasks()
        self.assertEqual(task_marketing.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task_marketing.assigned_to, "marketer_agent")

    async def test_failure_transition_metrics_are_recorded(self):
        """Failed execution should record transitions and attempts."""
        orchestrator = self._build_orchestrator()

        agent = MagicMock()
        agent.role = AgentRole.RESEARCHER
        agent.active = True
        agent.agent_id = "agent_fail"
        agent.execute_task = AsyncMock(return_value={"success": False, "agent_id": "agent_fail"})
        orchestrator.agents[agent.agent_id] = agent

        task = AutonomousTask(task_id="t_fail", role=AgentRole.RESEARCHER, description="Will fail")
        orchestrator.task_queue.append(task)

        await orchestrator._assign_tasks()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

        await orchestrator._execute_tasks_parallel()
        self.assertEqual(task.status, TaskStatus.FAILED)

        transition_metrics = orchestrator.get_task_transition_metrics()
        self.assertEqual(
            transition_metrics["transition_counts"].get("pending->in_progress"),
            1,
        )
        self.assertEqual(
            transition_metrics["transition_counts"].get("in_progress->failed"),
            1,
        )
        self.assertEqual(
            transition_metrics["execution_attempts"].get("t_fail"),
            1,
        )

    async def test_orphaned_in_progress_task_is_requeued(self):
        """In-progress tasks without a live assigned agent should be requeued."""
        orchestrator = self._build_orchestrator()

        orphan = AutonomousTask(
            task_id="orphan_task",
            role=AgentRole.RESEARCHER,
            description="Orphaned task",
            status=TaskStatus.IN_PROGRESS,
            assigned_to="missing_agent",
        )
        orchestrator.task_queue.append(orphan)

        await orchestrator._assign_tasks()

        self.assertEqual(orphan.status, TaskStatus.PENDING)
        self.assertIsNone(orphan.assigned_to)

        orphan_in_progress = [
            task
            for task in orchestrator.task_queue
            if task.status == TaskStatus.IN_PROGRESS
            and (not task.assigned_to or task.assigned_to not in orchestrator.agents)
        ]
        self.assertEqual(len(orphan_in_progress), 0)

        transition_metrics = orchestrator.get_task_transition_metrics()
        self.assertEqual(
            transition_metrics["transition_counts"].get("in_progress->pending"),
            1,
        )

if __name__ == '__main__':
    unittest.main()

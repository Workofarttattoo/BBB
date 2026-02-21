
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
        # We manually add to task_queue to avoid pending_tasks logic if we want to simulate already completed
        # But add_task adds to pending_tasks. If status is COMPLETED, _assign_tasks logic should handle removing it.
        # Let's use add_task for consistency, but note that add_task adds to pending.
        orchestrator.add_task(task1)
        # Ensure consistency: if completed, it should be in the set
        orchestrator.completed_task_ids.add("t1")

        # Task 2: Marketing (Depends on t1)
        task2 = AutonomousTask(task_id="t2", role=AgentRole.MARKETER, description="Marketing", dependencies=["t1"])
        orchestrator.add_task(task2)

        # Task 3: Sales (Depends on t2 - not complete)
        task3 = AutonomousTask(task_id="t3", role=AgentRole.SALES, description="Sales", dependencies=["t2"])
        orchestrator.add_task(task3)

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
        orchestrator.add_task(task1)

        # 1. Assign (should pick up T1)
        await orchestrator._assign_tasks()
        self.assertEqual(task1.status, TaskStatus.IN_PROGRESS)

        # 2. Execute (should complete T1 and update set)
        await orchestrator._execute_tasks_parallel()
        self.assertEqual(task1.status, TaskStatus.COMPLETED)
        self.assertIn("t1", orchestrator.completed_task_ids)

        # Add Task 2 (Depends on T1)
        task2 = AutonomousTask(task_id="t2", role=AgentRole.RESEARCHER, description="T2", dependencies=["t1"])
        orchestrator.add_task(task2)

        # 3. Assign (should pick up T2 because T1 is in completed_task_ids)
        await orchestrator._assign_tasks()
        self.assertEqual(task2.status, TaskStatus.IN_PROGRESS)

    async def test_resume_blocked_task(self):
        """Test that a BLOCKED task is retried and assigned once dependencies are met."""
        orchestrator = AutonomousBusinessOrchestrator("Test", "Founder")

        agent1 = MagicMock()
        agent1.role = AgentRole.RESEARCHER
        agent1.active = True
        agent1.agent_id = "agent1"
        orchestrator.agents["agent1"] = agent1

        # Task 1: Research (Will complete later)
        task1 = AutonomousTask(task_id="t1", role=AgentRole.RESEARCHER, description="T1")
        orchestrator.add_task(task1)

        # Task 2: Research (Depends on T1)
        task2 = AutonomousTask(task_id="t2", role=AgentRole.RESEARCHER, description="T2", dependencies=["t1"])
        orchestrator.add_task(task2)

        # 1. Assign - T1 goes IN_PROGRESS, T2 goes BLOCKED
        await orchestrator._assign_tasks()
        self.assertEqual(task1.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task2.status, TaskStatus.BLOCKED)

        # 2. Complete T1
        # Manually mark T1 as completed to simulate execution finishing
        task1.status = TaskStatus.COMPLETED
        orchestrator.completed_task_ids.add("t1")

        # 3. Assign again - T2 should be picked up (unblocked)
        await orchestrator._assign_tasks()
        self.assertEqual(task2.status, TaskStatus.IN_PROGRESS)

if __name__ == '__main__':
    unittest.main()

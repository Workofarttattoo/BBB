"""Tests for QuLab Hive Mind package integrated into BBB."""

from __future__ import annotations

import asyncio
import unittest

from src.blank_business_builder.hive_mind import (
    Agent,
    AgentType,
    HiveMind,
    Task,
    TaskPriority,
    create_bbb_agents,
)
from src.blank_business_builder.hive_mind_service import HiveMindService


class TestHiveMindCore(unittest.TestCase):
    def setUp(self):
        self.hive = HiveMind()

    def test_bbb_agent_registration(self):
        agents = create_bbb_agents(self.hive, include_lab_agents=False)
        self.assertEqual(len(agents), 7)
        status = self.hive.get_status()
        self.assertEqual(status["registry"]["total_agents"], 7)
        self.assertGreaterEqual(status["registry"]["by_type"].get("sales", 0), 1)

    def test_task_submission(self):
        create_bbb_agents(self.hive, include_lab_agents=False)
        task = Task(
            task_id="task-001",
            task_type="strategy",
            description="Draft Q2 OKR priorities",
            priority=TaskPriority.HIGH,
            required_capabilities=["strategy"],
            parameters={"quarter": "Q2"},
        )
        task_id = self.hive.submit_task(task)
        self.assertEqual(task_id, "task-001")
        queue = self.hive.distributor.get_queue_status()
        self.assertGreater(queue["total_pending"], 0)

    def test_knowledge_sharing(self):
        self.hive.knowledge.subscribe("agent-001", "business_discoveries")
        self.hive.knowledge.publish(
            "business_discoveries",
            {"finding": "pipeline velocity up"},
            "agent-002",
        )
        latest = self.hive.knowledge.get_latest("business_discoveries", n=1)
        self.assertEqual(len(latest), 1)
        self.assertIn("pipeline", str(latest[0]))


class TestHiveMindService(unittest.IsolatedAsyncioTestCase):
    async def test_status_and_intent(self):
        svc = HiveMindService()
        await svc.ensure_started()
        status = svc.status()
        self.assertTrue(status["started"])
        self.assertGreaterEqual(status["registry"]["total_agents"], 7)
        parsed = svc.parse_intent("Optimize marketing campaign for SaaS leads")
        self.assertIn("confidence", parsed)
        self.assertIn("experiment_type", parsed)

    async def test_submit_task_queues_without_drain(self):
        from unittest.mock import AsyncMock, patch

        svc = HiveMindService()
        await svc.ensure_started()
        with patch.object(svc, "_drain_assigned_tasks", new=AsyncMock()):
            result = await svc.submit_business_task(
                description="Write outbound email sequence",
                role_capability="outbound",
            )
        self.assertEqual(result["status"], "submitted")
        self.assertIn("task_id", result)


if __name__ == "__main__":
    unittest.main()

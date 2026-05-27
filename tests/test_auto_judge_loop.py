"""Tests for auto-judge loop and role model router."""

import pytest

from src.blank_business_builder.autonomous_business import (
    AgentRole,
    AutonomousBusinessOrchestrator,
    AutonomousTask,
    TaskStatus,
)
from src.blank_business_builder.auto_judge_loop import AutoJudgeLoop, MAX_JUDGE_REVISE_ATTEMPTS
from src.blank_business_builder.judge_service import JudgeService, JudgeVerdict
from src.blank_business_builder.local_model_client import RoleModelRouter
from src.blank_business_builder.task_locks import TaskLockStore


def test_role_model_router_tiers():
    router = RoleModelRouter()
    assert router.tier_for_role("sales") == "flash_worker"
    assert router.tier_for_role("executive") == "csuite"
    assert router.tier_for_role("judge-sales") == "judge"


def test_task_lock_exclusive(tmp_path):
    store = TaskLockStore(lock_dir=tmp_path)
    assert store.acquire("issue-1", "agent-a") is True
    assert store.acquire("issue-1", "agent-b") is False
    assert store.release("issue-1", "agent-a") is True
    assert store.acquire("issue-1", "agent-b") is True


@pytest.mark.asyncio
async def test_auto_judge_revise_requeues():
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="tester",
    )
    task = AutonomousTask(
        task_id="t-revise",
        role=AgentRole.SALES,
        description="Find leads",
        status=TaskStatus.IN_PROGRESS,
    )
    orch.add_task(task)
    orch._set_task_status(task, TaskStatus.IN_PROGRESS)

    class StubJudge:
        async def evaluate(self, **kwargs):
            from src.blank_business_builder.judge_service import JudgeResult

            return JudgeResult(
                verdict=JudgeVerdict.REVISE,
                score=0.4,
                fixes=["Add real URLs"],
                reasoning="stub",
                policy_flags=[],
            )

    loop = AutoJudgeLoop(
        "SaaS Micro-Tools Empire",
        orch,
        judge=StubJudge(),
        max_revise=MAX_JUDGE_REVISE_ATTEMPTS,
    )
    result = await loop.evaluate_worker_result(
        task,
        {
            "success": True,
            "artifact_type": "lead_batch",
            "content": "",
            "metadata": {"lead_count": 0},
        },
    )
    assert result.get("requeued_for_revise") is True
    assert task.status == TaskStatus.PENDING

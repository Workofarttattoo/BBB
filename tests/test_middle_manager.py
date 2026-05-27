"""Tests for Middle Manager state collection and Judge deterministic checks."""

import pytest

from src.blank_business_builder.autonomous_business import (
    AgentRole,
    AutonomousBusinessOrchestrator,
    AutonomousTask,
    TaskStatus,
)
from src.blank_business_builder.judge_service import JudgeService, JudgeVerdict
from src.blank_business_builder.middle_manager_state import collect_middle_manager_state
from src.blank_business_builder.milestone_parliament import MilestonePack, MilestoneParliamentGate


def test_collect_state_detects_blocked_tasks():
    orch = AutonomousBusinessOrchestrator(
        business_concept="Test Business",
        founder_name="tester",
    )
    orch.add_task(
        AutonomousTask(
            task_id="t-blocked",
            role=AgentRole.SALES,
            description="Follow up leads",
            status=TaskStatus.BLOCKED,
        )
    )
    state = collect_middle_manager_state(orch)
    assert state.task_counts.get("blocked") == 1
    assert any("blocked" in hint for hint in state.loose_end_hints)


def test_judge_deterministic_empty_lead_batch():
    svc = JudgeService(client=None)
    result = svc._deterministic_checks("lead_batch", "", {"lead_count": 0})
    assert result.verdict == JudgeVerdict.REVISE
    assert result.score == 0.0


def test_judge_escalates_email_with_approval_flag():
    svc = JudgeService(client=None)
    result = svc._deterministic_checks(
        "email_draft",
        "Hello prospect, we would love to connect.",
        {"requires_approval": True},
    )
    assert result.verdict == JudgeVerdict.ESCALATE


@pytest.mark.asyncio
async def test_milestone_parliament_rejects_low_score():
    gate = MilestoneParliamentGate(
        judge=JudgeService(client=None),
        approval_threshold=0.85,
    )
    pack = MilestonePack(
        milestone_id="m1",
        business_name="Test Business",
        title="Lead ingest",
        summary="",
        artifact_type="milestone_pack",
        content="",
    )
    decision = await gate.review(pack, mission="Ship leads safely")
    assert decision.parliament_status == "NEEDS_REFINEMENT"

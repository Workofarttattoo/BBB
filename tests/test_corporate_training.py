"""Corporate training and agent lifecycle tests."""

from src.blank_business_builder.agent_lifecycle import (
    AgentLifecycleManager,
    AgentLifecycleState,
    ShiftHandoff,
)
from src.blank_business_builder.corporate_training import CorporateTrainingPipeline


def test_corporate_export_has_seeds():
    pipeline = CorporateTrainingPipeline("SaaS Micro-Tools Empire")
    sft = pipeline.export_unified_sft()
    assert sft.is_file()
    lines = [ln for ln in sft.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 10


def test_role_instance_prompt_includes_role_skill():
    pipeline = CorporateTrainingPipeline("SaaS Micro-Tools Empire")
    prompt = pipeline.role_instance_prompt("sales")
    assert "Role: sales" in prompt
    assert "Lead gen" in prompt or "sales" in prompt.lower()


def test_agent_lifecycle_shift_and_sleep(tmp_path):
    mgr = AgentLifecycleManager(base_dir=tmp_path)
    assert mgr.accepts_tasks("agent-1") is False
    mgr.start_shift("agent-1", "sales", "day-us")
    assert mgr.accepts_tasks("agent-1") is True
    mgr.end_shift(
        "agent-1",
        "sales",
        "day-us",
        ShiftHandoff(
            role="sales",
            shift_id="day-us",
            agent_id="agent-1",
            open_tasks=["t1"],
        ),
    )
    assert mgr.get_state("agent-1") == AgentLifecycleState.SLEEPING
    assert mgr.accepts_tasks("agent-1") is False


def test_dream_consolidation(tmp_path):
    mgr = AgentLifecycleManager(base_dir=tmp_path)
    mgr.start_shift("agent-2", "support", "night")
    mgr.end_shift(
        "agent-2",
        "support",
        "night",
        ShiftHandoff(role="support", shift_id="night", agent_id="agent-2"),
    )
    record = mgr.consolidate_shift_logs(
        "agent-2",
        "support",
        "night",
        ["judge pass on ticket reply", "revise: missing empathy"],
    )
    assert record.learnings or record.mistakes_to_avoid
    assert mgr.get_state("agent-2") == AgentLifecycleState.OFF_DUTY

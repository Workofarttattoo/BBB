"""Paperclip planner/worker label and lock tests."""

import pytest

from src.blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator
from src.blank_business_builder.paperclip_work_source import (
    PaperclipIssuePayload,
    PaperclipWorkSourceSync,
)


@pytest.fixture
def sync_with_isolated_locks(tmp_path, monkeypatch):
    monkeypatch.setenv("BBB_TASK_LOCK_DIR", str(tmp_path))
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="tester",
    )
    return PaperclipWorkSourceSync(orch)


def test_planner_issue_skipped(sync_with_isolated_locks):
    sync = sync_with_isolated_locks
    issue = PaperclipIssuePayload(
        issue_id="plan-1",
        title="Break down Q2 launch",
        labels=["plan:decompose"],
    )
    assert sync.is_planner_issue(issue) is True
    result = sync.upsert_issue(issue)
    assert result["synced"] is False
    assert result["reason"] == "planner_issue"


def test_execute_issue_acquires_lock(sync_with_isolated_locks):
    sync = sync_with_isolated_locks
    issue = PaperclipIssuePayload(
        issue_id="exec-1",
        title="Run lead hunt",
        labels=["bbb:execute", "role:sales"],
        assignee_agent_id="sales-agent-1",
    )
    r1 = sync.upsert_issue(issue)
    assert r1["synced"] is True
    issue2 = PaperclipIssuePayload(
        issue_id="exec-1",
        title="Run lead hunt",
        labels=["bbb:execute"],
        assignee_agent_id="other-agent",
    )
    r2 = sync.upsert_issue(issue2)
    assert r2["synced"] is False
    assert r2["reason"] == "issue_locked"

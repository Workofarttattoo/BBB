"""Tests for enterprise agent policy, approvals, and Paperclip work sync."""

import pytest

from src.blank_business_builder.approval_gates import (
    ApprovalGateError,
    ApprovalStatus,
    ApprovalStore,
    GateAction,
    assert_approved_or_raise,
)
from src.blank_business_builder.enterprise_agent_policy import (
    AutomationMode,
    Capability,
    resolve_business_policy,
)
from src.blank_business_builder.autonomous_business import (
    AutonomousBusinessOrchestrator,
)
from src.blank_business_builder.paperclip_work_source import PaperclipIssuePayload
from src.blank_business_builder.lead_huntress import LeadHuntress


def test_saas_template_has_capability_overrides():
    policy = resolve_business_policy("SaaS Micro-Tools Empire")
    marketer = policy.policy_for_role("marketer")
    assert marketer.mode_for(Capability.EMAIL_CAMPAIGN) == AutomationMode.APPROVAL_REQUIRED
    sales = policy.policy_for_role("sales")
    assert sales.mode_for(Capability.APOLLO_SEARCH) == AutomationMode.MANUAL


def test_required_roles_not_twelve_role_fallback():
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="test",
    )
    assert len(orch.required_roles) <= 8
    assert any(r.value == "saas_builder" for r in orch.required_roles)


def test_approval_gate_blocks_without_approval():
    with pytest.raises(ApprovalGateError) as exc:
        assert_approved_or_raise(
            GateAction.EMAIL_SEND,
            "SaaS Micro-Tools Empire",
            "sales",
        )
    assert exc.value.approval_id


def test_approval_gate_allows_after_resolve():
    with pytest.raises(ApprovalGateError) as exc:
        assert_approved_or_raise(
            GateAction.EMAIL_SEND,
            "SaaS Micro-Tools Empire",
            "sales",
        )
    aid = exc.value.approval_id
    ApprovalStore.resolve(aid, ApprovalStatus.APPROVED)
    assert_approved_or_raise(
        GateAction.EMAIL_SEND,
        "SaaS Micro-Tools Empire",
        "sales",
        approval_id=aid,
    )


def test_paperclip_human_apollo_skipped():
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="test",
    )
    payload = PaperclipIssuePayload(
        issue_id="issue-1",
        title="Run Apollo manually",
        labels=["human:apollo"],
    )
    assert orch.paperclip_sync.should_skip_autonomous_task(payload)
    result = orch.paperclip_sync.upsert_issue(payload)
    assert result["synced"] is False


def test_paperclip_bbb_execute_synced():
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="test",
    )
    result = orch.paperclip_sync.upsert_issue(
        PaperclipIssuePayload(
            issue_id="issue-2",
            identifier="BBB-2",
            title="Draft outreach",
            labels=["bbb:execute", "role:sales"],
            status="todo",
        )
    )
    assert result["synced"] is True
    assert any(t.task_id.startswith("pc-") for t in orch.task_queue)


def test_lead_huntress_agent_path_blocks_manual_only_apollo():
    orch = AutonomousBusinessOrchestrator(
        business_concept="SaaS Micro-Tools Empire",
        founder_name="test",
    )
    huntress = LeadHuntress(orch, business_name="SaaS Micro-Tools Empire")
    with pytest.raises(ApprovalGateError):
        huntress.find_leads_agent("cto fintech", count=3)

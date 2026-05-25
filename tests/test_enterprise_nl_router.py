"""Tests for natural-language enterprise command routing."""

from src.blank_business_builder.enterprise_nl_router import parse_intent
from src.blank_business_builder.autonomous_business import AgentRole


def test_parse_help():
    intent = parse_intent("what can you do?", "SaaS Micro-Tools Empire")
    assert intent.name == "help"


def test_parse_pending_approvals():
    intent = parse_intent("what needs my approval?", "SaaS Micro-Tools Empire")
    assert intent.name == "list_approvals"


def test_parse_approve_latest():
    intent = parse_intent("approve the latest request", "SaaS Micro-Tools Empire")
    assert intent.name == "resolve_approval"
    assert intent.params["status"] == "approved"


def test_parse_find_leads_manual():
    intent = parse_intent("find 10 SaaS founders in the US", "SaaS Micro-Tools Empire")
    assert intent.name == "find_leads"
    assert intent.params["mode"] == "manual"
    assert intent.params["count"] == 10


def test_parse_ceo_task():
    intent = parse_intent(
        "CEO: analyze why sales pipeline stalled this week",
        "SaaS Micro-Tools Empire",
    )
    assert intent.name == "assign_task"
    assert intent.params["role"] == AgentRole.EXECUTIVE
    assert "pipeline" in intent.params["description"].lower()


def test_parse_tell_marketing():
    intent = parse_intent(
        "Tell marketing to draft a launch email for the new tool",
        "SaaS Micro-Tools Empire",
    )
    assert intent.name == "assign_task"
    assert intent.params["role"] == AgentRole.MARKETER

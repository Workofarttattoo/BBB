"""Tests for company pack loader."""

from src.blank_business_builder.company_pack import (
    load_role_skill,
    load_skills_index,
    slug_for_business,
    judge_domain_for_artifact,
    load_eval_jsonl,
)


def test_slug_for_business():
    assert slug_for_business("SaaS Micro-Tools Empire") == "saas-micro-tools"


def test_load_skills_index():
    idx = load_skills_index("SaaS Micro-Tools Empire")
    assert "sales/SKILL.md" in idx


def test_load_role_skill_sales():
    skill = load_role_skill("SaaS Micro-Tools Empire", "sales")
    assert "Lead quality bar" in skill


def test_judge_domain_mapping():
    assert judge_domain_for_artifact("lead_batch") == "sales"
    assert judge_domain_for_artifact("campaign_draft") == "content"


def test_eval_jsonl_loads():
    rows = load_eval_jsonl("SaaS Micro-Tools Empire", "judge-sales.jsonl")
    assert len(rows) >= 1
    assert rows[0].get("verdict") in ("pass", "revise", "escalate")

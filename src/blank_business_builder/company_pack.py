"""
Company pack loader — Viktor-style lazy skills and eval datasets.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
COMPANIES_ROOT = BBB_ROOT / "companies"

BUSINESS_SLUG_MAP = {
    "saas micro-tools empire": "saas-micro-tools",
    "saas-micro-tools": "saas-micro-tools",
}


def slug_for_business(business_name: str) -> str:
    key = (business_name or "").strip().lower()
    return BUSINESS_SLUG_MAP.get(key, "saas-micro-tools")


def company_root(business_name: str) -> Path:
    return COMPANIES_ROOT / slug_for_business(business_name)


@lru_cache(maxsize=8)
def load_skills_index(business_name: str) -> str:
    path = company_root(business_name) / "skills" / "_index.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def load_skill(business_name: str, relative_path: str) -> str:
    """Load a skill file relative to skills/ (e.g. sales/SKILL.md)."""
    rel = relative_path.lstrip("/")
    path = company_root(business_name) / "skills" / rel
    if not path.is_file():
        logger.warning("Skill not found: %s", path)
        return ""
    return path.read_text(encoding="utf-8")


def load_role_skill(business_name: str, role: str) -> str:
    """Primary SKILL.md for a worker role."""
    role_key = role.lower().replace(" ", "_")
    content = load_skill(business_name, f"{role_key}/SKILL.md")
    if content:
        return content
    return load_skill(business_name, f"{role}/SKILL.md")


def load_judge_skill(business_name: str, domain: str) -> str:
    return load_skill(business_name, f"judge-{domain}/SKILL.md")


def load_company_md(business_name: str) -> str:
    path = company_root(business_name) / "COMPANY.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def load_eval_jsonl(business_name: str, name: str, limit: int = 20) -> List[Dict[str, Any]]:
    path = company_root(business_name) / "eval" / name
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(rows) >= limit:
            break
    return rows


def judge_domain_for_artifact(artifact_type: str) -> str:
    if artifact_type in ("lead_batch", "email_draft") or artifact_type.startswith("sales"):
        return "sales"
    if artifact_type in ("content_draft", "campaign_draft") or "content" in artifact_type:
        return "content"
    if artifact_type in ("code_diff", "sandbox_result") or "code" in artifact_type:
        return "code"
    return "sales"

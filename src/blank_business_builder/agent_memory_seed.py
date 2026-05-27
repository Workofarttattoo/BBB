"""
Default semantic memory seeds for BBB company workspaces.

Run via scripts/bbb-seed-agent-memory.py or ensure_seeded() on first Viktor run.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from .agent_memory import AgentMemoryStore
from .config import settings

logger = logging.getLogger(__name__)

# workspace slug -> list of (key, content)
SEMANTIC_SEEDS: Dict[str, List[Tuple[str, str]]] = {
    "saas-micro-tools": [
        (
            "company_mission",
            "SaaS Micro-Tools Empire: ship focused micro-SaaS tools ($9–49/mo), content-led acquisition, minimal human support.",
        ),
        (
            "company_slug",
            "Active company pack slug is saas-micro-tools; skills live under companies/saas-micro-tools/skills/.",
        ),
        (
            "icp",
            "ICP: solo founders and small teams (2–20), B2B productivity/dev tools, US/EU English-first.",
        ),
        (
            "governance_outbound",
            "Outbound email and bulk CRM ingest require CEO approval — never send or ingest without approval record.",
        ),
        (
            "governance_apollo",
            "Apollo search is manual in GUI; agent may draft lead batches only, not auto-run Apollo API searches.",
        ),
        (
            "governance_judge",
            "Lead batches must pass judge-sales before CRM ingest.",
        ),
        (
            "slack_sales",
            f"Sales Slack channel env: SLACK_CHANNEL_SALES={settings.SLACK_CHANNEL_SALES or '(unset)'}",
        ),
        (
            "slack_marketing",
            f"Marketing Slack channel env: SLACK_CHANNEL_MARKETING={settings.SLACK_CHANNEL_MARKETING or '(unset)'}",
        ),
        (
            "slack_ops",
            f"Ops Slack channel env: SLACK_CHANNEL_OPS={settings.SLACK_CHANNEL_OPS or '(unset)'}",
        ),
        (
            "slack_exec",
            f"Exec Slack channel env: SLACK_CHANNEL_EXEC={settings.SLACK_CHANNEL_EXEC or '(unset)'}",
        ),
        (
            "viktor_execution",
            "Viktor mode: execute first, report assumptions after; two retries before escalate; no mid-task clarification.",
        ),
        (
            "sandbox_verify",
            "Code changes: use agent sandbox + scripts/agent-verify.sh --fast before PR.",
        ),
        (
            "paperclip_labels",
            "Paperclip: plan:* tasks are planner-only; bbb:execute tasks are workers; respect task locks.",
        ),
        (
            "arxiv_pipeline",
            "Morning arXiv job: fetch cs.AI/cs.LG/cs.SE recent papers, extract invention angles, append patent queue summary to exec channel.",
        ),
        (
            "default_models",
            f"Role tiers: worker={settings.ROLE_WORKER_MODEL}, judge={settings.JUDGE_MODEL}, csuite={settings.ROLE_CSUITE_MODEL}",
        ),
    ],
    "ech0": [
        (
            "echo_identity",
            "Echo is the autonomous business orchestrator for BBB; uses Viktor protocol council when VIKTOR_MODE_ENABLED.",
        ),
        (
            "echo_workspace",
            "Echo chat workspace slug is ech0; shares semantic memory DB with company workspace when configured.",
        ),
    ],
}


def seed_workspace(
    store: AgentMemoryStore,
    workspace: str,
    *,
    overwrite: bool = False,
) -> int:
    """Upsert semantic facts for a workspace. Returns count written."""
    entries = SEMANTIC_SEEDS.get(workspace, [])
    if not entries:
        logger.warning("No semantic seeds defined for workspace %s", workspace)
        return 0
    written = 0
    with store._connect() as conn:
        for key, content in entries:
            if not overwrite:
                row = conn.execute(
                    "SELECT 1 FROM semantic_memory WHERE workspace=? AND key=?",
                    (workspace, key),
                ).fetchone()
                if row:
                    continue
            store.upsert_semantic(workspace, key, content)
            written += 1
    logger.info("Seeded %s semantic keys for workspace %s", written, workspace)
    return written


def ensure_seeded(
    store: AgentMemoryStore | None = None,
    workspaces: List[str] | None = None,
) -> Dict[str, int]:
    """Idempotent seed for default workspaces (company + echo)."""
    store = store or AgentMemoryStore()
    targets = workspaces or ["saas-micro-tools", "ech0"]
    return {ws: seed_workspace(store, ws, overwrite=False) for ws in targets}

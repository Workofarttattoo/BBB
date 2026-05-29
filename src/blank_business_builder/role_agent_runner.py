"""
Role agent runner — lazy skills, policy inject, task execution.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .company_pack import load_company_md, load_role_skill, load_skills_index
from .config import settings
from .enterprise_agent_policy import policy_for_role
from .local_model_client import LocalModelClient, RoleModelRouter
from .agent_ops_state import (
    is_viktor_mode_enabled,
    is_viktor_oracle_enabled,
    is_viktor_strategist_enabled,
)

logger = logging.getLogger(__name__)


@dataclass
class RoleRunContext:
    business_name: str
    role: str
    task_id: str
    description: str
    skills_loaded: List[str] = field(default_factory=list)


class RoleAgentRunner:
    """Viktor-style runner: index in prompt, load SKILL on demand, execute with tiered model."""

    def __init__(
        self,
        business_name: str,
        *,
        client: Optional[LocalModelClient] = None,
        router: Optional[RoleModelRouter] = None,
    ):
        self.business_name = business_name
        self.router = router or RoleModelRouter()
        self.client = client or self.router.for_role("sales")

    def build_system_prompt(self, role: str, extra_skills: Optional[List[str]] = None) -> str:
        parts = [
            load_company_md(self.business_name),
            "\n## Skills index (lazy — read full files when needed)\n",
            load_skills_index(self.business_name),
            "\n## Role policy\n",
            json.dumps(policy_for_role(role), indent=2),
        ]
        role_skill = load_role_skill(self.business_name, role)
        if role_skill:
            parts.extend(["\n## Active role skill\n", role_skill])
        from .company_pack import load_skill

        agent_ops = load_skill(self.business_name, "agent-ops/SKILL.md")
        if agent_ops:
            parts.extend(["\n## Agent ops (shifts, sleep, dream)\n", agent_ops])
        if is_viktor_mode_enabled():
            viktor = load_skill(self.business_name, "viktor-mode/SKILL.md")
            if viktor:
                parts.extend(["\n## Viktor execution mode\n", viktor])
        for rel in extra_skills or []:
            content = load_skill(self.business_name, rel)
            if content:
                parts.extend([f"\n## Skill: {rel}\n", content])
        return "\n".join(p for p in parts if p)

    async def run_task(
        self,
        *,
        role: str,
        task_id: str,
        description: str,
        integration_skills: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if agent_id:
            from .agent_lifecycle import AgentLifecycleManager

            lifecycle = AgentLifecycleManager()
            if not lifecycle.accepts_tasks(agent_id):
                return {
                    "success": False,
                    "artifact_type": "lifecycle_block",
                    "content": "",
                    "metadata": {
                        "error": "agent_not_on_shift",
                        "state": lifecycle.get_state(agent_id).value,
                    },
                }
        ctx = RoleRunContext(
            business_name=self.business_name,
            role=role,
            task_id=task_id,
            description=description,
        )
        client = self.router.for_role(role)
        system = self.build_system_prompt(role, integration_skills)
        if is_viktor_mode_enabled():
            try:
                from .agent_memory import AgentMemoryStore
                from .protocol_council import ProtocolCouncil

                async def generate(prompt: str, sys: Optional[str] = None) -> str:
                    return await client.generate(prompt, system_prompt=sys or system)

                council = ProtocolCouncil(
                    generate,
                    memory=AgentMemoryStore(),
                    workspace=self.business_name,
                    enable_strategist=is_viktor_strategist_enabled(),
                    enable_oracle=is_viktor_oracle_enabled(),
                )
                result = await council.run_task(
                    description,
                    system_context=system,
                    agent_id=agent_id or role,
                    task_id=task_id,
                )
                return {
                    "success": result.success,
                    "task_id": task_id,
                    "role": role,
                    "artifact_type": f"{role}_viktor_output",
                    "content": result.output,
                    "metadata": {
                        "assumptions": result.assumptions,
                        "steps": len(result.steps),
                        **result.metadata,
                    },
                    "summary": result.output[:500],
                    "runner": "protocol_council",
                    "model_tier": self.router.tier_for_role(role),
                }
            except Exception as exc:
                logger.warning("Viktor council failed, falling back: %s", exc)

        prompt = (
            f"Task ID: {task_id}\n"
            f"Role: {role}\n\n"
            f"Description:\n{description}\n\n"
            "Produce a structured artifact JSON with keys: "
            "artifact_type, content, metadata, summary."
        )
        try:
            raw = await client.generate(prompt, system_prompt=system)
            artifact = self._parse_artifact(raw, role, task_id)
            artifact["runner"] = "role_agent_runner"
            artifact["model_tier"] = self.router.tier_for_role(role)
            return artifact
        except Exception as exc:
            logger.warning("RoleAgentRunner LLM failed, using stub: %s", exc)
            return self._stub_artifact(role, task_id, description, str(exc))

    def _parse_artifact(self, raw: str, role: str, task_id: str) -> Dict[str, Any]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
                return {
                    "success": True,
                    "task_id": task_id,
                    "role": role,
                    "artifact_type": data.get("artifact_type", f"{role}_output"),
                    "content": data.get("content", raw),
                    "metadata": data.get("metadata", {}),
                    "summary": data.get("summary", ""),
                }
            except json.JSONDecodeError:
                pass
        artifact_type = "lead_batch" if role == "sales" else f"{role}_draft"
        return {
            "success": True,
            "task_id": task_id,
            "role": role,
            "artifact_type": artifact_type,
            "content": raw,
            "metadata": {},
            "summary": raw[:500],
        }

    def _stub_artifact(
        self, role: str, task_id: str, description: str, error: str
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "task_id": task_id,
            "role": role,
            "artifact_type": f"{role}_draft",
            "content": json.dumps({"description": description, "status": "stub", "error": error}),
            "metadata": {"stub": True},
            "summary": description[:300],
        }

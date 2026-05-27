"""
ECH0 + BBB Viktor-mode runner — proactive employee behavior.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .agent_memory import AgentMemoryStore
from .agent_ops_state import is_viktor_oracle_enabled, is_viktor_strategist_enabled
from .config import settings
from .local_model_client import RoleModelRouter
from .protocol_council import ProtocolCouncil

logger = logging.getLogger(__name__)

VIKTOR_ECHO_SYSTEM = """
You are Echo — autonomous business operator for BBB / SaaS Micro-Tools Empire.
You behave like a senior employee: proactive, accountable, assume-forward execution.
Use retrieved memory and company skills. Never stall on clarification questions.
"""


class EchoViktorRunner:
    """Wire ProtocolCouncil to local Ollama/LM Studio or ECH0 LLM engine."""

    def __init__(
        self,
        *,
        workspace: str = "ech0",
        business_name: str = "SaaS Micro-Tools Empire",
        memory: Optional[AgentMemoryStore] = None,
    ):
        self.workspace = workspace
        self.business_name = business_name
        self.memory = memory or AgentMemoryStore()
        self.router = RoleModelRouter()
        self._client = self.router.for_csuite()

    async def _generate(self, prompt: str, system: Optional[str] = None) -> str:
        ctx = "\n\n".join(p for p in (VIKTOR_ECHO_SYSTEM, system or "") if p)
        return await self._client.generate(prompt, system_prompt=ctx)

    def council(self) -> ProtocolCouncil:
        return ProtocolCouncil(
            self._generate,
            memory=self.memory,
            workspace=self.workspace,
            enable_strategist=is_viktor_strategist_enabled(),
            enable_oracle=is_viktor_oracle_enabled(),
        )

    async def handle(self, message: str, *, agent_id: str = "echo", task_id: str = "") -> str:
        from .company_pack import load_company_md, load_skills_index
        from .role_agent_runner import RoleAgentRunner

        runner = RoleAgentRunner(self.business_name, router=self.router)
        role_context = runner.build_system_prompt("executive")
        company = load_company_md(self.business_name) or ""
        index = load_skills_index(self.business_name) or ""
        system_context = f"{company}\n{index}\n{role_context}"

        result = await self.council().run_task(
            message,
            system_context=system_context,
            agent_id=agent_id,
            task_id=task_id or "ech0-chat",
        )
        return result.output

    async def handle_structured(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        from .role_agent_runner import RoleAgentRunner

        runner = RoleAgentRunner(self.business_name, router=self.router)
        system_context = runner.build_system_prompt("executive")
        result = await self.council().run_task(
            message, system_context=system_context, **kwargs
        )
        return {
            "success": result.success,
            "output": result.output,
            "assumptions": result.assumptions,
            "steps": result.steps,
            "reflections": result.reflections,
            "related_notices": result.related_notices,
            "metadata": result.metadata,
        }

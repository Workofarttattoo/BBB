"""
Protocol council — Crystalline Intent, Parliament+Tensor+Cascade strategist, Viktor execute.

Internal preprocessing only: never asks the user for clarification mid-pipeline.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .agent_memory import AgentMemoryStore
from .viktor_execution import (
    PreparedMission,
    ViktorExecutor,
    ViktorRunResult,
    needs_strategist_pass,
    score_ambiguity,
)

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str, Optional[str]], Awaitable[str]]

CRYSTALLINE_INTENT_SYSTEM = """
You are the Crystalline Intent agent (⟡). INTERNAL ONLY — output for other agents, not the user.
Never ask questions. Crystallize vague requests into executable missions.

Output JSON:
{
  "core_intent": "2-3 sentences, absolute clarity",
  "constraints": ["will NOT do X", ...],
  "success_criteria": ["measurable outcomes"],
  "assumptions": ["interpretation choices made"],
  "confidence": 0.0-1.0
}
"""

STRATEGIST_SYSTEM = """
You are the Strategist agent combining:
- Echo Parliament (◎): Progressives, Conservatives, Pragmatists, Visionaries, Skeptics — brief votes
- Semantic Tensor (⊗): 5-axis map of key concepts [complexity, abstraction, temporality, certainty, connectivity] 0-100
- Echo Cascade (◈): surface → structural insight in 3 layers max

INTERNAL ONLY. Never ask the user questions. Output JSON:
{
  "parliament_consensus": "strong|moderate|weak",
  "consensus_score": -10 to 10,
  "tensor_insights": ["..."],
  "cascade_insight": "deepest structural truth in 2 sentences",
  "recommended_path": "ordered steps for executor",
  "risks": ["..."],
  "dissent": "one sentence from skeptics"
}
"""

PREDICTION_ORACLE_SYSTEM = """
You are Prediction Oracle — INTERNAL. For planning tasks only.
Output JSON: {"branches": [{"name","probability","preparation"}], "robust_strategy": "..."}
Max 3 branches. No user questions.
"""


class ProtocolCouncil:
    """
    Multi-agent prompt stack:
    1. Crystalline Intent — sharpen goals
    2. Strategist (Parliament + Semantic Tensor + Echo Cascade) — plot ahead
    3. Optional Prediction Oracle — scenario prep
    4. Viktor Executor — assume-forward ReAct
    """

    def __init__(
        self,
        generate: GenerateFn,
        *,
        memory: Optional[AgentMemoryStore] = None,
        workspace: str = "default",
        enable_strategist: bool = True,
        enable_oracle: bool = True,
    ):
        self.generate = generate
        self.memory = memory or AgentMemoryStore()
        self.workspace = workspace
        self.enable_strategist = enable_strategist
        self.enable_oracle = enable_oracle
        self.executor = ViktorExecutor(generate)
        from .agent_memory_seed import ensure_seeded

        ensure_seeded(self.memory, workspaces=[workspace, "ech0"])

    async def run_task(
        self,
        raw_request: str,
        *,
        system_context: str = "",
        agent_id: str = "echo",
        task_id: str = "",
        tool_runner=None,
    ) -> ViktorRunResult:
        memory_block = self.memory.context_block(self.workspace, raw_request)
        full_context = "\n\n".join(p for p in (system_context, memory_block) if p.strip())

        mission = await self._crystallize(raw_request, full_context)
        mission.ambiguity_score = score_ambiguity(raw_request)

        if self.enable_strategist and needs_strategist_pass(raw_request):
            mission.strategist_brief = await self._strategist_pass(mission, full_context)
            if self.enable_oracle:
                oracle = await self._oracle_pass(mission, full_context)
                mission.strategist_brief += f"\n\n## Prediction Oracle\n{oracle}"

        result = await self.executor.run(mission, system_context=full_context, tool_runner=tool_runner)

        report = self._format_report(mission, result)
        self.memory.write_episode(
            self.workspace,
            summary=report[:2000],
            agent_id=agent_id,
            task_id=task_id,
            assumptions=result.assumptions,
            outcome="success" if result.success else "partial",
        )
        result.output = report
        return result

    async def _crystallize(self, raw_request: str, context: str) -> PreparedMission:
        prompt = f"Raw request:\n{raw_request}\n\nContext:\n{context[:3000]}"
        raw = await self.generate(prompt, CRYSTALLINE_INTENT_SYSTEM)
        data = self._parse_json(raw)
        return PreparedMission(
            raw_request=raw_request,
            crystallized_intent=data.get("core_intent") or raw_request,
            constraints=list(data.get("constraints") or []),
            assumptions=list(data.get("assumptions") or []),
        )

    async def _strategist_pass(self, mission: PreparedMission, context: str) -> str:
        prompt = (
            f"Mission:\n{mission.crystallized_intent}\n"
            f"Constraints:\n{mission.constraints}\n"
            f"Context snippet:\n{context[:2000]}"
        )
        raw = await self.generate(prompt, STRATEGIST_SYSTEM)
        data = self._parse_json(raw)
        lines = [
            "## Strategist brief (Parliament + Tensor + Cascade)",
            f"Consensus: {data.get('parliament_consensus')} ({data.get('consensus_score')})",
            f"Path: {data.get('recommended_path', '')}",
            f"Cascade: {data.get('cascade_insight', '')}",
        ]
        for ins in data.get("tensor_insights") or []:
            lines.append(f"- Tensor: {ins}")
        for risk in data.get("risks") or []:
            lines.append(f"- Risk: {risk}")
        if data.get("dissent"):
            lines.append(f"- Dissent: {data['dissent']}")
        return "\n".join(lines)

    async def _oracle_pass(self, mission: PreparedMission, context: str) -> str:
        prompt = f"Mission:\n{mission.crystallized_intent}\nContext:\n{context[:1500]}"
        raw = await self.generate(prompt, PREDICTION_ORACLE_SYSTEM)
        data = self._parse_json(raw)
        parts = [f"Robust strategy: {data.get('robust_strategy', '')}"]
        for b in (data.get("branches") or [])[:3]:
            parts.append(f"- {b.get('name')} ({b.get('probability')}): {b.get('preparation')}")
        return "\n".join(parts)

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {}

    @staticmethod
    def _format_report(mission: PreparedMission, result: ViktorRunResult) -> str:
        lines = [
            "## Done",
            result.output if isinstance(result.output, str) else str(result.output),
            "",
            "### Assumptions (Viktor — reported after execution)",
        ]
        for a in result.assumptions[:8]:
            lines.append(f"- {a}")
        if result.related_notices:
            lines.append("\n### Related notices")
            for n in result.related_notices:
                lines.append(f"- {n}")
        if mission.strategist_brief:
            lines.append("\n### Strategist (internal)")
            lines.append(mission.strategist_brief[:800])
        return "\n".join(lines)

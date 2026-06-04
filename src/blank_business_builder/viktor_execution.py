"""
Viktor-style assume-forward execution + ReAct/reflect loop.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str, Optional[str]], Awaitable[str]]

VIKTOR_ASSUME_FORWARD_POLICY = """
EXECUTION PHILOSOPHY (VIKTOR MODE — NON-NEGOTIABLE):
- Execute first; report assumptions AFTER, never ask the user mid-task for clarification.
- When ambiguous: pick the highest-probability interpretation from context and memory; proceed.
- Only stop before irreversible harm (mass outbound, spend, delete, legal, production deploy without policy).
- If a step fails: try up to TWO alternative approaches before surfacing failure.
- Always deliver: what you did, what you assumed, what succeeded, what failed, suggested next step.
- Proactively note related work you noticed while executing (one short bullet).
- Do not say "Would you like me to…" or "Should I…" — do the work, then summarize.
"""

REACT_STEP_PROMPT = """
You are in a ReAct loop. Respond with JSON only:
{
  "think": "brief reasoning",
  "action": "tool|complete|retry",
  "tool_name": "optional",
  "tool_input": {},
  "complete": false,
  "final_output": "",
  "assumptions": ["list any assumptions made"],
  "confidence": 0.0-1.0
}
Set complete=true when the task is done; put deliverable in final_output.
"""


@dataclass
class PreparedMission:
    raw_request: str
    crystallized_intent: str
    constraints: List[str]
    strategist_brief: str = ""
    assumptions: List[str] = field(default_factory=list)
    ambiguity_score: float = 0.0
    proceed: bool = True


@dataclass
class ViktorRunResult:
    success: bool
    output: str
    assumptions: List[str]
    steps: List[Dict[str, Any]]
    reflections: List[str]
    related_notices: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


def score_ambiguity(text: str) -> float:
    """Higher = more ambiguous (0–1). Used to pick safest default interpretation."""
    if not text.strip():
        return 1.0
    lower = text.lower()
    score = 0.35
    if "?" in text:
        score += 0.15 * min(text.count("?"), 3)
    for phrase in ("maybe", "perhaps", "either", "or ", "not sure", "unclear", "tbd"):
        if phrase in lower:
            score += 0.08
    if any(w in lower for w in ("implement", "build", "fix", "send", "create", "deploy", "run")):
        score -= 0.12
    if len(text) > 120:
        score -= 0.08
    return max(0.0, min(1.0, score))


def needs_strategist_pass(text: str) -> bool:
    lower = text.lower()
    triggers = (
        "plan", "strategy", "decide", "roadmap", "architecture", "should we",
        "tradeoff", "milestone", "quarter", "launch", "prioritize",
    )
    return len(text) > 180 or any(t in lower for t in triggers)


class ViktorExecutor:
    """Assume-forward ReAct executor with reflection."""

    def __init__(
        self,
        generate: GenerateFn,
        *,
        max_steps: int = 6,
        ambiguity_execute_threshold: float = 0.45,
    ):
        self.generate = generate
        self.max_steps = max_steps
        self.ambiguity_execute_threshold = ambiguity_execute_threshold

    async def run(
        self,
        mission: PreparedMission,
        *,
        system_context: str = "",
        tool_runner: Optional[Callable[[str, Dict[str, Any]], Awaitable[str]]] = None,
    ) -> ViktorRunResult:
        steps: List[Dict[str, Any]] = []
        reflections: List[str] = []
        assumptions = list(mission.assumptions)
        observations: List[str] = []

        system = "\n\n".join(
            p
            for p in (
                VIKTOR_ASSUME_FORWARD_POLICY,
                system_context,
                f"CRYSTALLIZED MISSION:\n{mission.crystallized_intent}",
                f"CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in mission.constraints),
                mission.strategist_brief,
            )
            if p.strip()
        )

        final_output = ""
        success = False

        for step_idx in range(self.max_steps):
            obs_block = "\n".join(f"- {o}" for o in observations[-5:]) or "(none yet)"
            prompt = (
                f"Task (original): {mission.raw_request}\n"
                f"Step {step_idx + 1}/{self.max_steps}\n"
                f"Prior observations:\n{obs_block}\n\n"
                f"{REACT_STEP_PROMPT}"
            )
            raw = await self.generate(prompt, system)
            parsed = self._parse_json_block(raw)
            steps.append(parsed)
            assumptions.extend(parsed.get("assumptions") or [])

            if parsed.get("complete"):
                final_output = parsed.get("final_output") or raw
                success = True
                break

            action = (parsed.get("action") or "tool").lower()
            if action == "retry":
                reflections.append(parsed.get("think", "retry"))
                continue

            tool_name = parsed.get("tool_name") or "reasoning"
            tool_input = parsed.get("tool_input") or {}
            if tool_runner:
                try:
                    obs = await tool_runner(tool_name, tool_input)
                except Exception as exc:
                    obs = f"tool_error: {exc}"
            else:
                obs = parsed.get("think", "continuing")

            observations.append(f"{tool_name}: {obs[:500]}")
            reflect_prompt = (
                f"Observation from {tool_name}:\n{obs[:800]}\n\n"
                "Reflect in one sentence: did this match expectation? what's next?"
            )
            reflection = await self.generate(reflect_prompt, system)
            reflections.append(reflection.strip()[:400])

        if not success and observations:
            final_output = observations[-1]
            success = True

        related = await self._surface_related(mission, system, final_output)

        return ViktorRunResult(
            success=success,
            output=final_output,
            assumptions=list(dict.fromkeys(assumptions)),
            steps=steps,
            reflections=reflections,
            related_notices=related,
            metadata={"steps_used": len(steps), "ambiguity": mission.ambiguity_score},
        )

    async def _surface_related(
        self, mission: PreparedMission, system: str, output: str
    ) -> List[str]:
        prompt = (
            f"While completing: {mission.crystallized_intent[:300]}\n"
            "List 0-2 related proactive notices (one line each). JSON array of strings only."
        )
        raw = await self.generate(prompt, system)
        try:
            start = raw.find("[")
            end = raw.rfind("]")
            if start >= 0 and end > start:
                arr = json.loads(raw[start : end + 1])
                return [str(x) for x in arr][:2]
        except json.JSONDecodeError:
            pass
        return []

    @staticmethod
    def _parse_json_block(raw: str) -> Dict[str, Any]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"think": raw[:300], "action": "complete", "complete": True, "final_output": raw}

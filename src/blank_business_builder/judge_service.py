"""
Fast local judge for worker outputs and milestone packs.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .local_model_client import LocalModelClient
from .company_pack import judge_domain_for_artifact, load_judge_skill
from .judge_dataset_collector import JudgeDatasetCollector

logger = logging.getLogger(__name__)


class JudgeVerdict(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    ESCALATE = "escalate"


@dataclass
class JudgeResult:
    verdict: JudgeVerdict
    score: float
    fixes: List[str] = field(default_factory=list)
    reasoning: str = ""
    policy_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data


JUDGE_SYSTEM = (
    "You are a strict operations judge for an autonomous business stack. "
    "Evaluate whether an artifact is complete, on-mission, and safe to advance. "
    "Respond with JSON only: "
    '{"verdict":"pass|revise|escalate","score":0.0-1.0,"fixes":["..."],"reasoning":"...","policy_flags":["..."]}. '
    "Use escalate if outbound email, payment, bulk CRM ingest, or bulk Apollo would be required without approval."
)


class JudgeService:
    """Rubric-based critic — runs often, cheaply."""

    def __init__(self, client: Optional[LocalModelClient] = None):
        self.client = client or LocalModelClient.for_judge()
        self.collector = JudgeDatasetCollector()

    def _build_system_prompt(
        self,
        artifact_type: str,
        business_name: Optional[str] = None,
    ) -> str:
        parts = [JUDGE_SYSTEM]
        if business_name:
            domain = judge_domain_for_artifact(artifact_type)
            skill = load_judge_skill(business_name, domain)
            if skill:
                parts.append(f"\n## Domain rubric (judge-{domain})\n{skill}")
            few_shot = self.collector.few_shot_block(business_name, artifact_type)
            if few_shot:
                parts.append(f"\n{few_shot}")
        return "\n".join(parts)

    async def evaluate(
        self,
        *,
        artifact_type: str,
        content: str,
        mission: str,
        metadata: Optional[Dict[str, Any]] = None,
        business_name: Optional[str] = None,
    ) -> JudgeResult:
        metadata = metadata or {}
        deterministic = self._deterministic_checks(artifact_type, content, metadata)
        if deterministic.verdict == JudgeVerdict.ESCALATE and deterministic.score <= 0.3:
            return deterministic

        prompt = (
            f"Mission:\n{mission}\n\n"
            f"Artifact type: {artifact_type}\n"
            f"Metadata: {json.dumps(metadata, default=str)[:2000]}\n\n"
            f"Content:\n{content[:12000]}\n\n"
            f"Deterministic pre-check score: {deterministic.score:.2f}, flags: {deterministic.policy_flags}"
        )
        try:
            system = self._build_system_prompt(artifact_type, business_name)
            raw = await self.client.generate(prompt, system_prompt=system)
            parsed = self._parse_json_verdict(raw)
            merged_score = min(1.0, (parsed.score + deterministic.score) / 2)
            fixes = list(dict.fromkeys(parsed.fixes + deterministic.fixes))
            flags = list(dict.fromkeys(parsed.policy_flags + deterministic.policy_flags))
            verdict = parsed.verdict
            if deterministic.verdict == JudgeVerdict.ESCALATE:
                verdict = JudgeVerdict.ESCALATE
            elif parsed.verdict == JudgeVerdict.PASS and merged_score < 0.7:
                verdict = JudgeVerdict.REVISE
            return JudgeResult(
                verdict=verdict,
                score=merged_score,
                fixes=fixes,
                reasoning=parsed.reasoning or deterministic.reasoning,
                policy_flags=flags,
            )
        except Exception as exc:
            logger.warning("Judge model unavailable, using deterministic only: %s", exc)
            return deterministic

    def _deterministic_checks(
        self,
        artifact_type: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> JudgeResult:
        fixes: List[str] = []
        flags: List[str] = []
        score = 1.0
        lowered = content.lower()

        if not content.strip():
            return JudgeResult(
                verdict=JudgeVerdict.REVISE,
                score=0.0,
                fixes=["Artifact is empty"],
                reasoning="No content to evaluate",
            )

        if artifact_type == "lead_batch":
            lead_count = metadata.get("lead_count") or content.count('"url"')
            if lead_count == 0:
                fixes.append("Lead batch appears empty")
                score -= 0.4
            has_placeholder_example_host = False
            for token in re.findall(r"https?://[^\s\"'<>]+", content):
                host = urlparse(token).hostname
                if host and (host == "example.com" or host.endswith(".example.com")):
                    has_placeholder_example_host = True
                    break
            if has_placeholder_example_host:
                fixes.append("Remove placeholder example.com leads")
                score -= 0.3

        if artifact_type in ("email_draft", "campaign_draft"):
            if "unsubscribe" not in lowered and "opt out" not in lowered:
                flags.append("missing_unsubscribe_hint")
                score -= 0.1
            if metadata.get("requires_approval"):
                flags.append("approval_required_before_send")
                return JudgeResult(
                    verdict=JudgeVerdict.ESCALATE,
                    score=max(0.0, score - 0.2),
                    fixes=fixes,
                    reasoning="Outbound action requires human approval",
                    policy_flags=flags,
                )

        if artifact_type == "milestone_pack":
            required = ("summary", "artifacts", "next_actions")
            for key in required:
                if key not in metadata and key not in lowered:
                    fixes.append(f"Milestone pack missing {key}")
                    score -= 0.15

        verdict = JudgeVerdict.PASS if score >= 0.75 else JudgeVerdict.REVISE
        return JudgeResult(
            verdict=verdict,
            score=max(0.0, min(1.0, score)),
            fixes=fixes,
            reasoning="Deterministic rubric",
            policy_flags=flags,
        )

    def _parse_json_verdict(self, raw: str) -> JudgeResult:
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return JudgeResult(
                verdict=JudgeVerdict.REVISE,
                score=0.5,
                fixes=["Judge returned non-JSON response"],
                reasoning=raw[:500],
            )
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return JudgeResult(
                verdict=JudgeVerdict.REVISE,
                score=0.5,
                fixes=["Could not parse judge JSON"],
                reasoning=raw[:500],
            )

        verdict_raw = str(data.get("verdict", "revise")).lower()
        if verdict_raw not in ("pass", "revise", "escalate"):
            verdict_raw = "revise"
        return JudgeResult(
            verdict=JudgeVerdict(verdict_raw),
            score=float(data.get("score", 0.5)),
            fixes=[str(x) for x in (data.get("fixes") or [])],
            reasoning=str(data.get("reasoning", "")),
            policy_flags=[str(x) for x in (data.get("policy_flags") or [])],
        )

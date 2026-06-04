"""
Parliament airlock for milestone packs before external side effects.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .judge_service import JudgeResult, JudgeService, JudgeVerdict


@dataclass
class MilestonePack:
    """Bundle ready for final review before ship."""

    milestone_id: str
    business_name: str
    title: str
    summary: str
    artifact_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParliamentDecision:
    status: str
    score: float
    judge: Dict[str, Any]
    red_flags: List[str] = field(default_factory=list)
    parliament_status: str = "NEEDS_REFINEMENT"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MilestoneParliamentGate:
    """
    Final gate: Judge + score threshold before CRM/email/campaign ship.
    Full EnhancedParliamentValidator remains for UnifiedBusinessModel flows.
    """

    def __init__(
        self,
        judge: Optional[JudgeService] = None,
        approval_threshold: float = 0.85,
    ):
        self.judge = judge or JudgeService()
        self.approval_threshold = approval_threshold

    async def review(self, pack: MilestonePack, *, mission: str) -> ParliamentDecision:
        judge_meta = dict(pack.metadata)
        judge_meta.setdefault("milestone_id", pack.milestone_id)
        judge_meta.setdefault("summary", pack.summary)

        judge_result: JudgeResult = await self.judge.evaluate(
            artifact_type="milestone_pack",
            content=f"{pack.title}\n\n{pack.summary}\n\n{pack.content}",
            mission=mission,
            metadata=judge_meta,
        )

        red_flags = list(judge_result.policy_flags)
        if judge_result.verdict == JudgeVerdict.ESCALATE:
            red_flags.append("Judge escalated — requires approval before ship")
        if judge_result.fixes:
            red_flags.extend(judge_result.fixes)

        score = judge_result.score
        if judge_result.verdict == JudgeVerdict.REVISE:
            score = min(score, 0.79)

        parliament_status = "APPROVED" if score >= self.approval_threshold else "NEEDS_REFINEMENT"
        overall = "VERIFIED" if parliament_status == "APPROVED" else "FAILED_VALIDATION"

        return ParliamentDecision(
            status=overall,
            score=score,
            judge=judge_result.to_dict(),
            red_flags=red_flags,
            parliament_status=parliament_status,
        )

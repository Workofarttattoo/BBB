"""
Board Room
==========
Orchestrates the AI C-Suite. Runs board meetings, collects decisions,
builds consensus, and routes tasks to the right domain expert.

Usage:
    from blank_business_builder.board.board_room import BoardRoom

    board = BoardRoom()
    result = board.deliberate("Should we expand into European markets?")
    advice = board.ask_expert("cfo", "What's our current burn rate risk?")
    plan   = board.full_meeting("Q3 growth strategy for NovaSaaS AI")
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base_member import BoardDecision, BoardMember
from .members import CEO, COO, CFO, CTO, CMO, CSO, BoardChairman

logger = logging.getLogger(__name__)

_ROLE_MAP = {
    "ceo": CEO, "chief executive": CEO,
    "coo": COO, "operations": COO,
    "cfo": CFO, "finance": CFO, "financial": CFO,
    "cto": CTO, "technology": CTO, "technical": CTO,
    "cmo": CMO, "marketing": CMO, "creative": CMO,
    "cso": CSO, "strategy": CSO, "grok": CSO,
    "chairman": BoardChairman, "claude": BoardChairman,
}


@dataclass
class MeetingMinutes:
    topic: str
    decisions: List[BoardDecision]
    consensus: str
    chairman_verdict: str
    majority: str           # "approve" | "reject" | "modify" | "split"
    vote_tally: Dict[str, int]
    duration_seconds: float
    available_members: List[str]
    unavailable_members: List[str]

    def summary(self) -> str:
        lines = [
            f"Board Meeting: {self.topic}",
            f"Outcome: {self.majority.upper()} ({self.duration_seconds:.1f}s)",
            f"Members present: {', '.join(self.available_members)}",
            "",
            "Votes:",
        ]
        for d in self.decisions:
            conf = f"{d.confidence:.0%}"
            lines.append(f"  {d.member} ({d.model}): {d.recommendation.upper()} [{conf}]")
            if d.opinion:
                lines.append(f"    → {d.opinion[:120]}")
        if self.chairman_verdict:
            lines.append(f"\nChairman: {self.chairman_verdict[:300]}")
        return "\n".join(lines)


class BoardRoom:
    """
    The AI board room. Instantiates all C-suite members and orchestrates
    parallel deliberations, majority votes, and chairman oversight.
    """

    def __init__(self, parallel: bool = True, timeout_per_member: int = 90) -> None:
        self.parallel = parallel
        self.timeout  = timeout_per_member

        self.members: Dict[str, BoardMember] = {
            "chairman": BoardChairman(),
            "ceo":      CEO(),
            "coo":      COO(),
            "cfo":      CFO(),
            "cto":      CTO(),
            "cmo":      CMO(),
            "cso":      CSO(),
        }

    # ── public API ───────────────────────────────────────────────────────────

    def deliberate(
        self,
        topic: str,
        context: Optional[str] = None,
        include_chairman: bool = True,
    ) -> MeetingMinutes:
        """
        Run a full board meeting on a topic.
        All C-suite members deliberate in parallel, then the Chairman reviews.
        """
        t0 = time.time()
        logger.info("Board meeting called: %s", topic[:80])

        # C-suite deliberate (parallel)
        working_members = {k: v for k, v in self.members.items() if k != "chairman"}
        decisions, available, unavailable = self._collect_decisions(
            working_members, topic, context
        )

        # Chairman reviews the board's decisions
        chairman_verdict = ""
        if include_chairman and decisions:
            board_summary = "\n".join(
                f"- {d.member}: {d.recommendation} ({d.opinion[:100]})"
                for d in decisions
            )
            chairman_prompt = (
                f"Topic: {topic}\n\n"
                f"Board decisions:\n{board_summary}\n\n"
                f"As Board Chairman, synthesise these views and give your final verdict. "
                f"Approve, reject, or modify — and state exactly why."
            )
            try:
                chairman_verdict = self.members["chairman"].think(chairman_prompt)
            except Exception as exc:
                chairman_verdict = f"Chairman unavailable: {exc}"

        consensus, majority, tally = self._build_consensus(decisions)

        return MeetingMinutes(
            topic=topic,
            decisions=decisions,
            consensus=consensus,
            chairman_verdict=chairman_verdict,
            majority=majority,
            vote_tally=tally,
            duration_seconds=round(time.time() - t0, 2),
            available_members=available,
            unavailable_members=unavailable,
        )

    def ask_expert(self, role: str, question: str) -> str:
        """Route a question to the domain-appropriate board member."""
        key = role.lower().strip()
        member = self.members.get(key) or self.members.get(_ROLE_MAP.get(key, "coo").__name__.lower())
        if member is None:
            # fuzzy match
            for k, cls in _ROLE_MAP.items():
                if k in key:
                    member = self.members.get(cls.__name__.lower()[:3]) or self._find_by_class(cls)
                    break
        if member is None:
            return f"No board member found for role '{role}'"
        return member.advise(question)

    def full_meeting(self, objective: str) -> str:
        """
        Runs a full strategic meeting and returns formatted minutes.
        Intended for major decisions like launching a new business,
        pivoting strategy, or approving a large spend.
        """
        minutes = self.deliberate(objective)
        return minutes.summary()

    def quick_consult(self, question: str) -> str:
        """
        Fast single-member advice — routes to best expert based on keywords.
        Faster than a full meeting for routine questions.
        """
        q = question.lower()
        if any(w in q for w in ["revenue", "cost", "budget", "money", "invoice", "stripe", "cash"]):
            return self.members["cfo"].advise(question)
        if any(w in q for w in ["code", "api", "bug", "deploy", "architecture", "database", "server"]):
            return self.members["cto"].advise(question)
        if any(w in q for w in ["marketing", "email", "campaign", "brand", "copy", "social", "content"]):
            return self.members["cmo"].advise(question)
        if any(w in q for w in ["strategy", "market", "competitor", "expand", "pivot", "partnership"]):
            return self.members["cso"].advise(question)
        if any(w in q for w in ["workflow", "process", "agent", "task", "operations", "team"]):
            return self.members["coo"].advise(question)
        # Default to CEO for big-picture questions
        return self.members["ceo"].advise(question)

    def status(self) -> Dict[str, Any]:
        """Return availability of each board member."""
        report = {}
        for role, member in self.members.items():
            report[role] = {
                "title":  member.title,
                "model":  member.model,
                "vps":    getattr(member, "vps_url", "via-paperclip"),
                "online": member.is_available() if hasattr(member, "_healthy") else "unknown",
            }
        return report

    # ── internals ────────────────────────────────────────────────────────────

    def _collect_decisions(
        self,
        members: Dict[str, BoardMember],
        topic: str,
        context: Optional[str],
    ):
        decisions: List[BoardDecision] = []
        available: List[str] = []
        unavailable: List[str] = []

        def _deliberate_one(role: str, member: BoardMember):
            try:
                d = member.deliberate(topic, context)
                return role, d, True
            except Exception as exc:
                logger.warning("%s deliberation failed: %s", role, exc)
                return role, None, False

        if self.parallel:
            with ThreadPoolExecutor(max_workers=len(members)) as ex:
                futures = {ex.submit(_deliberate_one, role, m): role
                           for role, m in members.items()}
                for fut in as_completed(futures, timeout=self.timeout):
                    role, decision, ok = fut.result()
                    if ok and decision:
                        decisions.append(decision)
                        available.append(role)
                    else:
                        unavailable.append(role)
        else:
            for role, member in members.items():
                role_out, decision, ok = _deliberate_one(role, member)
                if ok and decision:
                    decisions.append(decision)
                    available.append(role)
                else:
                    unavailable.append(role)

        return decisions, available, unavailable

    @staticmethod
    def _build_consensus(decisions: List[BoardDecision]):
        if not decisions:
            return "No quorum — all board members unavailable.", "abstain", {}

        tally: Dict[str, int] = {"approve": 0, "reject": 0, "modify": 0, "abstain": 0}
        for d in decisions:
            rec = d.recommendation.lower()
            if rec in tally:
                tally[rec] += 1
            else:
                tally["abstain"] += 1

        majority = max(tally, key=tally.__getitem__)

        # Build narrative consensus
        approvers  = [d.member for d in decisions if d.recommendation == "approve"]
        rejecters  = [d.member for d in decisions if d.recommendation == "reject"]
        modifiers  = [d.member for d in decisions if d.recommendation == "modify"]
        conditions = [c for d in decisions if d.recommendation == "modify" for c in d.conditions]

        parts = []
        if approvers:
            parts.append(f"{', '.join(approvers)} approve.")
        if rejecters:
            parts.append(f"{', '.join(rejecters)} reject.")
        if modifiers:
            parts.append(f"{', '.join(modifiers)} want modifications.")
        if conditions:
            parts.append(f"Conditions: {'; '.join(conditions[:3])}.")

        consensus = " ".join(parts) or "No clear consensus reached."
        return consensus, majority, tally

    def _find_by_class(self, cls) -> Optional[BoardMember]:
        for m in self.members.values():
            if isinstance(m, cls):
                return m
        return None


# Module singleton
_board: Optional[BoardRoom] = None


def get_board() -> BoardRoom:
    global _board
    if _board is None:
        _board = BoardRoom()
    return _board

"""
Always-on Middle Manager — long-horizon supervisor for BBB worker agents.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .config import settings
from .judge_service import JudgeService
from .local_model_client import LocalModelClient
from .middle_manager_state import collect_middle_manager_state
from .milestone_parliament import MilestonePack, MilestoneParliamentGate

if TYPE_CHECKING:
    from .autonomous_business import AutonomousBusinessOrchestrator

logger = logging.getLogger(__name__)

MIDDLE_MANAGER_SYSTEM = (
    "You are the always-on Middle Manager for an autonomous business operations stack. "
    "You do NOT send email, charge payments, or ingest CRM data. You audit state, tie loose ends, "
    "and propose at most three concrete supervisor actions. "
    "Respond with JSON only: "
    '{"brief":"CEO-readable summary","actions":[{"type":"reassign|unblock|escalate_approval|'
    'request_revision|sync_paperclip|prepare_milestone","target":"","details":"","priority":1-10}],'
    '"open_loops":["..."],"confidence":0.0-1.0}'
)


@dataclass
class MiddleManagerReport:
    business_name: str
    heartbeat_at: str
    state: Dict[str, Any]
    brief: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    open_loops: List[str] = field(default_factory=list)
    confidence: float = 0.0
    model: str = ""
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MiddleManagerLoop:
    """Heartbeat supervisor + milestone Parliament routing."""

    def __init__(
        self,
        orchestrator: "AutonomousBusinessOrchestrator",
        *,
        middle_client: Optional[LocalModelClient] = None,
        judge: Optional[JudgeService] = None,
        parliament: Optional[MilestoneParliamentGate] = None,
    ):
        self.orchestrator = orchestrator
        self.middle_client = middle_client or LocalModelClient.for_middle_manager()
        self.judge = judge or JudgeService()
        self.parliament = parliament or MilestoneParliamentGate(judge=self.judge)
        self.log_path = Path(settings.MIDDLE_MANAGER_LOG_PATH)

    async def run_heartbeat(self, *, mission: Optional[str] = None) -> MiddleManagerReport:
        state = collect_middle_manager_state(self.orchestrator, mission=mission)
        report = MiddleManagerReport(
            business_name=state.business_name,
            heartbeat_at=datetime.utcnow().isoformat(),
            state=state.to_dict(),
            brief="",
            model=self.middle_client.model,
        )

        prompt = (
            "Current operational snapshot:\n"
            f"{json.dumps(state.to_dict(), indent=2)[:14000]}\n\n"
            "Identify loose ends and propose supervisor actions. "
            "Never propose direct outbound email, payment, or CRM ingest — only prepare or escalate approvals."
        )

        try:
            raw = await self.middle_client.generate(prompt, system_prompt=MIDDLE_MANAGER_SYSTEM)
            parsed = self._parse_supervisor_response(raw)
            report.brief = parsed.get("brief", "")
            report.actions = parsed.get("actions", [])[:3]
            report.open_loops = list(
                dict.fromkeys((parsed.get("open_loops") or []) + state.loose_end_hints)
            )
            report.confidence = float(parsed.get("confidence", 0.7))
            self._apply_safe_actions(report.actions)
        except Exception as exc:
            logger.exception("Middle manager heartbeat failed")
            report.errors.append(str(exc))
            report.brief = (
                f"Supervisor offline ({exc}). Loose ends: "
                + "; ".join(state.loose_end_hints or ["none detected"])
            )
            report.open_loops = state.loose_end_hints

        self._append_log(report)
        self._publish_hive(report)
        return report

    async def review_milestone(
        self,
        pack: MilestonePack,
        *,
        mission: Optional[str] = None,
    ) -> Dict[str, Any]:
        state = collect_middle_manager_state(self.orchestrator, mission=mission)
        decision = await self.parliament.review(pack, mission=state.mission)
        payload = {
            "milestone": pack.to_dict(),
            "parliament": decision.to_dict(),
        }
        self._append_log(
            MiddleManagerReport(
                business_name=pack.business_name,
                heartbeat_at=datetime.utcnow().isoformat(),
                state={"milestone_review": True},
                brief=f"Milestone '{pack.title}' → {decision.parliament_status}",
                open_loops=decision.red_flags,
                confidence=decision.score,
                model=self.middle_client.model,
            )
        )
        return payload

    async def judge_artifact(
        self,
        *,
        artifact_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        state = collect_middle_manager_state(self.orchestrator)
        result = await self.judge.evaluate(
            artifact_type=artifact_type,
            content=content,
            mission=state.mission,
            metadata=metadata or {},
        )
        return result.to_dict()

    def _parse_supervisor_response(self, raw: str) -> Dict[str, Any]:
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return {
                "brief": raw[:1000],
                "actions": [],
                "open_loops": [],
                "confidence": 0.5,
            }
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {
                "brief": raw[:1000],
                "actions": [],
                "open_loops": ["Supervisor returned invalid JSON"],
                "confidence": 0.5,
            }

    def _apply_safe_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Only in-process, non-destructive adjustments."""
        for action in actions:
            action_type = str(action.get("type", "")).lower()
            target = str(action.get("target", ""))
            if action_type == "unblock" and target:
                for task in self.orchestrator.task_queue:
                    if task.task_id == target and task.status.value == "blocked":
                        from .autonomous_business import TaskStatus

                        task.status = TaskStatus.PENDING
                        logger.info("Middle manager unblocked task %s", target)
            elif action_type == "reassign" and target:
                assignee = action.get("details") or action.get("assignee")
                if assignee:
                    for task in self.orchestrator.task_queue:
                        if task.task_id == target:
                            task.assigned_to = str(assignee)
                            logger.info("Middle manager reassigned %s → %s", target, assignee)

    def _append_log(self, report: MiddleManagerReport) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(report.to_dict(), default=str) + "\n")
        except OSError as exc:
            logger.warning("Could not write middle manager log: %s", exc)

    def _publish_hive(self, report: MiddleManagerReport) -> None:
        hive = getattr(self.orchestrator, "hive_mind", None)
        if not hive:
            return
        try:
            from .hive_mind_coordinator import AgentType, DecisionPriority, HiveMessage

            hive.send_message(
                HiveMessage(
                    sender="middle_manager",
                    agent_type=AgentType.LEVEL9_MONITORING,
                    message_type="supervisor_heartbeat",
                    payload=report.to_dict(),
                    priority=DecisionPriority.MEDIUM,
                )
            )
        except Exception as exc:
            logger.debug("Hive publish skipped: %s", exc)


def load_last_report(business_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    path = Path(settings.MIDDLE_MANAGER_LOG_PATH)
    if not path.exists():
        return None
    last: Optional[Dict[str, Any]] = None
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if business_name and row.get("business_name") != business_name:
                    continue
                last = row
    except OSError:
        return None
    return last

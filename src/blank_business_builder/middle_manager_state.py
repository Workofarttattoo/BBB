"""
Operational snapshot for the always-on Middle Manager loop.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .approval_gates import ApprovalStore

if TYPE_CHECKING:
    from .autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, TaskStatus


@dataclass
class TaskSnapshot:
    task_id: str
    role: str
    status: str
    description: str
    priority: int
    assigned_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MiddleManagerState:
    business_name: str
    mission: str
    collected_at: str
    tasks: List[TaskSnapshot] = field(default_factory=list)
    pending_approvals: List[Dict[str, Any]] = field(default_factory=list)
    task_counts: Dict[str, int] = field(default_factory=dict)
    paperclip_issue_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    loose_end_hints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "business_name": self.business_name,
            "mission": self.mission,
            "collected_at": self.collected_at,
            "tasks": [t.to_dict() for t in self.tasks],
            "pending_approvals": self.pending_approvals,
            "task_counts": self.task_counts,
            "paperclip_issue_count": self.paperclip_issue_count,
            "metrics": self.metrics,
            "loose_end_hints": self.loose_end_hints,
        }


def collect_middle_manager_state(
    orchestrator: "AutonomousBusinessOrchestrator",
    *,
    mission: Optional[str] = None,
) -> MiddleManagerState:
    from .autonomous_business import TaskStatus

    tasks: List[TaskSnapshot] = []
    counts: Dict[str, int] = {s.value: 0 for s in TaskStatus}

    for task in orchestrator.task_queue:
        counts[task.status.value] = counts.get(task.status.value, 0) + 1
        tasks.append(
            TaskSnapshot(
                task_id=task.task_id,
                role=task.role.value,
                description=task.description[:500],
                status=task.status.value,
                priority=task.priority,
                assigned_to=task.assigned_to,
            )
        )

    pending = [r.to_dict() for r in ApprovalStore.list_pending(orchestrator.business_concept)]
    hints = _detect_loose_ends(tasks, pending, orchestrator)

    metrics = {
        "tasks_completed": getattr(orchestrator.metrics, "tasks_completed", 0),
        "tasks_pending": getattr(orchestrator.metrics, "tasks_pending", 0),
        "leads_generated": getattr(orchestrator.metrics, "leads_generated", 0),
    }

    return MiddleManagerState(
        business_name=orchestrator.business_concept,
        mission=mission or _default_mission(orchestrator.business_concept),
        collected_at=datetime.utcnow().isoformat(),
        tasks=tasks,
        pending_approvals=pending,
        task_counts=counts,
        paperclip_issue_count=len(getattr(orchestrator.paperclip_sync, "_issue_index", {})),
        metrics=metrics,
        loose_end_hints=hints,
    )


def _default_mission(business_name: str) -> str:
    return (
        f"Operate {business_name}: advance Paperclip issues, resolve blocked work, "
        "prepare approval-ready outbound packages, and keep worker outputs consistent."
    )


def _detect_loose_ends(
    tasks: List[TaskSnapshot],
    pending_approvals: List[Dict[str, Any]],
    orchestrator: "AutonomousBusinessOrchestrator",
) -> List[str]:
    hints: List[str] = []
    blocked = [t for t in tasks if t.status == "blocked"]
    stale_in_progress = [t for t in tasks if t.status == "in_progress"]
    unassigned_pending = [t for t in tasks if t.status == "pending" and not t.assigned_to]

    if blocked:
        hints.append(f"{len(blocked)} blocked task(s) need dependency or owner resolution")
    if len(stale_in_progress) > 5:
        hints.append(f"{len(stale_in_progress)} in_progress tasks — possible stall")
    if unassigned_pending:
        hints.append(f"{len(unassigned_pending)} pending task(s) without assignee")
    if pending_approvals:
        hints.append(f"{len(pending_approvals)} approval(s) waiting on human")
    if orchestrator.metrics.leads_generated > 0 and not any(
        a.get("action") == "lead_ingest" for a in pending_approvals
    ):
        hints.append("Leads may exist without a pending ingest approval package")

    pc_index = getattr(orchestrator.paperclip_sync, "_issue_index", {})
    task_ids = {t.task_id for t in tasks}
    orphan_pc = [tid for tid in pc_index.values() if tid not in task_ids]
    if orphan_pc:
        hints.append(f"{len(orphan_pc)} Paperclip index entries missing from task queue")

    return hints

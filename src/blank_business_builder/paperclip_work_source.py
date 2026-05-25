"""
Paperclip issue sync — single work source for staffed autonomous agents.

Maps external control-plane issues (Paperclip) into BBB AutonomousTask queue.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .autonomous_business import (
        AgentRole,
        AutonomousBusinessOrchestrator,
        AutonomousTask,
        TaskStatus,
    )

logger = logging.getLogger(__name__)

PAPERCLIP_LABEL_ROLE_MAP = {
    "bbb:execute": None,
    "echo:strategy": "executive",
    "human:apollo": None,
}

ISSUE_STATUS_TO_TASK = {
    "backlog": "pending",
    "todo": "pending",
    "in_progress": "in_progress",
    "in_review": "in_progress",
    "blocked": "blocked",
    "done": "completed",
    "cancelled": "failed",
}


@dataclass
class PaperclipIssuePayload:
    """Inbound issue from Paperclip webhook or manual sync."""

    issue_id: str
    identifier: Optional[str] = None
    title: str = ""
    description: str = ""
    status: str = "todo"
    assignee_agent_id: Optional[str] = None
    assignee_role: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    company_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: int = 5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperclipIssuePayload":
        labels = data.get("labels") or []
        if isinstance(labels, str):
            labels = [labels]
        return cls(
            issue_id=str(data.get("id") or data.get("issue_id") or ""),
            identifier=data.get("identifier"),
            title=str(data.get("title") or ""),
            description=str(data.get("description") or ""),
            status=str(data.get("status") or "todo"),
            assignee_agent_id=data.get("assignee_agent_id") or data.get("assigneeAgentId"),
            assignee_role=data.get("assignee_role") or data.get("assigneeRole"),
            labels=list(labels),
            company_id=data.get("company_id") or data.get("companyId"),
            project_id=data.get("project_id") or data.get("projectId"),
            priority=int(data.get("priority") or 5),
        )


class PaperclipWorkSourceSync:
    """Keeps BBB task queue aligned with Paperclip issues."""

    def __init__(self, orchestrator: "AutonomousBusinessOrchestrator"):
        self.orchestrator = orchestrator
        self._issue_index: Dict[str, str] = {}

    def _resolve_role(self, issue: PaperclipIssuePayload) -> "AgentRole":
        from .autonomous_business import AgentRole

        if issue.assignee_role:
            try:
                return AgentRole(issue.assignee_role)
            except ValueError:
                logger.warning("Unknown assignee_role=%s", issue.assignee_role)

        for label in issue.labels:
            if label.startswith("role:"):
                try:
                    return AgentRole(label.split(":", 1)[1])
                except ValueError:
                    pass
            mapped = PAPERCLIP_LABEL_ROLE_MAP.get(label)
            if mapped:
                return AgentRole(mapped)
        return AgentRole.SALES

    def _task_status(self, issue_status: str) -> "TaskStatus":
        from .autonomous_business import TaskStatus

        key = ISSUE_STATUS_TO_TASK.get(issue_status, "pending")
        return TaskStatus(key)

    def should_skip_autonomous_task(self, issue: PaperclipIssuePayload) -> bool:
        """human:apollo and unlabeled board-only work stay out of the agent loop."""
        labels = {label.lower() for label in issue.labels}
        if "human:apollo" in labels:
            return True
        if issue.status in ("done", "cancelled"):
            return True
        return False

    def upsert_issue(self, issue: PaperclipIssuePayload) -> Dict[str, Any]:
        from .autonomous_business import AutonomousTask

        if not issue.issue_id:
            raise ValueError("issue_id is required")

        if self.should_skip_autonomous_task(issue):
            return {
                "synced": False,
                "reason": "human_or_terminal_issue",
                "issue_id": issue.issue_id,
            }

        task_id = f"pc-{issue.issue_id}"
        existing_id = self._issue_index.get(issue.issue_id)
        role = self._resolve_role(issue)
        task_status = self._task_status(issue.status)
        description = issue.description or issue.title

        if existing_id:
            for task in self.orchestrator.task_queue:
                if task.task_id == existing_id:
                    task.description = description
                    task.status = task_status
                    task.priority = issue.priority
                    return {"synced": True, "task_id": task.task_id, "updated": True}
        else:
            task = AutonomousTask(
                task_id=task_id,
                role=role,
                description=f"[{issue.identifier or issue.issue_id}] {description}",
                status=task_status,
                assigned_to=issue.assignee_agent_id,
                priority=issue.priority,
            )
            self.orchestrator.add_task(task)
            self._issue_index[issue.issue_id] = task_id
            return {"synced": True, "task_id": task_id, "updated": False}

        return {"synced": False, "reason": "task_not_found", "issue_id": issue.issue_id}

    def sync_batch(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for raw in issues:
            try:
                payload = PaperclipIssuePayload.from_dict(raw)
                results.append(self.upsert_issue(payload))
            except Exception as exc:
                results.append({"synced": False, "error": str(exc), "raw": raw})
        return {
            "count": len(results),
            "synced": sum(1 for r in results if r.get("synced")),
            "results": results,
            "synced_at": datetime.utcnow().isoformat(),
        }

"""
Auto-judge loop after worker task completion (Ralph-style revise re-queue).

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from .judge_dataset_collector import JudgeDatasetCollector
from .judge_service import JudgeService, JudgeVerdict
from .local_model_client import RoleModelRouter

if TYPE_CHECKING:
    from .autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, TaskStatus

logger = logging.getLogger(__name__)

MAX_JUDGE_REVISE_ATTEMPTS = 3


class AutoJudgeLoop:
    """Evaluate worker artifacts and re-queue on revise."""

    def __init__(
        self,
        business_name: str,
        orchestrator: "AutonomousBusinessOrchestrator",
        *,
        judge: Optional[JudgeService] = None,
        collector: Optional[JudgeDatasetCollector] = None,
        max_revise: int = MAX_JUDGE_REVISE_ATTEMPTS,
    ):
        self.business_name = business_name
        self.orchestrator = orchestrator
        self.judge = judge or JudgeService(client=RoleModelRouter().for_judge())
        self.collector = collector or JudgeDatasetCollector()
        self.max_revise = max_revise
        if not hasattr(orchestrator, "judge_revise_counts"):
            orchestrator.judge_revise_counts = {}

    async def evaluate_worker_result(
        self,
        task: "AutonomousTask",
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        from .autonomous_business import TaskStatus

        artifact_type = str(result.get("artifact_type") or "generic_output")
        content = str(result.get("content") or result.get("summary") or "")
        if not content and result.get("task_description"):
            content = str(result.get("task_description"))
        metadata = dict(result.get("metadata") or {})
        mission = task.description

        judge_result = await self.judge.evaluate(
            artifact_type=artifact_type,
            content=content,
            mission=mission,
            metadata=metadata,
            business_name=self.business_name,
        )

        self.collector.log_evaluation(
            business_name=self.business_name,
            artifact_type=artifact_type,
            mission=mission,
            content=content,
            metadata=metadata,
            verdict=judge_result.verdict.value,
            score=judge_result.score,
            fixes=judge_result.fixes,
            policy_flags=judge_result.policy_flags,
            task_id=task.task_id,
        )

        outcome = {
            "judge_verdict": judge_result.verdict.value,
            "judge_score": judge_result.score,
            "judge_fixes": judge_result.fixes,
            "judge_policy_flags": judge_result.policy_flags,
        }
        result.update(outcome)

        if judge_result.verdict == JudgeVerdict.PASS:
            return result

        if judge_result.verdict == JudgeVerdict.ESCALATE:
            result["success"] = False
            result["requires_approval"] = True
            self.orchestrator._set_task_status(
                task,
                TaskStatus.BLOCKED,
                result=result,
            )
            return result

        # REVISE — re-queue with fix hints
        attempts = self.orchestrator.judge_revise_counts.get(task.task_id, 0) + 1
        self.orchestrator.judge_revise_counts[task.task_id] = attempts
        if attempts >= self.max_revise:
            result["success"] = False
            result["error"] = f"Judge revise limit ({self.max_revise}) exceeded"
            self.orchestrator._set_task_status(task, TaskStatus.FAILED, result=result)
            return result

        fix_note = "; ".join(judge_result.fixes) or "Address judge feedback"
        task.description = f"{task.description}\n\n[Judge revise {attempts}/{self.max_revise}]: {fix_note}"
        self.orchestrator._set_task_status(
            task,
            TaskStatus.PENDING,
            result=result,
            clear_assignment=True,
        )
        if task not in self.orchestrator.pending_tasks:
            self.orchestrator.pending_tasks.append(task)
        result["success"] = False
        result["requeued_for_revise"] = True
        return result

"""
Agent ops service — memory, proactive jobs, settings for GUI + API.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from .agent_memory import AgentMemoryStore
from .agent_memory_seed import SEMANTIC_SEEDS, ensure_seeded, seed_workspace
from .agent_ops_state import (
    get_agent_ops_settings,
    list_proactive_runs,
    record_proactive_run,
    save_agent_ops_settings,
)
from .proactive_scheduler import ProactiveScheduler, ScheduledJob

logger = logging.getLogger(__name__)


def _celery_broker_reachable() -> bool:
    """Quick check so GUI 'Run now' does not block on Celery/redis retries."""
    try:
        import redis

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(url, socket_connect_timeout=0.3)
        client.ping()
        return True
    except Exception:
        return False


class AgentOpsService:
    def get_settings(self) -> Dict[str, Any]:
        return get_agent_ops_settings()

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "viktor_mode_enabled",
            "viktor_strategist_enabled",
            "viktor_oracle_enabled",
            "viktor_proactive_beat_enabled",
            "workspace",
            "business_name",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        return save_agent_ops_settings(filtered)

    def memory_status(self, workspace: Optional[str] = None) -> Dict[str, Any]:
        ops = get_agent_ops_settings()
        ws = workspace or ops.get("workspace", "saas-micro-tools")
        store = AgentMemoryStore()
        semantic_count = 0
        episodic_count = 0
        with store._connect() as conn:
            semantic_count = conn.execute(
                "SELECT COUNT(*) FROM semantic_memory WHERE workspace=?",
                (ws,),
            ).fetchone()[0]
            episodic_count = conn.execute(
                "SELECT COUNT(*) FROM episodic_memory WHERE workspace=?",
                (ws,),
            ).fetchone()[0]
        return {
            "workspace": ws,
            "db_path": str(store.db_path),
            "semantic_count": semantic_count,
            "episodic_count": episodic_count,
            "seed_keys_available": len(SEMANTIC_SEEDS.get(ws, [])),
        }

    def memory_preview(self, workspace: Optional[str] = None, limit: int = 12) -> List[Dict[str, str]]:
        ops = get_agent_ops_settings()
        ws = workspace or ops.get("workspace", "saas-micro-tools")
        store = AgentMemoryStore()
        chunks = store.retrieve(ws, "company governance slack viktor mission", limit=limit)
        return [{"kind": c.kind, "key": c.key, "content": c.content[:300]} for c in chunks]

    def seed_memory(
        self,
        *,
        workspace: Optional[str] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        ops = get_agent_ops_settings()
        ws = workspace or ops.get("workspace", "saas-micro-tools")
        store = AgentMemoryStore()
        workspaces = [ws, "ech0"]
        if overwrite:
            counts = {w: seed_workspace(store, w, overwrite=True) for w in workspaces}
        else:
            counts = ensure_seeded(store, workspaces=workspaces)
        return {"seeded": counts, **self.memory_status(ws)}

    def proactive_schedule(self) -> List[Dict[str, Any]]:
        sched = ProactiveScheduler()
        return [
            {
                "job_id": j.job_id,
                "cron": j.cron,
                "utc_time": f"{j.hour:02d}:{j.minute:02d}",
                "prompt": j.prompt,
                "beat_key": f"viktor-{j.job_id}",
            }
            for j in sched.scheduled
        ]

    async def run_proactive_job(self, job_id: str) -> Dict[str, Any]:
        ops = get_agent_ops_settings()
        workspace = ops.get("workspace", "saas-micro-tools")
        business_name = ops.get("business_name", "SaaS Micro-Tools Empire")

        if _celery_broker_reachable():
            try:
                from .tasks import viktor_proactive_job

                async_result = viktor_proactive_job.delay(
                    job_id=job_id,
                    business_name=business_name,
                    workspace=workspace,
                )
                payload = {
                    "status": "queued",
                    "job_id": job_id,
                    "celery_task_id": async_result.id,
                    "message": "Job queued on Celery worker. Check run history shortly.",
                }
                record_proactive_run(job_id, payload)
                return payload
            except Exception as exc:
                logger.info("Celery queue failed (%s), running proactive job inline", exc)

        return await self._run_proactive_inline(job_id, business_name, workspace)

    async def _run_proactive_inline(
        self, job_id: str, business_name: str, workspace: str
    ) -> Dict[str, Any]:
        from .agent_ops_state import is_viktor_mode_enabled
        from .ech0_viktor_runner import EchoViktorRunner

        self.seed_memory(workspace=workspace, overwrite=False)
        scheduler = ProactiveScheduler()

        async def handler(prompt: str) -> str:
            if is_viktor_mode_enabled():
                runner = EchoViktorRunner(workspace=workspace, business_name=business_name)
                return await runner.handle(
                    prompt,
                    agent_id="proactive-gui",
                    task_id=f"gui-{job_id}",
                )
            from .role_agent_runner import RoleAgentRunner

            runner = RoleAgentRunner(business_name)
            artifact = await runner.run_task(
                role="executive",
                task_id=f"gui-{job_id}",
                description=prompt,
                agent_id="proactive-gui",
            )
            return artifact.get("summary") or artifact.get("content") or str(artifact)

        scheduler.handler = handler
        try:
            output = await scheduler.run_job(job_id)
            payload = {
                "status": "completed",
                "job_id": job_id,
                "output_preview": (output or "")[:500],
            }
            record_proactive_run(job_id, payload)
            return payload
        except Exception as exc:
            payload = {"status": "error", "job_id": job_id, "error": str(exc)}
            record_proactive_run(job_id, payload)
            return payload

    def recent_proactive_runs(self, limit: int = 8) -> List[Dict[str, Any]]:
        return list_proactive_runs(limit=limit)

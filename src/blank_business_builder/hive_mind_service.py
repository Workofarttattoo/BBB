"""
Hive Mind Intel Mesh service — QuLab coordination layer for BBB GUI and API.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from .agent_ops_state import get_agent_ops_settings
from .hive_mind import (
    HiveMind,
    IntentParser,
    KnowledgeGraph,
    Task,
    TaskPriority,
    create_bbb_agents,
)

logger = logging.getLogger(__name__)

_hive_instance: Optional["HiveMindService"] = None


class HiveMindService:
    """Singleton wrapper around QuLab HiveMind for BBB."""

    def __init__(self) -> None:
        self.hive = HiveMind()
        self.knowledge_graph = KnowledgeGraph()
        self.intent_parser = IntentParser()
        self._started = False
        self._lock = asyncio.Lock()
        self._task_log: List[Dict[str, Any]] = []

    async def ensure_started(self) -> None:
        async with self._lock:
            if self._started:
                return
            ops = get_agent_ops_settings()
            create_bbb_agents(
                self.hive,
                business_name=ops.get("business_name", "SaaS Micro-Tools Empire"),
                workspace=ops.get("workspace", "saas-micro-tools"),
                include_lab_agents=False,
            )
            await self.hive.start()
            self._started = True
            logger.info("Hive Mind Intel Mesh started with %s agents", len(self.hive.registry.agents))

    async def stop(self) -> None:
        async with self._lock:
            if self._started:
                await self.hive.stop()
                self._started = False

    def status(self) -> Dict[str, Any]:
        ops = get_agent_ops_settings()
        base = self.hive.get_status()
        base["business_name"] = ops.get("business_name")
        base["workspace"] = ops.get("workspace")
        base["started"] = self._started
        base["recent_tasks"] = self._task_log[-10:]
        base["knowledge_graph_nodes"] = len(self.knowledge_graph.nodes)
        return base

    async def submit_business_task(
        self,
        *,
        description: str,
        role_capability: str,
        priority: str = "normal",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self.ensure_started()
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND,
        }
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=role_capability,
            description=description,
            priority=priority_map.get(priority.lower(), TaskPriority.NORMAL),
            required_capabilities=[role_capability],
            parameters=parameters or {},
        )
        self.hive.submit_task(task)
        entry = {
            "task_id": task_id,
            "description": description,
            "capability": role_capability,
            "priority": priority,
            "status": "submitted",
        }
        self._task_log.append(entry)
        await asyncio.sleep(0.25)
        await self._drain_assigned_tasks()
        return entry

    async def _drain_assigned_tasks(self) -> None:
        """Run assigned tasks on registered Level-6 agent instances."""
        for task_id, task in list(self.hive.distributor.active_tasks.items()):
            agent_id = task.assigned_agent
            if not agent_id:
                continue
            iface = self.hive.registry.get_agent_instance(agent_id)
            if iface is None:
                continue
            try:
                result = await iface.execute_task(task)
                self.hive.distributor.mark_task_completed(task_id, result)
                for entry in self._task_log:
                    if entry.get("task_id") == task_id:
                        entry["status"] = "completed"
                        entry["result_preview"] = str(result.get("summary", result))[:200]
            except Exception as exc:
                self.hive.distributor.mark_task_completed(task_id, None, error=str(exc))
                for entry in self._task_log:
                    if entry.get("task_id") == task_id:
                        entry["status"] = "failed"
                        entry["error"] = str(exc)

    def parse_intent(self, text: str) -> Dict[str, Any]:
        parsed = self.intent_parser.parse(text)
        return {
            "raw_text": text,
            "experiment_type": parsed.experiment_type,
            "materials": parsed.materials,
            "properties": parsed.properties,
            "objectives": [o.name for o in parsed.objectives],
            "constraints": [c.name for c in parsed.constraints],
            "confidence": parsed.confidence,
        }

    def knowledge_topics(self, limit: int = 8) -> List[Dict[str, Any]]:
        summary = self.hive.knowledge.get_summary()
        topics = summary.get("topics", [])[:limit]
        out = []
        for topic in topics:
            latest = self.hive.knowledge.get_latest(topic, n=1)
            out.append({"topic": topic, "latest": latest[0] if latest else None})
        return out

    def sync_from_coordinator(self, coordinator: Any) -> Dict[str, Any]:
        """Push HiveMindCoordinator shared knowledge into QuLab knowledge bus."""
        shared = getattr(coordinator, "shared_knowledge", {}) or {}
        count = 0
        for key, value in shared.items():
            self.hive.knowledge.publish("coordinator_sync", {"key": key, "value": value}, "coordinator")
            count += 1
        return {"synced_entries": count}


def get_hive_mind_service() -> HiveMindService:
    global _hive_instance
    if _hive_instance is None:
        _hive_instance = HiveMindService()
    return _hive_instance

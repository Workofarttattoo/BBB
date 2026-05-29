"""
Agent shift, sleep, and dream (memory consolidation) lifecycle.

Runtime behavior — not model fine-tuning. Supports human-like schedules for agent fleets.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LIFECYCLE_DIR = BBB_ROOT / "logs" / "agent_lifecycle"


class AgentLifecycleState(str, Enum):
    ON_SHIFT = "on_shift"
    SLEEPING = "sleeping"
    DREAMING = "dreaming"
    OFF_DUTY = "off_duty"


@dataclass
class ShiftHandoff:
    role: str
    shift_id: str
    agent_id: str
    open_tasks: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    notes: str = ""
    written_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DreamRecord:
    agent_id: str
    role: str
    shift_id: str
    learnings: List[str] = field(default_factory=list)
    mistakes_to_avoid: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    source_log_paths: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentLifecycleManager:
    """File-backed shift/sleep/dream state per agent instance."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(
            base_dir or os.getenv("BBB_AGENT_LIFECYCLE_DIR", str(DEFAULT_LIFECYCLE_DIR))
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "shifts").mkdir(exist_ok=True)
        (self.base_dir / "dreams").mkdir(exist_ok=True)
        (self.base_dir / "state").mkdir(exist_ok=True)

    def _state_path(self, agent_id: str) -> Path:
        safe = agent_id.replace("/", "_")
        return self.base_dir / "state" / f"{safe}.json"

    def get_state(self, agent_id: str) -> AgentLifecycleState:
        path = self._state_path(agent_id)
        if not path.is_file():
            return AgentLifecycleState.OFF_DUTY
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AgentLifecycleState(data.get("state", AgentLifecycleState.OFF_DUTY.value))
        except (json.JSONDecodeError, ValueError):
            return AgentLifecycleState.OFF_DUTY

    def set_state(
        self,
        agent_id: str,
        state: AgentLifecycleState,
        *,
        role: str = "",
        shift_id: str = "",
    ) -> None:
        payload = {
            "agent_id": agent_id,
            "state": state.value,
            "role": role,
            "shift_id": shift_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._state_path(agent_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def accepts_tasks(self, agent_id: str) -> bool:
        return self.get_state(agent_id) == AgentLifecycleState.ON_SHIFT

    def start_shift(self, agent_id: str, role: str, shift_id: str) -> Optional[ShiftHandoff]:
        self.set_state(agent_id, AgentLifecycleState.ON_SHIFT, role=role, shift_id=shift_id)
        return self.read_handoff(role)

    def end_shift(self, agent_id: str, role: str, shift_id: str, handoff: ShiftHandoff) -> None:
        handoff.written_at = datetime.now(timezone.utc).isoformat()
        path = self.base_dir / "shifts" / role / "last_handoff.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(handoff.to_dict(), indent=2), encoding="utf-8")
        self.set_state(agent_id, AgentLifecycleState.SLEEPING, role=role, shift_id=shift_id)

    def read_handoff(self, role: str) -> Optional[ShiftHandoff]:
        path = self.base_dir / "shifts" / role / "last_handoff.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ShiftHandoff(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    def begin_dream(self, agent_id: str, role: str, shift_id: str) -> None:
        self.set_state(agent_id, AgentLifecycleState.DREAMING, role=role, shift_id=shift_id)

    def save_dream(self, record: DreamRecord) -> Path:
        safe = record.agent_id.replace("/", "_")
        day = record.created_at[:10]
        out_dir = self.base_dir / "dreams" / safe
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{day}.json"
        path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
        self.set_state(record.agent_id, AgentLifecycleState.OFF_DUTY, role=record.role, shift_id=record.shift_id)
        return path

    def consolidate_shift_logs(
        self,
        agent_id: str,
        role: str,
        shift_id: str,
        log_snippets: List[str],
    ) -> DreamRecord:
        """Deterministic dream stub — replace with LLM summarization when local model available."""
        self.begin_dream(agent_id, role, shift_id)
        learnings: List[str] = []
        mistakes: List[str] = []
        questions: List[str] = []
        for line in log_snippets[-20:]:
            low = line.lower()
            if "revise" in low or "blocked" in low:
                mistakes.append(line[:200])
            elif "pass" in low or "approved" in low:
                learnings.append(line[:200])
            elif "?" in line:
                questions.append(line[:200])
        if not learnings and log_snippets:
            learnings.append(f"Processed {len(log_snippets)} log lines this shift.")
        record = DreamRecord(
            agent_id=agent_id,
            role=role,
            shift_id=shift_id,
            learnings=learnings[:3],
            mistakes_to_avoid=mistakes[:1],
            open_questions=questions[:3],
        )
        self.save_dream(record)
        return record

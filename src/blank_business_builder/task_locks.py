"""
Git worktree task locks for Paperclip planner/worker coordination.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LOCK_DIR = BBB_ROOT / "logs" / "task_locks"


@dataclass
class TaskLock:
    issue_id: str
    holder: str
    locked_at: float
    expires_at: float
    lock_type: str = "execute"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskLockStore:
    """File-based locks — one active lock per issue_id."""

    def __init__(self, lock_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        self.lock_dir = Path(lock_dir or os.getenv("BBB_TASK_LOCK_DIR", str(DEFAULT_LOCK_DIR)))
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _path(self, issue_id: str) -> Path:
        safe = issue_id.replace("/", "_")
        return self.lock_dir / f"{safe}.json"

    def acquire(self, issue_id: str, holder: str, lock_type: str = "execute") -> bool:
        now = time.time()
        existing = self.get(issue_id)
        if existing and existing.expires_at > now and existing.holder != holder:
            logger.info(
                "Lock held for issue %s by %s until %s",
                issue_id,
                existing.holder,
                existing.expires_at,
            )
            return False
        lock = TaskLock(
            issue_id=issue_id,
            holder=holder,
            locked_at=now,
            expires_at=now + self.ttl_seconds,
            lock_type=lock_type,
        )
        self._path(issue_id).write_text(json.dumps(lock.to_dict(), indent=2), encoding="utf-8")
        return True

    def release(self, issue_id: str, holder: Optional[str] = None) -> bool:
        existing = self.get(issue_id)
        if not existing:
            return True
        if holder and existing.holder != holder:
            return False
        path = self._path(issue_id)
        if path.is_file():
            path.unlink()
        return True

    def get(self, issue_id: str) -> Optional[TaskLock]:
        path = self._path(issue_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lock = TaskLock(**data)
        except (json.JSONDecodeError, TypeError):
            return None
        if lock.expires_at < time.time():
            path.unlink(missing_ok=True)
            return None
        return lock

"""
Incremental agent memory — working, episodic, semantic (SQLite).

Viktor-style: retrieve relevant facts before each task; compress after completion.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = BBB_ROOT / "logs" / "agent_memory.db"


@dataclass
class MemoryChunk:
    kind: str
    key: str
    content: str
    score: float = 1.0


class AgentMemoryStore:
    """SQLite-backed episodic + semantic memory per agent/workspace."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or os.getenv("BBB_AGENT_MEMORY_DB", str(DEFAULT_DB)))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(workspace, key)
                );
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace TEXT NOT NULL,
                    agent_id TEXT,
                    task_id TEXT,
                    summary TEXT NOT NULL,
                    assumptions TEXT,
                    outcome TEXT,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_episodic_ws ON episodic_memory(workspace, created_at DESC);
                """
            )

    def upsert_semantic(self, workspace: str, key: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO semantic_memory (workspace, key, content, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workspace, key) DO UPDATE SET
                    content=excluded.content,
                    updated_at=excluded.updated_at
                """,
                (workspace, key, content, time.time()),
            )

    def write_episode(
        self,
        workspace: str,
        summary: str,
        *,
        agent_id: str = "",
        task_id: str = "",
        assumptions: Optional[List[str]] = None,
        outcome: str = "success",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO episodic_memory
                (workspace, agent_id, task_id, summary, assumptions, outcome, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace,
                    agent_id,
                    task_id,
                    summary,
                    json.dumps(assumptions or []),
                    outcome,
                    time.time(),
                ),
            )

    def retrieve(self, workspace: str, query: str, limit: int = 8) -> List[MemoryChunk]:
        """Keyword overlap retrieval (upgrade to vectors later)."""
        tokens = {t.lower() for t in query.split() if len(t) > 2}
        chunks: List[MemoryChunk] = []
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT key, content FROM semantic_memory WHERE workspace=?",
                (workspace,),
            ):
                text = f"{row['key']} {row['content']}"
                overlap = sum(1 for t in tokens if t in text.lower())
                if overlap or not tokens:
                    score = overlap / max(len(tokens), 1)
                    chunks.append(MemoryChunk("semantic", row["key"], row["content"], score))
            for row in conn.execute(
                """
                SELECT summary, assumptions FROM episodic_memory
                WHERE workspace=? ORDER BY created_at DESC LIMIT 30
                """,
                (workspace,),
            ):
                text = row["summary"]
                overlap = sum(1 for t in tokens if t in text.lower())
                if overlap or not tokens:
                    score = 0.5 * overlap / max(len(tokens), 1)
                    chunks.append(MemoryChunk("episodic", "episode", text, score))
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:limit]

    def context_block(self, workspace: str, query: str, limit: int = 8) -> str:
        chunks = self.retrieve(workspace, query, limit=limit)
        if not chunks:
            return ""
        lines = ["## Retrieved memory"]
        for c in chunks:
            lines.append(f"- [{c.kind}:{c.key}] {c.content[:400]}")
        return "\n".join(lines)

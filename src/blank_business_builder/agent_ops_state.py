"""
Runtime agent-ops settings persisted in business_state.json (GUI-controlled).

Env vars are defaults; GUI toggles override for the running app and saved state.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings

STATE_FILE = os.getenv("BBB_STATE_FILE", "business_state.json")
AGENT_OPS_KEY = "agent_ops"


def _read_state() -> Dict[str, Any]:
    path = Path(STATE_FILE)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_state(state: Dict[str, Any]) -> None:
    path = Path(STATE_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _env_defaults() -> Dict[str, Any]:
    return {
        "viktor_mode_enabled": settings.VIKTOR_MODE_ENABLED,
        "viktor_strategist_enabled": settings.VIKTOR_STRATEGIST_ENABLED,
        "viktor_oracle_enabled": settings.VIKTOR_ORACLE_ENABLED,
        "viktor_proactive_beat_enabled": settings.VIKTOR_PROACTIVE_BEAT_ENABLED,
        "workspace": settings.DEFAULT_COMPANY_SLUG,
        "business_name": "SaaS Micro-Tools Empire",
    }


def get_agent_ops_settings() -> Dict[str, Any]:
    """Merged env defaults + persisted GUI settings."""
    merged = _env_defaults()
    stored = _read_state().get(AGENT_OPS_KEY, {})
    if isinstance(stored, dict):
        merged.update({k: v for k, v in stored.items() if v is not None})
    merged["memory_db"] = settings.BBB_AGENT_MEMORY_DB
    return merged


def save_agent_ops_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    state = _read_state()
    current = state.get(AGENT_OPS_KEY, {})
    if not isinstance(current, dict):
        current = {}
    current.update(updates)
    state[AGENT_OPS_KEY] = current
    _write_state(state)
    _sync_process_env(current)
    return get_agent_ops_settings()


def _sync_process_env(ops: Dict[str, Any]) -> None:
    """Keep os.environ aligned so Celery workers on same machine pick up if restarted."""
    mapping = {
        "viktor_mode_enabled": "VIKTOR_MODE_ENABLED",
        "viktor_strategist_enabled": "VIKTOR_STRATEGIST_ENABLED",
        "viktor_oracle_enabled": "VIKTOR_ORACLE_ENABLED",
        "viktor_proactive_beat_enabled": "VIKTOR_PROACTIVE_BEAT_ENABLED",
    }
    for key, env_key in mapping.items():
        if key in ops:
            os.environ[env_key] = "true" if ops[key] else "false"


def is_viktor_mode_enabled() -> bool:
    return bool(get_agent_ops_settings().get("viktor_mode_enabled"))


def is_viktor_strategist_enabled() -> bool:
    return bool(get_agent_ops_settings().get("viktor_strategist_enabled", True))


def is_viktor_oracle_enabled() -> bool:
    return bool(get_agent_ops_settings().get("viktor_oracle_enabled", True))


def record_proactive_run(job_id: str, result: Dict[str, Any]) -> None:
    state = _read_state()
    runs = state.get("proactive_runs", [])
    if not isinstance(runs, list):
        runs = []
    runs.insert(
        0,
        {
            "job_id": job_id,
            "status": result.get("status", "unknown"),
            "output_preview": (result.get("output_preview") or "")[:500],
            "error": result.get("error"),
        },
    )
    state["proactive_runs"] = runs[:20]
    _write_state(state)


def list_proactive_runs(limit: int = 10) -> List[Dict[str, Any]]:
    runs = _read_state().get("proactive_runs", [])
    if not isinstance(runs, list):
        return []
    return runs[:limit]

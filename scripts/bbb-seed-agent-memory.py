#!/usr/bin/env python3
"""
Seed default semantic memory for BBB Viktor agents.

Usage:
  PYTHONPATH=src python scripts/bbb-seed-agent-memory.py
  PYTHONPATH=src python scripts/bbb-seed-agent-memory.py --workspace saas-micro-tools --overwrite

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from blank_business_builder.agent_memory import AgentMemoryStore
from blank_business_builder.agent_memory_seed import SEMANTIC_SEEDS, ensure_seeded, seed_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed BBB agent semantic memory")
    parser.add_argument(
        "--workspace",
        action="append",
        dest="workspaces",
        help="Workspace slug (default: saas-micro-tools + ech0)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing keys",
    )
    parser.add_argument("--list", action="store_true", help="List seed keys only")
    args = parser.parse_args()

    if args.list:
        print(json.dumps({k: [x[0] for x in v] for k, v in SEMANTIC_SEEDS.items()}, indent=2))
        return 0

    store = AgentMemoryStore()
    workspaces = args.workspaces or list(SEMANTIC_SEEDS.keys())
    if args.overwrite:
        counts = {
            ws: seed_workspace(store, ws, overwrite=True) for ws in workspaces
        }
    else:
        counts = ensure_seeded(store, workspaces=workspaces)
    print(json.dumps({"seeded": counts, "db": str(store.db_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

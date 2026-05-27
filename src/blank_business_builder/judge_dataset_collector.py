"""
Judge JSONL collector and few-shot example builder.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .company_pack import company_root, judge_domain_for_artifact, load_eval_jsonl, slug_for_business

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_JUDGE_LOG = BBB_ROOT / "logs" / "judge.jsonl"


class JudgeDatasetCollector:
    """Append judge runs and merge CEO decisions into company eval sets."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = Path(log_path or os.getenv("JUDGE_LOG_PATH", str(DEFAULT_JUDGE_LOG)))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_evaluation(
        self,
        *,
        business_name: str,
        artifact_type: str,
        mission: str,
        content: str,
        metadata: Dict[str, Any],
        verdict: str,
        score: float,
        fixes: List[str],
        policy_flags: List[str],
        task_id: Optional[str] = None,
        ceo_decision: Optional[str] = None,
    ) -> None:
        record = {
            "ts": datetime.utcnow().isoformat(),
            "business_name": business_name,
            "company_slug": slug_for_business(business_name),
            "artifact_type": artifact_type,
            "mission": mission,
            "content": content[:8000],
            "metadata": metadata,
            "verdict": verdict,
            "score": score,
            "fixes": fixes,
            "policy_flags": policy_flags,
            "task_id": task_id,
            "ceo_decision": ceo_decision,
        }
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def record_ceo_decision(
        self,
        *,
        business_name: str,
        task_id: str,
        decision: str,
        notes: str = "",
    ) -> None:
        record = {
            "ts": datetime.utcnow().isoformat(),
            "type": "ceo_decision",
            "business_name": business_name,
            "task_id": task_id,
            "decision": decision,
            "notes": notes,
        }
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
        self._maybe_export_to_eval(business_name, artifact_type="lead_batch", limit=500)

    def _maybe_export_to_eval(self, business_name: str, artifact_type: str, limit: int) -> None:
        """When enough labels exist, refresh eval JSONL from log (best-effort)."""
        if not self.log_path.is_file():
            return
        rows: List[Dict[str, Any]] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "ceo_decision":
                continue
            if row.get("verdict"):
                rows.append(row)
        if len(rows) < 5:
            return
        domain = judge_domain_for_artifact(artifact_type)
        eval_path = company_root(business_name) / "eval" / f"judge-{domain}.jsonl"
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        with eval_path.open("w", encoding="utf-8") as fh:
            for row in rows[-limit:]:
                fh.write(
                    json.dumps(
                        {
                            "artifact_type": row.get("artifact_type"),
                            "mission": row.get("mission"),
                            "content": row.get("content"),
                            "metadata": row.get("metadata", {}),
                            "verdict": row.get("verdict"),
                            "score": row.get("score"),
                            "policy_flags": row.get("policy_flags", []),
                        },
                        default=str,
                    )
                    + "\n"
                )

    @staticmethod
    def few_shot_block(business_name: str, artifact_type: str, max_examples: int = 3) -> str:
        domain = judge_domain_for_artifact(artifact_type)
        examples = load_eval_jsonl(business_name, f"judge-{domain}.jsonl", limit=max_examples)
        if not examples:
            return ""
        lines = ["Few-shot examples (match this format):"]
        for ex in examples:
            lines.append(
                f"- artifact={ex.get('artifact_type')} verdict={ex.get('verdict')} "
                f"score={ex.get('score')} flags={ex.get('policy_flags', [])}"
            )
        return "\n".join(lines)

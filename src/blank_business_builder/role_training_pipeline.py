"""
LoRA / Modelfile export pipeline (Phase 2 — after 100+ labels).

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .company_pack import company_root, load_eval_jsonl, slug_for_business

logger = logging.getLogger(__name__)

MIN_LABELS_FOR_LORA = 100


@dataclass
class TrainingExport:
    role_or_judge: str
    example_count: int
    jsonl_path: str
    modelfile_path: str
    ready: bool
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_or_judge": self.role_or_judge,
            "example_count": self.example_count,
            "jsonl_path": self.jsonl_path,
            "modelfile_path": self.modelfile_path,
            "ready": self.ready,
            "message": self.message,
        }


class RoleTrainingPipeline:
    """Export SFT JSONL and Ollama Modelfile when label volume threshold met."""

    def __init__(self, business_name: str, min_labels: int = MIN_LABELS_FOR_LORA):
        self.business_name = business_name
        self.min_labels = min_labels
        self.slug = slug_for_business(business_name)
        self.root = company_root(business_name)

    def _count_jsonl(self, filename: str) -> int:
        path = self.root / "eval" / filename
        if not path.is_file():
            return 0
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    def export_judge_modelfile(
        self,
        domain: str = "sales",
        base_model: str = "qwen3.5:4b",
    ) -> TrainingExport:
        eval_name = f"judge-{domain}.jsonl"
        examples = load_eval_jsonl(self.business_name, eval_name, limit=10000)
        count = len(examples)
        export_dir = self.root / "training" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        sft_path = export_dir / f"sft-judge-{domain}.jsonl"
        modelfile_path = export_dir / f"Modelfile.judge-{domain}"

        with sft_path.open("w", encoding="utf-8") as fh:
            for ex in examples:
                prompt = (
                    f"Mission: {ex.get('mission')}\n"
                    f"Artifact: {ex.get('artifact_type')}\n"
                    f"Content: {ex.get('content')}\n"
                )
                target = json.dumps(
                    {
                        "verdict": ex.get("verdict"),
                        "score": ex.get("score"),
                        "policy_flags": ex.get("policy_flags", []),
                    }
                )
                fh.write(json.dumps({"prompt": prompt, "completion": target}) + "\n")

        modelfile = (
            f"FROM {base_model}\n"
            f"# BBB judge-{domain} — export after {count} labels\n"
            f"PARAMETER temperature 0.1\n"
            f"SYSTEM You are bbb-judge-{domain}. Output JSON verdict only.\n"
        )
        modelfile_path.write_text(modelfile, encoding="utf-8")

        ready = count >= self.min_labels
        msg = (
            f"Ready for ollama create bbb-judge-{domain}:4b -f {modelfile_path}"
            if ready
            else f"Need {self.min_labels - count} more labeled examples (have {count})"
        )
        return TrainingExport(
            role_or_judge=f"judge-{domain}",
            example_count=count,
            jsonl_path=str(sft_path),
            modelfile_path=str(modelfile_path),
            ready=ready,
            message=msg,
        )

    def export_worker_modelfile(
        self,
        role: str = "sales",
        base_model: str = "qwen3.5:4b",
    ) -> TrainingExport:
        eval_name = f"worker-{role}.jsonl"
        examples = load_eval_jsonl(self.business_name, eval_name, limit=10000)
        count = len(examples)
        export_dir = self.root / "training" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        sft_path = export_dir / f"sft-worker-{role}.jsonl"
        modelfile_path = export_dir / f"Modelfile.worker-{role}"

        with sft_path.open("w", encoding="utf-8") as fh:
            for ex in examples:
                fh.write(
                    json.dumps(
                        {
                            "prompt": f"Task: {ex.get('task')}\nInput: {ex.get('input')}",
                            "completion": ex.get("output", ""),
                        }
                    )
                    + "\n"
                )

        modelfile = (
            f"FROM {base_model}\n"
            f"# BBB worker-{role}\n"
            f"PARAMETER temperature 0.3\n"
        )
        modelfile_path.write_text(modelfile, encoding="utf-8")
        ready = count >= self.min_labels
        msg = (
            f"Ready for ollama create bbb-worker-{role}:4b -f {modelfile_path}"
            if ready
            else f"Need {self.min_labels - count} more worker examples (have {count})"
        )
        return TrainingExport(
            role_or_judge=f"worker-{role}",
            example_count=count,
            jsonl_path=str(sft_path),
            modelfile_path=str(modelfile_path),
            ready=ready,
            message=msg,
        )

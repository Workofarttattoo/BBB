#!/usr/bin/env python3
"""
Export BBB training artifacts and create Ollama Modelfiles on your machine.

Usage:
  python scripts/bbb-train-models.py status
  python scripts/bbb-train-models.py export --base qwen3.5:9b
  python scripts/bbb-train-models.py role-modelfiles --base-tag bbb-corporate-base
  python scripts/bbb-train-models.py ollama-create --base qwen3.5:9b

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.blank_business_builder.corporate_training import CorporateTrainingPipeline
from src.blank_business_builder.role_training_pipeline import RoleTrainingPipeline


def cmd_status(_: argparse.Namespace) -> int:
    corp = CorporateTrainingPipeline()
    judge = RoleTrainingPipeline(corp.business_name)
    base = corp.export_corporate_modelfile()
    j_sales = judge.export_judge_modelfile("sales")
    w_sales = judge.export_worker_modelfile("sales")
    print(json.dumps(
        {
            "strategy": "unified_base_plus_role_prompts",
            "corporate_base": base.to_dict(),
            "judge_sales": j_sales.to_dict(),
            "worker_sales": w_sales.to_dict(),
            "recommendation": (
                "1) ollama pull qwen3.5:9b (or your local model)\n"
                "2) python scripts/bbb-train-models.py ollama-create --base qwen3.5:9b\n"
                "3) Set ROLE_WORKER_MODEL=bbb-corporate-base in .env\n"
                "4) Run real tasks; judge logs feed LoRA after 100+ labels"
            ),
        },
        indent=2,
    ))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    corp = CorporateTrainingPipeline()
    corp.export_domain_jsonl()
    export = corp.export_corporate_modelfile(base_model=args.base)
    print(export.message)
    print(f"SFT: {export.jsonl_path}")
    print(f"Modelfile: {export.modelfile_path}")
    return 0


def cmd_role_modelfiles(args: argparse.Namespace) -> int:
    corp = CorporateTrainingPipeline()
    for role in ("sales", "marketer", "support", "saas_builder", "executive", "meta_manager"):
        ex = corp.export_role_modelfile(role, base_tag=args.base_tag)
        print(ex.message)
    return 0


def cmd_ollama_create(args: argparse.Namespace) -> int:
    corp = CorporateTrainingPipeline()
    export = corp.export_corporate_modelfile(base_model=args.base, tag=args.tag)
    if not export.ready:
        print(export.message, file=sys.stderr)
        return 1
    cmd = ["ollama", "create", args.tag, "-f", export.modelfile_path]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=False)
    if args.roles:
        for role in ("sales", "marketer", "support", "saas_builder", "executive", "meta_manager"):
            rf = corp.export_role_modelfile(role, base_tag=args.tag)
            rcmd = ["ollama", "create", f"bbb-{role}", "-f", rf.modelfile_path]
            print("Running:", " ".join(rcmd))
            subprocess.run(rcmd, check=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BBB model training export / Ollama create")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show export readiness and paths").set_defaults(func=cmd_status)

    p_export = sub.add_parser("export", help="Write SFT JSONL + Modelfile.corporate-base")
    p_export.add_argument("--base", default="qwen3.5:9b", help="Ollama base model tag")
    p_export.set_defaults(func=cmd_export)

    p_roles = sub.add_parser("role-modelfiles", help="Modelfiles FROM corporate base + role SKILL")
    p_roles.add_argument("--base-tag", default="bbb-corporate-base")
    p_roles.set_defaults(func=cmd_role_modelfiles)

    p_create = sub.add_parser("ollama-create", help="Run ollama create for corporate base (+ optional roles)")
    p_create.add_argument("--base", default="qwen3.5:9b")
    p_create.add_argument("--tag", default="bbb-corporate-base")
    p_create.add_argument("--roles", action="store_true", help="Also create bbb-{role} tags")
    p_create.set_defaults(func=cmd_ollama_create)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

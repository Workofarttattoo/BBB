"""
Unified corporate-base training: curriculum seeds, SFT JSONL export, Ollama Modelfile.

One trained base + role system prompts (recommended). Optional per-judge LoRA later.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .company_pack import company_root, load_skill, slug_for_business
from .role_training_pipeline import MIN_LABELS_FOR_LORA, TrainingExport

logger = logging.getLogger(__name__)


@dataclass
class CurriculumDomain:
    key: str
    title: str
    seed_examples: List[Dict[str, str]]


class CorporateTrainingPipeline:
    """Build unified SFT dataset and Modelfile for bbb-corporate-base."""

    def __init__(self, business_name: str = "SaaS Micro-Tools Empire"):
        self.business_name = business_name
        self.slug = slug_for_business(business_name)
        self.root = company_root(business_name)
        self.curriculum_path = self.root / "training" / "curriculum.yaml"
        self.export_dir = self.root / "training" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def load_curriculum(self) -> Dict[str, Any]:
        if not self.curriculum_path.is_file():
            return {}
        try:
            import yaml  # type: ignore

            return yaml.safe_load(self.curriculum_path.read_text(encoding="utf-8")) or {}
        except ImportError:
            logger.warning("PyYAML not installed; curriculum.yaml ignored (built-in seeds only)")
            return {}

    def _domain_seeds(self) -> List[CurriculumDomain]:
        """Built-in seed pairs — expand from real task gold outputs over time."""
        seeds: List[CurriculumDomain] = [
            CurriculumDomain(
                "business_operations",
                "Business operations",
                [
                    {
                        "prompt": "Draft a weekly ops summary for a micro-SaaS with 3 products.",
                        "completion": "Use: revenue, active users, support tickets, top blocker, next week priorities. No fabricated metrics.",
                    },
                    {
                        "prompt": "When should an agent escalate to the human CEO?",
                        "completion": "Escalate on: outbound email at scale, spend, legal, first customer contract, repeated judge failures, or policy_flags requiring approval.",
                    },
                ],
            ),
            CurriculumDomain(
                "customer_service",
                "Customer service",
                [
                    {
                        "prompt": "User says billing charged twice. First response?",
                        "completion": "Acknowledge, apologize, ask for invoice ID and last 4 of card, promise investigation within 24h, do not admit fault before verification.",
                    },
                ],
            ),
            CurriculumDomain(
                "software_engineering_phd",
                "Software engineering",
                [
                    {
                        "prompt": "Design a idempotent webhook handler for Stripe.",
                        "completion": "Store event id, verify signature, process in transaction, return 200 on duplicate, structured logging, dead-letter for poison events.",
                    },
                ],
            ),
            CurriculumDomain(
                "systems_design",
                "Systems design",
                [
                    {
                        "prompt": "Tradeoffs: Celery vs synchronous FastAPI for BBB task queue?",
                        "completion": "Celery for long-running agent work, retries, horizontal workers; sync for quick API reads. Redis broker, idempotent tasks, visibility timeout.",
                    },
                ],
            ),
            CurriculumDomain(
                "coding_2026_best_practices",
                "2026 coding practices",
                [
                    {
                        "prompt": "Before opening a PR, what checks run?",
                        "completion": "Run scripts/agent-verify.sh --fast; minimal diff; tests for behavior change; no secrets; update SKILL if integration discovered.",
                    },
                ],
            ),
            CurriculumDomain(
                "communication",
                "Communication",
                [
                    {
                        "prompt": "Rewrite for executive: 'the thing broke lol'",
                        "completion": "Incident: [service] experienced errors affecting [scope]. Mitigation in progress. ETA update in 30 minutes.",
                    },
                ],
            ),
            CurriculumDomain(
                "critical_thinking",
                "Critical thinking",
                [
                    {
                        "prompt": "List assumptions before launching cold email campaign.",
                        "completion": "ICP fit, list source legality, opt-out path, send volume, domain reputation, approval gate, success metric, rollback plan.",
                    },
                ],
            ),
            CurriculumDomain(
                "time_management",
                "Time management",
                [
                    {
                        "prompt": "Agent has 5 tasks and 2 hours. Prioritize how?",
                        "completion": "CEO-blocked first, then revenue-path, then judge-revise loops, then docs. Timebox 25m per task; handoff remainder.",
                    },
                ],
            ),
            CurriculumDomain(
                "autonomous_agent_conduct",
                "Autonomous conduct",
                [
                    {
                        "prompt": "Can you send 500 emails without approval?",
                        "completion": "No. Check enterprise_agent_policy and approval_gates. Batch outbound requires explicit CEO approval.",
                    },
                ],
            ),
            CurriculumDomain(
                "retail_operations",
                "Retail",
                [
                    {
                        "prompt": "Plan a product launch checklist for a $29/mo micro-SaaS.",
                        "completion": "Landing page, pricing, support macros, refund policy, analytics events, launch email (approval gated), monitor first 48h tickets.",
                    },
                ],
            ),
            CurriculumDomain(
                "real_business_practices",
                "Real business",
                [
                    {
                        "prompt": "What belongs in a one-page operating agreement for a solo SaaS?",
                        "completion": "Entity, ownership, decision rights, expense policy, customer data handling, termination — recommend human attorney for final doc.",
                    },
                ],
            ),
            CurriculumDomain(
                "english_professional",
                "Professional English",
                [
                    {
                        "prompt": "Fix grammar: 'We are excited to announcing our new tool.'",
                        "completion": "We are excited to announce our new tool.",
                    },
                ],
            ),
            CurriculumDomain(
                "electrical_engineering_basics",
                "Electrical engineering",
                [
                    {
                        "prompt": "When should an agent defer to a licensed EE?",
                        "completion": "Mains voltage, panel work, compliance (NEC/local), safety-critical hardware — provide concepts only; no wiring instructions without qualified review.",
                    },
                ],
            ),
            CurriculumDomain(
                "devops_and_reliability",
                "DevOps",
                [
                    {
                        "prompt": "Minimum production checklist for a FastAPI + Celery stack.",
                        "completion": "Health checks, structured logs, secrets in env, Redis persistence, worker autoscale, backups, on-call runbook, rate limits.",
                    },
                ],
            ),
            CurriculumDomain(
                "approval_and_compliance",
                "Compliance",
                [
                    {
                        "prompt": "Can agents store customer PII in skill files?",
                        "completion": "No. Skills hold patterns and integration IDs, not personal data. Redact before logging or training export.",
                    },
                ],
            ),
            CurriculumDomain(
                "meditation_stress",
                "Meditation / reset",
                [
                    {
                        "prompt": "You failed judge twice on same artifact. Next step?",
                        "completion": "Pause, re-read mission and SKILL, apply fixes list, if still failing escalate with concise blocker summary.",
                    },
                ],
            ),
            CurriculumDomain(
                "shift_handoffs",
                "Shift handoffs",
                [
                    {
                        "prompt": "End of shift with 2 open tasks — what do you write?",
                        "completion": "Handoff: open task IDs, blockers, what next shift should do first, links to CRM/docs, no outbound until reviewed.",
                    },
                ],
            ),
        ]
        return seeds

    def export_domain_jsonl(self) -> Dict[str, str]:
        paths: Dict[str, str] = {}
        domain_dir = self.export_dir / "domains"
        domain_dir.mkdir(parents=True, exist_ok=True)
        for domain in self._domain_seeds():
            path = domain_dir / f"{domain.key}.jsonl"
            with path.open("w", encoding="utf-8") as fh:
                for ex in domain.seed_examples:
                    fh.write(json.dumps(ex) + "\n")
            paths[domain.key] = str(path)
        return paths

    def export_unified_sft(self, include_worker_eval: bool = True) -> Path:
        """Merge curriculum seeds + approved worker/judge eval into one SFT file."""
        out = self.export_dir / "sft-corporate-base.jsonl"
        lines: List[str] = []
        for domain in self._domain_seeds():
            for ex in domain.seed_examples:
                lines.append(
                    json.dumps(
                        {
                            "domain": domain.key,
                            "prompt": ex["prompt"],
                            "completion": ex["completion"],
                        }
                    )
                )
        if include_worker_eval:
            for name in ("worker-sales.jsonl", "judge-sales.jsonl"):
                eval_path = self.root / "eval" / name
                if eval_path.is_file():
                    for raw in eval_path.read_text(encoding="utf-8").splitlines():
                        if not raw.strip():
                            continue
                        row = json.loads(raw)
                        if "task" in row:
                            lines.append(
                                json.dumps(
                                    {
                                        "domain": "real_ops",
                                        "prompt": f"Task: {row.get('task')}\nInput: {row.get('input', '')}",
                                        "completion": row.get("output", ""),
                                    }
                                )
                            )
                        elif "verdict" in row:
                            lines.append(
                                json.dumps(
                                    {
                                        "domain": "real_judge",
                                        "prompt": f"Judge artifact: {row.get('content', '')[:500]}",
                                        "completion": json.dumps(
                                            {
                                                "verdict": row.get("verdict"),
                                                "score": row.get("score"),
                                            }
                                        ),
                                    }
                                )
                            )
        out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return out

    def build_corporate_system_prompt(self) -> str:
        parts = [
            "You are a BBB corporate agent: professional, accountable, policy-aware.",
            "Never fabricate metrics, URLs, or approvals.",
            load_skill(self.business_name, "agent-ops/SKILL.md") or "",
        ]
        return "\n\n".join(p for p in parts if p.strip())

    def export_corporate_modelfile(
        self,
        base_model: str = "qwen3.5:9b",
        tag: str = "bbb-corporate-base",
    ) -> TrainingExport:
        sft_path = self.export_unified_sft()
        count = sum(1 for _ in sft_path.read_text(encoding="utf-8").splitlines() if _.strip())
        modelfile_path = self.export_dir / "Modelfile.corporate-base"
        modelfile = (
            f"FROM {base_model}\n"
            f"# Unified corporate base — {count} SFT seed lines + eval\n"
            f"PARAMETER temperature 0.25\n"
            f'PARAMETER stop "<|end|>"\n'
            f'SYSTEM """\n{self.build_corporate_system_prompt()}\n"""\n'
        )
        modelfile_path.write_text(modelfile, encoding="utf-8")
        ready = count >= 20
        msg = (
            f"ollama create {tag} -f {modelfile_path}\n"
            f"Then set ROLE_WORKER_MODEL={tag} and use role SKILL.md per instance."
            if ready
            else f"Add more examples (have {count}, want ≥20 for modelfile create)."
        )
        return TrainingExport(
            role_or_judge="corporate-base",
            example_count=count,
            jsonl_path=str(sft_path),
            modelfile_path=str(modelfile_path),
            ready=ready,
            message=msg,
        )

    def role_instance_prompt(self, role: str) -> str:
        """System prompt slice for one instance of the unified base model."""
        skill = load_skill(self.business_name, f"{role}/SKILL.md") or ""
        agent_ops = load_skill(self.business_name, "agent-ops/SKILL.md") or ""
        return (
            f"Role: {role}\n\n"
            f"{self.build_corporate_system_prompt()}\n\n"
            f"--- Role skill ---\n{skill}\n\n"
            f"--- Agent ops ---\n{agent_ops}"
        )

    def export_role_modelfile(self, role: str, base_tag: str = "bbb-corporate-base") -> TrainingExport:
        """Thin Modelfile: FROM corporate base + role-specific SYSTEM."""
        modelfile_path = self.export_dir / f"Modelfile.role-{role}"
        modelfile_path.write_text(
            f"FROM {base_tag}\n"
            f"PARAMETER temperature 0.3\n"
            f'SYSTEM """\n{self.role_instance_prompt(role)}\n"""\n',
            encoding="utf-8",
        )
        return TrainingExport(
            role_or_judge=f"role-{role}",
            example_count=0,
            jsonl_path=str(self.export_dir / "sft-corporate-base.jsonl"),
            modelfile_path=str(modelfile_path),
            ready=True,
            message=f"ollama create bbb-{role} -f {modelfile_path}",
        )

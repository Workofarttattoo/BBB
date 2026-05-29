# BBB Agent Map

Table of contents for agent-first operations (Viktor-inspired harness). Keep this file ~100 lines; link out for detail.

## Company packs

| Slug | Business | Path |
|------|----------|------|
| saas-micro-tools | SaaS Micro-Tools Empire | [companies/saas-micro-tools/](companies/saas-micro-tools/) |

- [COMPANY.md](companies/saas-micro-tools/COMPANY.md) — mission, ICP, tone
- [skills/_index.md](companies/saas-micro-tools/skills/_index.md) — lazy-load skill index
- [eval/](companies/saas-micro-tools/eval/) — judge + worker JSONL datasets

## Agent runtime (Python)

| Module | Purpose |
|--------|---------|
| [role_agent_runner.py](src/blank_business_builder/role_agent_runner.py) | Role task execution + skill/policy inject |
| [company_pack.py](src/blank_business_builder/company_pack.py) | Load company skills and eval sets |
| [auto_judge_loop.py](src/blank_business_builder/auto_judge_loop.py) | Post-worker judge + revise re-queue |
| [judge_service.py](src/blank_business_builder/judge_service.py) | Deterministic + local LLM judge |
| [judge_dataset_collector.py](src/blank_business_builder/judge_dataset_collector.py) | JSONL logging + few-shot |
| [local_model_client.py](src/blank_business_builder/local_model_client.py) | Per-role model routing |
| [middle_manager_loop.py](src/blank_business_builder/middle_manager_loop.py) | Supervisor heartbeat |
| [agent_sandbox.py](src/blank_business_builder/agent_sandbox.py) | Git worktree sandbox |
| [role_training_pipeline.py](src/blank_business_builder/role_training_pipeline.py) | LoRA / Modelfile export (Phase 2) |
| [paperclip_work_source.py](src/blank_business_builder/paperclip_work_source.py) | Paperclip → task queue |
| [task_locks.py](src/blank_business_builder/task_locks.py) | Planner/worker issue locks |

## Config

- [config.py](src/blank_business_builder/config.py) — role model tiers, paths
- [config/enterprise/paperclip_issue_labels.json](config/enterprise/paperclip_issue_labels.json) — label → role routing
- [.env.example](.env.example) — MIDDLE_MANAGER_*, JUDGE_*, ROLE_* model vars

## Scripts

- [scripts/agent-verify.sh](scripts/agent-verify.sh) — fast verify for sandbox PRs (`--fast`)

## Docs

- [docs/agent/DESIGN.md](docs/agent/DESIGN.md) — harness beliefs (OpenAI + Anthropic + Cursor + Viktor)
- [docs/agent/VIKTOR_MODE.md](docs/agent/VIKTOR_MODE.md) — assume-forward + protocol council (Crystalline, Parliament, Tensor, Cascade)
- [docs/deployment/ENTERPRISE_AGENT_STACK.md](docs/deployment/ENTERPRISE_AGENT_STACK.md) — deployment stack

## Paperclip labels (quick reference)

| Label | Behavior |
|-------|----------|
| `bbb:execute` | Worker executes issue to completion |
| `plan:*` | Planner creates child issues only |
| `echo:strategy` | Route to executive / Echo Prime |
| `judge:*` | Review-only judge issues |
| `human:apollo` | Skip autonomous loop (manual GUI) |

## Golden rules

1. Skills before LoRA — enrich `skills/` after every approved task.
2. Deterministic judge checks always win for compliance flags.
3. Outbound email, payments, bulk CRM ingest → approval gates (never bypass).
4. One company pack until G1 stability KPIs met.

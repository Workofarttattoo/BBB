# BBB agent training strategy

## One model + role prompts (recommended)

Train **one corporate base** on shared behavior, then spawn **many instances** with different system prompts and `skills/{role}/SKILL.md`.

| Approach | When to use |
|----------|-------------|
| **Unified base + role Modelfiles** | Default. Same weights; role = SYSTEM + skill + policy. |
| **Per-judge LoRA** | After 100+ labeled pass/fail in `eval/judge-*.jsonl`. |
| **Per-worker LoRA** | Only for sales/marketer after 200+ gold task pairs. |
| **Many full fine-tunes** | Avoid — expensive, hard to maintain, skills bleed between companies. |

PhD-level depth for every domain in one 4B model is **not realistic in weights**. Use:

1. **Corporate base SFT** — conduct, communication, business ops, autonomous policy
2. **Role skills** — lazy-loaded markdown (Viktor)
3. **Cloud / larger model** — executive, architecture, hard coding (tier `csuite`)
4. **RAG / tools** — electrical engineering formulas, docs, calculators on demand

## Curriculum tiers

See `companies/saas-micro-tools/training/curriculum.yaml`:

- **corporate_core** — business, CS, retail, English, communication, thinking, time mgmt
- **technical** — software engineering, systems design, 2026 practices, EE basics
- **wellbeing** — meditation, shifts, sleep, dream (**runtime**, not primary SFT)

## Sleep, dream, shifts

These are **harness features**, not training data:

- `agent_lifecycle.py` — shift handoffs, sleep blocks tasks, dream consolidates logs
- `skills/agent-ops/SKILL.md` — protocols in every agent prompt

Dream = summarize shift → learnings / mistakes / open questions → optional SKILL append after judge approval.

## Commands

```bash
cd BBB
python scripts/bbb-train-models.py status
python scripts/bbb-train-models.py export --base qwen3.5:9b
ollama pull qwen3.5:9b   # or your local model
python scripts/bbb-train-models.py ollama-create --base qwen3.5:9b --roles
```

Set in `.env`:

```
ROLE_WORKER_MODEL=bbb-corporate-base
# or per-role: use bbb-sales, bbb-support, etc. after ollama create
```

## Real LoRA (Phase 2b)

When `logs/judge.jsonl` + eval files exceed 100 examples:

1. Export SFT via `RoleTrainingPipeline.export_judge_modelfile()`
2. Run MLX / Unsloth / HF Jobs on `training/exports/sft-*.jsonl`
3. Register adapter: `ollama create bbb-judge-sales:4b -f Modelfile.judge-sales`

Deterministic judge rules in `judge_service.py` always win over LoRA output.

## What else to add over time

- **Industry packs** — retail vs B2B SaaS eval sets
- **CEO preference log** — approve/reject → SFT completions
- **Integration skills** — auto-append after first API probe
- **Shift schedules** — Celery beat: `start_shift` / `end_shift` / `dream_consolidate`
- **Multimodal** — only if you add vision tools; not required for ops agents

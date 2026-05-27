# Viktor Mode — Proactive Agent Architecture

Maps GetViktor-style "employee" behavior onto BBB + Echo.

## Five pillars

| Pillar | BBB module |
|--------|------------|
| Assume-forward execution | `viktor_execution.py` |
| Incremental memory | `agent_memory.py` |
| Proactive event loop | `proactive_scheduler.py` (+ Celery beat) |
| Execution sandbox | `agent_sandbox.py` (existing) |
| ReAct + reflect | `ViktorExecutor` in `viktor_execution.py` |

## Protocol council

```
User request
    → Memory retrieve
    → Crystalline Intent (internal JSON)
    → [if complex] Strategist: Parliament + Semantic Tensor + Echo Cascade
    → [if planning] Prediction Oracle
    → Viktor ReAct loop
    → Episodic memory write
    → Report (done + assumptions + related notices)
```

## Enable

```bash
export VIKTOR_MODE_ENABLED=true
export VIKTOR_STRATEGIST_ENABLED=true
export VIKTOR_ORACLE_ENABLED=true
export VIKTOR_PROACTIVE_BEAT_ENABLED=true   # default on
```

Echo chat (`ECH0Service.chat`) and `RoleAgentRunner.run_task` use the council automatically.

## Semantic memory seed

```bash
cd BBB && PYTHONPATH=src python scripts/bbb-seed-agent-memory.py
```

Seeds `saas-micro-tools` (15 facts: governance, ICP, Slack env, Viktor policy) and `ech0`. Idempotent — also runs on first ProtocolCouncil init.

## Celery beat (proactive jobs)

| Beat key | UTC | What |
|----------|-----|------|
| `viktor-arxiv-ingest` | 06:00 | Fetch arXiv cs.AI/LG/SE → Viktor invention brief |
| `viktor-daily-ops` | 07:00 | Queue/judge/ops executive summary |

```bash
celery -A blank_business_builder.tasks worker -l info
celery -A blank_business_builder.tasks beat -l info
```

Manual: `viktor_proactive_job.delay(job_id="arxiv-ingest")`

Disable: `VIKTOR_PROACTIVE_BEAT_ENABLED=false`

## Prompt superpowers mapping

| Skill | Agent role |
|-------|------------|
| Crystalline Intent | Goal crystallizer (stage 1) |
| Echo Parliament + Semantic Tensor + Echo Cascade | Strategist (stage 2) |
| Prediction Oracle | Scenario prep (stage 2b) |
| Parallel Pathways | Optional: extend strategist for multi-path |
| Function Cartography | Tool routing in ReAct (future) |

## Training note

Viktor behavior is **harness-first** (prompts + memory + loop). LoRA on judge/worker roles comes after labeled examples in `corporate_training.py`.

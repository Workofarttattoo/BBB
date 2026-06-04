# BBB Agent Harness — Design

Viktor-inspired agent company for **SaaS Micro-Tools Empire** (pilot). Training = skills + eval datasets first; LoRA only after labeled volume.

## Core beliefs

1. **Harness over fine-tune** — Persistent sandbox, lazy skills, and verify scripts beat early LoRA for productivity.
2. **Lazy skills** — `_index.md` one-liners in system prompt; read full `SKILL.md` on demand.
3. **Planners vs workers** — Executives with `plan:*` decompose; workers with `bbb:execute` ship one issue each.
4. **Auto-judge loop** — Every worker artifact passes JudgeService; `revise` re-queues (max 3); `escalate` → approval gates.
5. **Model tiers** — Flash 4B–8B for workers/judges; Qwen 9B middle manager; cloud or 14B+ for C-suite planning.
6. **Deterministic safety** — LoRA/few-shot never overrides hard policy flags (approval, empty leads, etc.).

## Flow

```
CEO criteria → Planner (plan:*) → Workers (+ skills/sandbox)
  → Judge (flash) → revise loop → Middle Manager → Parliament → approval_gates → ship
```

## Company pack layout

```
companies/saas-micro-tools/
├── COMPANY.md
├── policy.json
├── skills/_index.md + role SKILL.md files
├── eval/*.jsonl
└── exec-plans/active/
```

## Integration exploration (Viktor)

When an agent first uses Apollo, Firecrawl, or GitHub, append gotchas to `skills/*/integrations/*.md`.

## References

- OpenAI harness engineering — AGENTS.md as TOC, observability, golden principles
- Anthropic — parallel agents, Ralph loop, task locks
- Cursor — planners/workers/judge; avoid flat peer locks at scale
- Viktor — sandbox + skills + code-as-tool; no customer-data model training

## Phase gates (single company)

| Gate | Metric |
|------|--------|
| G1 | 30d lead→draft→approve→ingest; <20% judge revise rate |
| G2 | 10 sandbox PRs with verify green |
| G3 | Paperclip issues closed with human review |
| G4 | Second company pack (e.g. QuLab) only after G2 |

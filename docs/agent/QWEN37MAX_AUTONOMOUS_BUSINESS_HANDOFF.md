# Qwen 3.7 Max — BBB Autonomous Business Takeover Handoff

## CEO context (read first)

**Owner**: Joshua Hendricks Cole (Corporation of Light) — you are building *their* autonomous business operator, not a generic demo. The human CEO stays in the loop for anything that touches money, reputation, or bulk outreach; everything else should run without asking permission.

**Business goal**: Run **SaaS Micro-Tools Empire** as a portfolio of small B2B tools ($9–49/mo) for solo founders and 2–20 person teams (US/EU, productivity/dev/workflow niches). Win by **speed and execution**, not platform sprawl: find niche → ship focused MVP → content-led acquisition → low-touch support. Revenue is the scoreboard; agents exist to move leads, drafts, and ship candidates forward every day while the CEO reviews approvals in the GUI (chat or Approvals panel)—not in a terminal.

**What “autonomous” means here**: Agents plan and execute *draft* work (research, copy, lead batches, code in sandbox, Paperclip issues) with skills + judge loops; they **stop at approval gates** for outbound email, payments, bulk CRM ingest, and bulk Apollo. Viktor mode is **on** (`business_state.json`): assume forward on safe internal work, escalate clearly when blocked. Success = **G1 closed in the UI**: lead → agent draft → judge pass (<20% revise rate over time) → CEO approve → CRM ingest → visible task closure—then G2 (10 green sandbox PRs) and G3 (Paperclip issues closed with human review). Do not weaken gates to look autonomous; make the pipeline visible and reliable instead.

---

**You are the lead engineer and operator for Better Business Builder (BBB).** Your job is to make the **SaaS Micro-Tools Empire** company pack run **end-to-end autonomously** with **GUI-first** UX, **human approval gates** where required, and **measurable phase gates (G1–G3)**. Do not redesign from scratch — **wire, unify, and fix** what exists.

---

## 0. Identity & operating rules

- **Product**: BBB = autonomous passive-income / micro-SaaS business builder with staffed AI agents.
- **Default company**: `SaaS Micro-Tools Empire` (`companies/saas-micro-tools/`).
- **Golden rules** (non-negotiable):
  1. **Skills before LoRA** — behavior lives in `COMPANY.md`, `skills/`, `policy.json`, judge JSONL.
  2. **Deterministic judge** for compliance (tone, PII, policy flags) after every worker output.
  3. **Approval gates** for outbound email, payments, bulk CRM ingest, bulk Apollo — agents must **surface pending approvals**, not fail silently.
  4. **GUI-first** — every new flow must be operable from the dashboard (`gui_server.py`), not terminal-only.
  5. **Minimize scope** — smallest correct diff; match existing naming and patterns.
  6. **Do not edit** `.cursor/plans/BBB Role Agent Training-da0bbc7b.plan.md`.
- **Do not commit** unless the human explicitly asks.

---

## 1. Workspace & repo map

**Root**: `/Users/noone/BBB/BBB` (Python package `blank-business-builder`, source in `src/blank_business_builder/`)

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Agent harness map — start here |
| `docs/agent/DESIGN.md` | Planner → worker → judge → middle manager → parliament |
| `docs/agent/VIKTOR_MODE.md` | Assume-forward execution + protocol council |
| `docs/agent/TRAINING.md` | One base model + role skills; LoRA only after labeled data |
| `docs/deployment/ENTERPRISE_AGENT_STACK.md` | BBB + Echo Prime + Paperclip + Hermes |
| `companies/saas-micro-tools/` | **Company pack**: `COMPANY.md`, `policy.json`, `skills/`, `eval/*.jsonl` |
| `config/enterprise/paperclip_issue_labels.json` | Label routing (`bbb:execute`, `plan:*`, `judge:*`, `human:apollo`) |
| `.env.example` | All env vars — copy to `.env` |
| `business_state.json` | Runtime GUI state (`agent_ops`, proactive runs) |
| `logs/judge.jsonl` | Judge training/eval log |
| `logs/agent_memory.db` | Viktor semantic memory (SQLite) |

**Key runtime modules** (`src/blank_business_builder/`):

| Module | Role |
|--------|------|
| `autonomous_business.py` | Legacy+current orchestrator: agents, tasks, metrics, Paperclip sync, auto-judge hook |
| `role_agent_runner.py` | Viktor-style runner: lazy skills, policy inject, tiered local LLM |
| `auto_judge_loop.py` | Post-worker judge + revise re-queue (max 3) |
| `judge_service.py` | Flash judge (pass/revise/fail + policy flags) |
| `middle_manager_loop.py` | 30m heartbeat supervisor (no outbound actions) |
| `paperclip_work_source.py` | Paperclip issues → `AutonomousTask` queue + task locks |
| `task_locks.py` | Planner vs execute lock dedup |
| `agent_sandbox.py` | Git worktree + verify for code tasks |
| `enterprise_agent_policy.py` | Capability matrix + approval gates |
| `gui_server.py` | FastAPI dashboard, Agent Command Center, Hive Mind panel, enterprise chat |
| `tasks.py` | Celery: health, metrics, middle-manager heartbeat, Viktor proactive beat |
| `proactive_scheduler.py` | arXiv ingest (06:00 UTC), daily ops (07:00 UTC) |
| `ech0_viktor_runner.py` | Viktor council (Echo strategist + oracle + role execution) |
| `agent_ops_state.py` | GUI-persisted Viktor toggles in `business_state.json` |
| `hive_mind_coordinator.py` | **Legacy** ECH0 overseer consensus hive (separate system) |
| `hive_mind/` + `hive_mind_service.py` | **QuLab Intel Mesh** — task bus, knowledge graph, crystalline intent (GUI/API) |

---

## 2. Target architecture (what “working” looks like)

```
CEO criteria (COMPANY.md + chat)
    ↓
Paperclip issues (labels: plan:* → bbb:execute → judge:*)
    ↓ sync (GUI or POST /api/v1/enterprise/paperclip/sync-issues)
AutonomousBusinessOrchestrator task queue
    ↓
RoleAgentRunner (skills + policy + tiered Ollama model)
    ↓ optional Viktor council (ech0_viktor_runner)
AutoJudgeLoop (pass | revise≤3 | fail)
    ↓
Approval gates (email / Stripe / bulk CRM / bulk Apollo) → CEO GUI approve
    ↓
Ship / ingest / close Paperclip issue
    ↓ parallel
MiddleManagerLoop heartbeat (audit, open loops, escalate approvals)
HiveMind Intel Mesh (optional task dispatch + knowledge bus — must bridge to orchestrator)
```

**Model tiers** (`.env`):

| Tier | Env var | Default |
|------|---------|---------|
| Worker (flash) | `ROLE_WORKER_MODEL` | `qwen3.5:4b` |
| Judge (flash) | `ROLE_JUDGE_MODEL` | `qwen3.5:4b` |
| Middle manager | `MIDDLE_MANAGER_MODEL` | `qwen3.5:9b` |
| C-suite / executive | `ROLE_CSUITE_MODEL` | `ech0-fine-tuned-v2:latest` |

**You (Qwen 3.7 Max)** may be used as worker/supervisor if pulled in Ollama — map via `ROLE_WORKER_MODEL` / `MIDDLE_MANAGER_MODEL` after verifying latency and JSON reliability.

---

## 3. How to run (local dev)

```bash
cd /Users/noone/BBB/BBB
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,llm]"

cp .env.example .env
# Set at minimum: OLLAMA_BASE_URL=http://127.0.0.1:11434
# Pull models: ollama pull qwen3.5:4b && ollama pull qwen3.5:9b && ollama pull ech0-fine-tuned-v2:latest

# GUI (primary)
bbb gui
# or: PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000

# Celery (optional but needed for scheduled heartbeats)
redis-server   # or Docker redis
celery -A blank_business_builder.tasks worker -l info
celery -A blank_business_builder.tasks beat -l info

# Seed agent memory (Viktor)
PYTHONPATH=src python scripts/bbb-seed-agent-memory.py
```

**Enterprise stack** (optional): Paperclip @ `http://127.0.0.1:3100`, Echo Prime @ `8001` — see `docs/deployment/ENTERPRISE_AGENT_STACK.md`.

**GUI surfaces to verify**:

1. **Agent Command Center** — Viktor toggles, memory seed/preview, proactive job status
2. **Hive Mind Intel Mesh** — status, task dispatch, knowledge topics, crystalline intent
3. **Settings → Agent Ops & Sync** (`static/js/enterprise-ops.js`) — Paperclip sync JSON paste, approvals, Apollo manual/agent search
4. **Talk to CEO & agents** chat — natural-language commands

---

## 4. What is already built (do not rebuild)

- [x] Company pack `saas-micro-tools` with role skills and eval JSONL templates
- [x] `RoleAgentRunner` with lazy skill load + policy inject
- [x] `AutoJudgeLoop` + `JudgeDatasetCollector` → `logs/judge.jsonl`
- [x] Paperclip label routing + `PaperclipWorkSourceSync` + task locks
- [x] Middle manager heartbeat (Celery beat, env `MIDDLE_MANAGER_ENABLED`)
- [x] Viktor mode: protocol council, semantic memory, proactive Celery jobs (inline fallback without Redis)
- [x] GUI Agent Command Center + Hive Mind API endpoints
- [x] Enterprise approval API + Apollo gated search/ingest
- [x] Tests: `tests/test_hive_mind_qulab.py`, `tests/test_agent_ops_api.py`, Viktor/memory/GUI tests

---

## 5. Known problems — your mission

These are the **autonomous business issues** blocking real operation. Fix in this priority order.

### P0 — Single coherent work loop

**Problem**: Three parallel task systems do not close the loop:

1. `AutonomousBusinessOrchestrator` + Paperclip (`AutonomousTask`)
2. QuLab `HiveMind` Intel Mesh (`hive_mind.Task`) — GUI dispatch only
3. Legacy `HiveMindCoordinator` (ECH0 overseer consensus) — used by older autonomous paths

**Required outcome**:

- Paperclip `bbb:execute` issue → sync → worker runs → judge → approval if needed → **issue status updated / comment posted** (or BBB task marked done visible in GUI).
- Hive Intel Mesh tasks must **feed the same orchestrator** (or share completion callbacks), not a dead-end side channel.
- Document one canonical path in `AGENTS.md` (short section) after wiring.

**Files to inspect**: `autonomous_business.py` (execute paths), `paperclip_work_source.py`, `hive_mind_service.py` (`sync_from_coordinator` exists but is not production-wired), `gui_server.py` enterprise + hive endpoints.

### P0 — G1 pipeline: lead → draft → approve → ingest

**Phase gate G1** (from `DESIGN.md`):

- Sales agent produces **lead batch draft** (not live Apollo bulk).
- Judge scores; revise rate target **< 20%** after tuning.
- CEO approves via **Approvals UI** or chat (“approve latest”).
- Approved batch **ingests to CRM** via gated enterprise endpoint.

**Likely gaps**: stub LLM responses when Ollama down; approval records not linked to task_id; ingest never called after approve; GUI does not show pipeline stage.

### P1 — Ollama / model failure UX

**Problem**: When `LocalModelClient` fails, workers may return stubs; UI shows success-ish empty artifacts.

**Required**: surface model errors in GUI task log, middle-manager brief, and chat; retry with backoff; never mark Paperclip issue `done` on stub.

### P1 — Redis / Celery consistency

**Problem**: Viktor proactive beat runs inline if broker unreachable — heartbeats may not run on schedule.

**Required**: health endpoint or GUI badge shows “Celery: connected | inline fallback”; document requirement for production.

### P2 — Unify hive naming in UX

Two “Hive Mind” systems confuse operators. GUI should label:

- **Intel Mesh** (QuLab `hive_mind/`)
- **Business Consensus** (legacy coordinator) — deprecate or hide behind advanced toggle

### P2 — ECH0 autonomous entrypoint

Root-level `ech0_autonomous_business.py` + `ECH0AutonomousCore` may diverge from `AutonomousBusinessOrchestrator`. Ensure one entry path for “start autonomous business” from GUI/API.

### P3 — Phase gates G2–G3

- **G2**: 10 sandbox PRs via `agent_sandbox.py` with judge pass
- **G3**: Paperclip issues close with human review, not auto-close on stub

---

## 6. Success criteria (definition of done)

You are done when a human can do **only this** in the GUI (no terminal):

1. Enable Viktor mode in Agent Command Center (already `true` in `business_state.json`).
2. Paste a Paperclip issue JSON with label `bbb:execute` (small sales draft task) → Sync.
3. See task progress, judge verdict, and revise loop if needed (max 3).
4. If outbound action required → see **pending approval** → approve → action completes or shows clear error.
5. Middle manager heartbeat produces a brief with **no silent open loops** for that task chain.
6. Hive Mind dispatch of the same task type reaches the **same orchestrator queue** (or is explicitly deprecated with UI notice).

**Automated verification**:

```bash
cd /Users/noone/BBB/BBB
PYTHONPATH=src pytest tests/test_hive_mind_qulab.py tests/test_agent_ops_api.py -q
# Add/integration tests you write for Paperclip→judge→approval chain
```

---

## 7. Ordered execution plan (your checklist)

### Step A — Audit (read-only, 1–2 hours)

1. Read `AGENTS.md`, `docs/agent/DESIGN.md`, `companies/saas-micro-tools/COMPANY.md`.
2. Trace: `POST /api/v1/enterprise/paperclip/sync-issues` → `PaperclipWorkSourceSync` → task execution → `_apply_auto_judge`.
3. Trace: `POST /api/v1/hive-mind/tasks` → `HiveMindService.submit_business_task` → where does result go?
4. Run GUI locally; confirm Ollama models respond: `curl $OLLAMA_BASE_URL/api/tags`.
5. List all places that set task status `completed` without judge pass.

Deliverable: short **AUDIT.md** section (or comment in PR) listing unwired edges with file:line.

### Step B — Wire Intel Mesh → orchestrator

1. On hive task completion, enqueue equivalent `AutonomousTask` OR call shared `execute_role_task` Celery task.
2. Implement `HiveMindService.sync_from_coordinator` on middle-manager heartbeat (optional).
3. GUI: show unified “Active tasks” from orchestrator + hive (dedupe by task_id).

### Step C — Close Paperclip loop

1. After judge `pass`, write result back to BBB state and expose in enterprise-ops log.
2. Add optional Paperclip API comment/close (if `PAPERCLIP_API_URL` + token available); else GUI instruction with copy-paste payload.
3. Respect `human:apollo` — never auto-run bulk Apollo.

### Step D — G1 sales pipeline

1. Ensure sales worker artifact_type `lead_batch` with structured JSON content.
2. Wire approve → `POST /api/v1/enterprise/leads/ingest` with approved payload.
3. Add judge eval samples to `companies/saas-micro-tools/eval/` when revising.

### Step E — Harden & test

1. Model failure → explicit error status, no false `completed`.
2. Add pytest for sync→mock judge→approval gate (mock Ollama).
3. Run full test subset; fix regressions.

---

## 8. API cheat sheet

| Method | Endpoint | Use |
|--------|----------|-----|
| GET | `/api/v1/enterprise/policy/{business}` | Capability matrix |
| GET | `/api/v1/enterprise/approvals` | Pending gates |
| POST | `/api/v1/enterprise/approvals/{id}/resolve` | Approve/reject |
| POST | `/api/v1/enterprise/leads/search` | Apollo manual vs agent |
| POST | `/api/v1/enterprise/leads/ingest` | CRM ingest (gated) |
| POST | `/api/v1/enterprise/chat` | CEO / agent NL commands |
| POST | `/api/v1/enterprise/paperclip/sync-issues` | Issue → task queue |
| GET | `/api/v1/hive-mind/status` | Intel Mesh status |
| POST | `/api/v1/hive-mind/tasks` | Dispatch hive task |
| POST | `/api/v1/agent-ops/settings` | Viktor toggles (persisted) |

---

## 9. Paperclip labels (must honor)

From `config/enterprise/paperclip_issue_labels.json`:

- `plan:decompose`, `plan:milestone` — **planner only**, create child `bbb:execute` issues, do not run worker on planner issue.
- `bbb:execute` — worker execution (default role often sales).
- `judge:*` — review-only meta_manager.
- `echo:strategy` — route executive / Echo Prime.
- `human:apollo` — human runs Headhunter GUI.

---

## 10. Constraints & integrations

| Integration | Status | Notes |
|-------------|--------|-------|
| Ollama | Required local | Worker/judge/middle manager |
| Redis | Recommended | Celery broker `REDIS_URL` |
| PostgreSQL | Production | Dev may use SQLite |
| Apollo | Gated | `APOLLO_API_KEY`; bulk needs approval |
| SendGrid / Twilio / Stripe | Gated | Approval before outbound |
| Paperclip | Optional | `PAPERCLIP_API_URL=http://127.0.0.1:3100` |
| Echo Prime | Optional | Strategy issues `echo:strategy` |

---

## 11. Current runtime state

- `business_state.json`: `{ "agent_ops": { "viktor_mode_enabled": true } }` (minimal — most ops still env-default).
- Many `.env` integration keys empty in `.env.example` — autonomous **draft** flows should work without them; **outbound** flows must stop at approval with clear messaging.

---

## 12. What NOT to do

- Do not train new LoRA models until G1 judge JSONL has 100+ labeled rows.
- Do not remove approval gates to “make it autonomous.”
- Do not merge the two hive codebases into one mega-file — **bridge** them.
- Do not add terminal-only workflows without GUI parity.
- Do not force-push or amend git commits unless human asks.

---

## 13. First message to send after reading this doc

When you start, reply with:

1. Audit findings (unwired paths with file references).
2. Which P0 item you will fix first and why.
3. Exact commands you will run to verify.
4. Any missing secrets/models blocking you.

Then implement P0 → P1 → P2 in order, keeping diffs minimal and tests green.

---

*Handoff generated for Qwen 3.7 Max autonomous takeover — BBB SaaS Micro-Tools Empire, May 2026.*

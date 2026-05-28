# Viktor-Style Autonomous Operations Guide

## Quick Start

### 1. Start the GUI Dashboard

```bash
cd /Users/noone/BBB/BBB
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000
```

Then open: **http://localhost:8000**

### 2. Enable Viktor Mode

The dashboard loads with Viktor Mode **enabled by default**. You'll see:
- Green "ACTIVE" indicator in header
- Toggle button to disable/enable
- Real-time task queue, approvals, and judge stats

---

## What Makes This Viktor-Style Autonomous

### 1. **Assume Forward Execution Policy**

Agents execute on ambiguity instead of asking for clarification first. When a task is ambiguous:
- Select highest-probability interpretation
- Proceed with execution
- Report assumptions made at the end

**Configured in**: `business_state.json` → `agent_ops.assume_forward`

### 2. **Persistent Incremental Memory**

Viktor maintains state across sessions using:
- **Working memory**: Current task, last N tool calls (in context)
- **Episodic memory**: Compressed summaries in SQLite (`logs/agent_memory.db`)
- **Semantic memory**: Indexed facts about workspace

**Seed memory**: `PYTHONPATH=src python scripts/bbb-seed-agent-memory.py`

### 3. **Proactive Event Loop**

Agents wake themselves up based on:
- **SCHEDULED**: Cron-style (e.g., "Every 6AM, check arXiv")
- **EVENT**: Webhook listener (e.g., "When Paperclip issue opens")
- **THRESHOLD**: Polling loop (e.g., "If revise rate > 20%, alert")

**Celery beat schedule**: See `tasks.py` for proactive scheduler

### 4. **Deterministic Judge Loop**

Every worker output goes through judge evaluation:
- **Pass**: Continue to approval gate or auto-complete
- **Revise**: Re-queue with feedback (max 3 attempts)
- **Fail**: Mark failed, log reason, update stats

**Target**: <20% revise rate over time

### 5. **Approval Gates**

Outbound actions require CEO approval:
- Bulk email/SMS outreach
- Payments (Stripe charges)
- Bulk CRM ingest
- Bulk Apollo searches

**GUI shows**: Pending Approvals panel with approve/reject buttons

---

## GUI Features

### Agent Command Center

| Panel | Purpose |
|-------|---------|
| **Active Tasks** | Real-time queue with status (queued→running→completed/failed) |
| **Pending Approvals** | Actions awaiting CEO decision |
| **Agent Ops Settings** | Viktor mode, assume forward, max revises, schedule |
| **Hive Mind Status** | Intel Mesh operational status |
| **Paperclip Sync** | Paste issue JSON to sync tasks |
| **Chat Interface** | Natural language commands |

### Chat Commands

Type these in the chat box:

- `"approve latest"` - Approve all pending approvals
- `"list tasks"` - Show active tasks summary
- `"viktor enable"` - Enable Viktor mode
- `"viktor disable"` - Disable Viktor mode
- Any natural language question → Echo LLM responds

---

## API Endpoints

### Task Management

| Method | Endpoint | Use |
|--------|----------|-----|
| GET | `/api/v1/enterprise/tasks` | Get active + history |
| POST | `/api/v1/enterprise/paperclip/sync-issues` | Sync Paperclip issues |
| POST | `/api/v1/hive-mind/tasks` | Submit Hive Mind task |
| GET | `/api/v1/hive-mind/status` | Get Intel Mesh status |

### Approvals

| Method | Endpoint | Use |
|--------|----------|-----|
| GET | `/api/v1/enterprise/approvals` | List pending |
| POST | `/api/v1/enterprise/approvals/{id}/resolve` | Approve/reject |

### Settings

| Method | Endpoint | Use |
|--------|----------|-----|
| GET | `/api/v1/agent-ops/settings` | Get Viktor config |
| POST | `/api/v1/agent-ops/settings` | Update config |
| GET | `/api/v1/enterprise/policy/{business}` | Capability matrix |

### Chat

| Method | Endpoint | Use |
|--------|----------|-----|
| POST | `/api/v1/enterprise/chat` | CEO/agent NL commands |

---

## Phase Gates (G1-G3)

### G1: Lead → Draft → Approve → Ingest

**Flow**:
1. Sales agent produces lead batch draft (artifact_type: `lead_batch`)
2. Judge scores; target <20% revise rate
3. CEO approves via GUI Approvals panel or chat ("approve latest")
4. Approved batch ingests to CRM via `/api/v1/enterprise/leads/ingest`

**Verify**:
- Task shows `judge_verdict: pass` in Active Tasks
- Approval appears in Pending Approvals
- After approve, task status → `completed`

### G2: 10 Sandbox PRs

**Flow**:
1. Code tasks run in `agent_sandbox.py` (Git worktree + verify)
2. Judge evaluates each PR candidate
3. 10 consecutive judge passes = G2 complete

**Verify**:
- Check `logs/judge.jsonl` for 10+ pass verdicts on code artifacts

### G3: Paperclip Issues Closed with Human Review

**Flow**:
1. Paperclip issues with `bbb:execute` label sync to task queue
2. Worker executes, judge evaluates
3. Human reviews result before issue closes (no auto-close on stub)

**Verify**:
- Issue status not set to `done` until human confirms
- GUI shows task linked to Paperclip issue number

---

## Paperclip Label Routing

From `config/enterprise/paperclip_issue_labels.json`:

| Label | Behavior |
|-------|----------|
| `plan:decompose`, `plan:milestone` | Planner only — create child `bbb:execute` issues |
| `bbb:execute` | Worker execution (default role: sales) |
| `judge:*` | Review-only meta_manager |
| `echo:strategy` | Route to executive/Echo Prime |
| `human:apollo` | Human runs Headhunter GUI (no auto-run) |

---

## Model Tiers (.env)

```bash
# Worker (flash)
ROLE_WORKER_MODEL=qwen3.5:4b

# Judge (flash)
ROLE_JUDGE_MODEL=qwen3.5:4b

# Middle manager
MIDDLE_MANAGER_MODEL=qwen3.5:9b

# C-suite / executive
ROLE_CSUITE_MODEL=ech0-fine-tuned-v2:latest
```

**Pull models**:
```bash
ollama pull qwen3.5:4b
ollama pull qwen3.5:9b
ollama pull ech0-fine-tuned-v2:latest
```

---

## Troubleshooting

### Ollama Not Responding

```bash
curl http://127.0.0.1:11434/api/tags
```

If no response:
1. Start Ollama: `ollama serve`
2. Pull models: `ollama pull qwen3.5:4b`

### Celery Broker Unreachable

Viktor proactive beat runs inline if Redis unreachable. GUI shows:
- "Celery: connected" or "inline fallback"

**Production requirement**: Run Redis broker

```bash
redis-server
celery -A blank_business_builder.tasks worker -l info
celery -A blank_business_builder.tasks beat -l info
```

### Judge Revise Rate > 20%

Add eval samples to `companies/saas-micro-tools/eval/` JSONL files. Retrain Flash judge after 100+ labeled rows.

---

## Success Criteria

You're done when a human can do **only this** in the GUI:

1. ✅ Enable Viktor mode in Agent Command Center
2. ✅ Paste Paperclip issue JSON with `bbb:execute` label → Sync
3. ✅ See task progress, judge verdict, revise loop
4. ✅ If outbound action required → see pending approval → approve → action completes
5. ✅ Middle manager heartbeat produces brief with no silent open loops
6. ✅ Hive Mind dispatch reaches same orchestrator queue

---

## Architecture Diagram

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
HiveMind Intel Mesh (task dispatch + knowledge bus)
```

---

*Generated for SaaS Micro-Tools Empire — BBB Autonomous Business Takeover*

# BBB Agent Architecture — Viktor-Style Autonomous Execution

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

---

## Overview

BBB uses **Viktor-style autonomous execution** with these key principles:

1. **Assume Forward** — Execute first, report assumptions after
2. **Deterministic Judge** — Every worker output passes compliance check
3. **Revision Loop** — Max 3 revises before human escalation
4. **Approval Gates** — Outbound email, payments, bulk operations require CEO approval
5. **GUI-First** — All flows operable from dashboard, not terminal

---

## Canonical Task Flow (P0)

```
Paperclip Issue (bbb:execute label)
    ↓
PaperclipWorkSourceSync.route_issue()
    ↓
TaskLockManager.acquire_lock() — prevent duplicates
    ↓
AutoJudgeLoop.execute_with_judge(role, task_description)
    ├── RoleAgentRunner.run_role() — worker produces output
    └── JudgeService.evaluate() — pass | revise | fail
        ↓ (if revise, max 3 attempts)
    ↓
EnterpriseAgentPolicy.check_and_request_approval()
    ↓ (if approval required)
CEO approves in GUI → Action executes
    ↓
PaperclipWorkSourceSync.post_comment() + close_issue()
    ↓
MiddleManagerLoop heartbeat audits closure
```

**Hive Mind Intel Mesh** tasks follow the same path via `HiveMindService.sync_from_coordinator()` which enqueues to the same `AutoJudgeLoop`.

---

## Core Components

### 1. RoleAgentRunner (`role_agent_runner.py`)

**Purpose**: Execute role-specific tasks with lazy skill loading

```python
from blank_business_builder.role_agent_runner import RoleAgentRunner

runner = RoleAgentRunner(company_pack="saas-micro-tools")
output = await runner.run_role(
    role="sales",
    task_description="Generate 10 leads for SaaS tools",
    context={}
)
```

**Features**:
- Lazy skill loading from `companies/{pack}/skills/{role}.md`
- Policy injection for compliance
- Tiered LLM models (worker/judge/manager/executive)
- ReAct + Reflection loop

---

### 2. AutoJudgeLoop (`auto_judge_loop.py`)

**Purpose**: Run worker + judge revision cycle

```python
from blank_business_builder.auto_judge_loop import AutoJudgeLoop

judge_loop = AutoJudgeLoop(company_pack="saas-micro-tools", max_revises=3)
result = await judge_loop.execute_with_judge(
    role="sales",
    task_description="Generate 10 leads",
    task_id="task-123"
)

if result.success:
    # Output passed judge, ready for approval
else:
    # Failed after max revises, needs human review
```

**Returns**: `JudgeLoopResult` with:
- `success`: bool
- `final_output`: dict (if passed)
- `total_attempts`: int
- `revision_history`: list of attempts with verdicts
- `error_message`: str (if failed)

---

### 3. JudgeService (`judge_service.py`)

**Purpose**: Deterministic compliance checking

```python
from blank_business_builder.judge_service import JudgeService

judge = JudgeService(company_pack="saas-micro-tools")
verdict = judge.evaluate(agent_output, role="sales")

# verdict.verdict: "pass" | "revise" | "fail"
# verdict.policy_flags: ["pii_detected", "spam_trigger"]
# verdict.suggested_revisions: ["Add unsubscribe mention"]
```

**Checks**:
- PII detection
- Tone analysis
- Spam trigger words
- Compliance (unsubscribe, legal triggers)
- Structured output validation

---

### 4. PaperclipWorkSourceSync (`paperclip_work_source.py`)

**Purpose**: Sync Paperclip issues → task queue

```python
from blank_business_builder.paperclip_work_source import PaperclipWorkSourceSync

sync = PaperclipWorkSourceSync()

# API mode (if PAPERCLIP_API_URL/TOKEN set)
issues = await sync.fetch_issues(label="bbb:execute")

# GUI paste mode (no API)
issues = sync.parse_paste(json_text_from_gui)

# Route to task
for issue in issues:
    task = sync.route_issue(issue)
    if task:
        # Enqueue to AutoJudgeLoop
        pass
```

**Label Routing** (from `config/enterprise/paperclip_issue_labels.json`):
- `plan:decompose` → Planner creates child issues
- `bbb:execute` → Worker execution (default)
- `judge:review` → Meta-manager review only
- `echo:strategy` → Route to Echo Prime
- `human:apollo` → Escalate to human (never auto-execute)

---

### 5. TaskLockManager (`task_locks.py`)

**Purpose**: Prevent duplicate task execution

```python
from blank_business_builder.task_locks import TaskLockManager

locks = TaskLockManager()

# Before executing
if locks.acquire_lock(task_id, "executor", description):
    # Safe to execute
    pass

# Before planner creates child task
if not locks.is_similar_task_locked(child_description):
    # Safe to create
    pass
```

**Features**:
- Automatic expiration (30 min default)
- Hash-based deduplication (catches similar tasks)
- Thread-safe
- Persistent state across restarts

---

### 6. EnterpriseAgentPolicy (`enterprise_agent_policy.py`)

**Purpose**: Capability matrix + approval gates

```python
from blank_business_builder.enterprise_agent_policy import EnterpriseAgentPolicy

policy = EnterpriseAgentPolicy(company_pack="saas-micro-tools")

# Check capability
if policy.can_execute("sales", "email_draft"):
    # Can draft internally

# Check approval requirement
needs_approval = policy.requires_approval(
    "sales", "outbound_email", quantity=10
)

# Create approval request
approval_id = policy.create_approval_request(
    role="sales",
    action="outbound_email",
    description="Send 10 cold emails",
    payload={...}
)

# CEO resolves in GUI
policy.resolve_approval(approval_id, approved=True, resolved_by="ceo")
```

**Approval Gates** (from `policy.json`):
- `outbound_email`: Always requires approval
- `bulk_crm_ingest`: >10 leads requires approval
- `apollo_bulk_search`: >50 leads requires approval
- `stripe_payment`: Any amount requires approval

---

### 7. MiddleManagerLoop (`middle_manager_loop.py`)

**Purpose**: 30-min heartbeat supervision

```python
from blank_business_builder.middle_manager_loop import MiddleManagerLoop

manager = MiddleManagerLoop(company_pack="saas-micro-tools")
brief = await manager.run_heartbeat()

# brief contains:
# - active_tasks: count
# - stuck_tasks: list
# - pending_approvals: count
# - open_loops: list
# - escalations: list
# - judge_stats: dict
# - system_health: dict
```

**Called by**: Celery beat every 30 minutes (or inline fallback)

**Outputs**:
- Saves brief to `logs/manager_briefs.jsonl`
- Updates `business_state.json` with escalations
- Surfaces stuck tasks and pending approvals

---

### 8. AgentSandbox (`agent_sandbox.py`)

**Purpose**: Isolated code execution (G2 phase gate)

```python
from blank_business_builder.agent_sandbox import AgentSandbox

sandbox = AgentSandbox(repo_path="/path/to/repo")
result = await sandbox.execute_code_task(
    task_description="Add /health endpoint to API",
    role="engineer"
)

if result.verified:
    # Tests/lint/build passed, ready for PR (after human review)
    diff = sandbox.get_diff_for_review(result.worktree_path)
```

**Features**:
- Git worktree isolation
- Automatic test/lint/build verification
- Judge evaluates diff before PR
- Never commits to main without approval

---

## Phase Gates

### G1: Lead → Draft → Approve → Ingest

1. Sales agent produces `lead_batch` artifact (draft only)
2. Judge scores; target revise rate < 20%
3. CEO approves via GUI Approvals panel
4. Approved batch ingests to CRM via `/api/v1/enterprise/leads/ingest`

**Files**: `role_agent_runner.py`, `auto_judge_loop.py`, `enterprise_agent_policy.py`

---

### G2: 10 Sandbox PRs

1. Engineer agent writes code in git worktree
2. Runs tests, lint, build automatically
3. Judge evaluates diff quality
4. Human reviews before merge

**Files**: `agent_sandbox.py`, `auto_judge_loop.py`

---

### G3: Paperclip Issues Closed with Human Review

1. Issue labeled `bbb:execute` synced
2. Worker runs, judge passes
3. Result posted as comment
4. Human confirms closure (no auto-close on stub)

**Files**: `paperclip_work_source.py`, `auto_judge_loop.py`

---

## Model Tiers

Configure in `.env`:

```bash
ROLE_WORKER_MODEL=qwen3.5:4b      # Flash worker
ROLE_JUDGE_MODEL=qwen3.5:4b       # Flash judge
MIDDLE_MANAGER_MODEL=qwen3.5:9b   # Supervisor
ROLE_CSUITE_MODEL=ech0-fine-tuned-v2:latest  # Executive
```

**Qwen 3.7 Max** can be used by setting:
```bash
ROLE_WORKER_MODEL=qwen3.7:max
MIDDLE_MANAGER_MODEL=qwen3.7:max
```

Verify with: `curl $OLLAMA_BASE_URL/api/tags`

---

## GUI Integration

All flows exposed via `gui_server.py`:

1. **Agent Command Center** (`/gui/agent-ops`)
   - Viktor mode toggle
   - Memory seed/preview
   - Proactive job status

2. **Approvals Panel** (`/gui/approvals`)
   - Pending approval requests
   - Approve/reject buttons

3. **Paperclip Sync** (`/gui/enterprise-ops`)
   - JSON paste input
   - Sync button
   - Task progress log

4. **Chat** (`/gui/chat`)
   - Natural language commands
   - "approve latest", "show pending", etc.

---

## Testing

```bash
cd /Users/noone/BBB/BBB
PYTHONPATH=src pytest tests/test_hive_mind_qulab.py tests/test_agent_ops_api.py -q

# Add integration test for Paperclip→judge→approval chain
PYTHONPATH=src pytest tests/test_paperclip_judge_chain.py -v
```

---

## Troubleshooting

### Ollama Unavailable

- GUI shows "Model Error" badge
- Tasks return explicit error status (not false `completed`)
- Middle manager brief includes `ollama_available: false`

### Celery Broker Down

- Viktor proactive beat runs inline fallback
- GUI shows "Celery: inline fallback" badge
- Heartbeats may be delayed

### Paperclip API Not Configured

- Use GUI paste mode (copy issue JSON, paste in Enterprise Ops)
- `PAPERCLIP_API_URL` and `PAPERCLIP_API_TOKEN` optional

---

## Success Metrics

- **Revise rate**: < 20% over time (tracked in `logs/judge.jsonl`)
- **Approval rate**: > 70% first submission (CEO GUI)
- **Task completion**: Visible closure in GUI, not terminal
- **No silent failures**: All errors surfaced in brief/chat

---

*Document generated for BBB Viktor-Style Autonomous Takeover — SaaS Micro-Tools Empire, May 2026.*

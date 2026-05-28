# SaaS Micro-Tools Empire — Company Pack

**Owner**: Joshua Hendricks Cole (Corporation of Light)  
**Business Model**: Portfolio of small B2B tools ($9–49/mo) for solo founders and 2–20 person teams  
**Target Market**: US/EU, productivity/dev/workflow niches  
**Strategy**: Win by speed and execution — find niche → ship focused MVP → content-led acquisition → low-touch support

---

## Operating Principles

1. **Skills before LoRA** — behavior lives in `COMPANY.md`, `skills/`, `policy.json`, judge JSONL
2. **Deterministic judge** for compliance (tone, PII, policy flags) after every worker output
3. **Approval gates** for outbound email, payments, bulk CRM ingest, bulk Apollo — agents must surface pending approvals
4. **GUI-first** — every new flow must be operable from the dashboard, not terminal-only
5. **Minimize scope** — smallest correct diff; match existing naming and patterns
6. **Viktor mode ON** — assume forward on safe internal work, escalate clearly when blocked

---

## Phase Gates

### G1: Lead → Draft → Approve → Ingest
- Sales agent produces lead batch draft (not live Apollo bulk)
- Judge scores; revise rate target < 20% after tuning
- CEO approves via Approvals UI or chat ("approve latest")
- Approved batch ingests to CRM via gated enterprise endpoint

### G2: 10 Sandbox PRs
- Code tasks produce Git worktree + verify via `agent_sandbox.py`
- Judge pass required before PR creation
- Human review before merge

### G3: Paperclip Issues Closed with Human Review
- No auto-close on stub
- Human confirms closure or reopens with feedback

---

## Role Skills Location

Role skills are in `skills/` directory:
- `sales.md` — cold outreach, lead qualification, email drafting
- `engineer.md` — MVP development, bug fixes, refactoring
- `marketer.md` — content creation, SEO, social media
- `support.md` — customer service, retention, onboarding
- `researcher.md` — market analysis, competitor intel, arXiv ingestion

Each skill file contains:
- Role description
- Task examples
- Output format requirements
- Policy constraints

---

## Evaluation Datasets

Judge eval datasets in `eval/`:
- `sales_lead_batch.jsonl` — lead batch scoring samples
- `code_pr.jsonl` — code quality evaluation
- `email_draft.jsonl` — tone and compliance checks
- `content_piece.jsonl` — marketing content quality

Format:
```jsonl
{"input": "...", "expected_verdict": "pass|revise|fail", "policy_flags": [], "notes": "..."}
```

---

## Runtime Configuration

See `policy.json` for capability matrix and approval gates.

Models (via `.env`):
- Worker (flash): `ROLE_WORKER_MODEL=qwen3.5:4b`
- Judge (flash): `ROLE_JUDGE_MODEL=qwen3.5:4b`
- Middle manager: `MIDDLE_MANAGER_MODEL=qwen3.5:9b`
- C-suite / executive: `ROLE_CSUITE_MODEL=ech0-fine-tuned-v2:latest`

---

## Success Metrics

- Revenue is the scoreboard
- Agents exist to move leads, drafts, and ship candidates forward every day
- CEO reviews approvals in GUI (chat or Approvals panel) — not in terminal
- Target: < 20% revise rate over time for judge loop
- G1 closed in UI: lead → agent draft → judge pass → CEO approve → CRM ingest → visible task closure

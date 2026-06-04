# Enterprise Agent Stack (BBB + Echo Prime + Paperclip + Hermes)

Deploy the control plane and execution plane separately on a VPS.

## Architecture

| Service | Port (localhost) | Role |
|---------|------------------|------|
| BBB API | 8000 | Business logic, approvals, Apollo GUI, Celery |
| Echo Prime | 8001 | Reasoning (`/api/v1/echo-prime`) |
| Paperclip | 3100 | Org chart, issues, heartbeats, budgets |

Hermes runs **on the host or in Paperclip's adapter process** as `hermes_local` with API keys — not inside the BBB container.

## Quick start

```bash
cp .env.production.example .env.production
# Set: ECH0_LLM_API_KEY, DATABASE_PASSWORD, BBB_INTERNAL_API_TOKEN

docker compose -f docker-compose.yml -f docker-compose.enterprise.yml up -d --build
docker compose exec api alembic upgrade head
```

## Nginx (optional)

- `https://bbb.aios.is/` → `127.0.0.1:8000`
- `https://ops.bbb.aios.is/` → `127.0.0.1:3100` (Paperclip UI)

## Hermes MCP routing

1. Install: `pip install hermes-agent` and register `hermes-paperclip-adapter` in Paperclip.
2. Copy [`config/enterprise/hermes_mcp_servers.example.yaml`](../../config/enterprise/hermes_mcp_servers.example.yaml) into `~/.hermes/config.yaml`.
3. Use Paperclip issue labels per [`config/enterprise/paperclip_issue_labels.json`](../../config/enterprise/paperclip_issue_labels.json).

## BBB enterprise API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/enterprise/policy/{business}` | Capability matrix |
| `GET /api/v1/enterprise/approvals` | Pending gates |
| `POST /api/v1/enterprise/approvals/{id}/resolve` | Approve/reject |
| `POST /api/v1/enterprise/leads/search` | Apollo manual vs agent |
| `POST /api/v1/enterprise/leads/ingest` | CRM ingest (gated) |
| `POST /api/v1/enterprise/chat` | Natural-language CEO / agent commands |
| `POST /api/v1/enterprise/paperclip/sync-issues` | Sync issues → task queue |
| `GET /api/v1/enterprise/routing/labels` | Label routing map |

## CEO first task (reliable path)

1. Paperclip onboarding: `hermes_local` CEO, API keys on VPS.
2. First issue label: `bbb:execute`, small scope.
3. Sync: `POST /api/v1/enterprise/paperclip/sync-issues` with issue payload.
4. Approve outbound actions via `/api/v1/enterprise/approvals` before email/Stripe/Apollo bulk.

## Apollo toolbox

- **Manual**: BBB GUI Headhunter or `POST /api/v1/enterprise/leads/search` with `"mode": "manual"`.
- **Agent**: same endpoint with `"mode": "agent"` after policy allows and approval if bulk.

## Dashboard GUI (no terminal)

BBB main dashboard → **Settings** → **Agent Ops & Sync** (`static/js/enterprise-ops.js`):

- **Sync fields**: business template name, Paperclip URL, Apollo criteria (saved in browser localStorage).
- **Buttons**: view policy, routing labels, MCP manifest, Echo health, open Paperclip, manual/agent lead search, ingest to CRM, refresh/approve/reject approvals, sync Paperclip issues (paste JSON), clear output log.

For Paperclip sync: export or copy issues from Paperclip, paste into the JSON box, click **Sync Paperclip issues**.

## Natural-language command center

Use the floating **Talk to CEO & agents** chat (bottom-right of the dashboard) or `POST /api/v1/enterprise/chat`:

- "What needs my approval?"
- "Approve the latest request"
- "Find 5 SaaS founders in the US"
- "CEO: analyze why sales pipeline stalled"
- "Tell marketing to draft a launch email"
- "Add those leads to the CRM"

No terminal commands or slash syntax — plain English routes to enterprise ops and queues tasks for the CEO and staffed agents.

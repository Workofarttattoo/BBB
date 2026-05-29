# BBB Enterprise Leads API

## Endpoints

- `POST /api/v1/enterprise/leads/search` — Apollo manual or agent mode
- `POST /api/v1/enterprise/leads/ingest` — CRM ingest (gated)

## Headers

- `Authorization: Bearer <BBB_INTERNAL_API_TOKEN>` when configured

## Ingest payload

Provide judged lead batch + `business_name`: `SaaS Micro-Tools Empire`

# Apollo — SaaS Micro-Tools Empire

## Mode

- **Manual**: CEO uses BBB Headhunter GUI or `POST /api/v1/enterprise/leads/search` with `"mode": "manual"`
- **Agent**: same endpoint with `"mode": "agent"` only after policy allows + approval if bulk

## Search criteria template

```json
{
  "mode": "manual",
  "criteria": {
    "titles": ["Founder", "CEO", "Head of Product"],
    "industries": ["Software", "Internet"],
    "locations": ["United States"]
  },
  "limit": 25
}
```

## Gotchas

- Bulk searches trigger approval gates
- Never store API keys in artifacts; use env on server

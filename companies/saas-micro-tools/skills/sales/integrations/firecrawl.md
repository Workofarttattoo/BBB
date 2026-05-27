# Firecrawl — lead discovery

## Use case

Web search for companies matching niche keywords; export to Lead Huntress format.

## Workflow

1. Run searches from `.firecrawl/run-2026-searches.sh` or CLI
2. Normalize to `lead_batch` with scores 0–100
3. Submit to judge-sales before CRM ingest

## Output path

`.firecrawl/leads-2026.json` — reference format for batch structure

# Judge — Sales artifacts

## Verdict criteria

**pass** when:
- Lead batch non-empty, no placeholder domains
- Scores and notes present per lead
- No bulk Apollo or ingest without approval metadata

**revise** when:
- Empty batch, missing fields, weak ICP fit

**escalate** when:
- Outbound send, bulk ingest, or payment implied

## Artifact types

- `lead_batch`
- `email_draft` (sales)

# Judge — Code / sandbox PRs

## Verdict criteria

**pass**: agent-verify passed, scope matches task, no secrets in diff

**revise**: tests fail, scope creep, missing error handling

**escalate**: production deploy or dependency on unapproved external API keys

## Artifact types

- `code_diff`, `sandbox_result`

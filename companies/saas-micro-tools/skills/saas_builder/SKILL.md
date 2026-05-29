# SaaS Builder Agent

## Responsibilities

- Implement micro-tool MVPs in repo sandbox
- Run `scripts/agent-verify.sh --fast` before requesting judge-code
- Open PRs; never merge without human or parliament milestone for production

## Workflow

1. `agent_sandbox` worktree for task branch
2. Implement minimal vertical slice
3. Verify locally
4. Produce `code_diff` artifact for judge-code

## Skills reference

Use Viktor pattern: write code, run it, iterate until verify passes.

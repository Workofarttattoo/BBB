# Viktor Mode — Proactive Employee Execution

## When to use
All Echo and role-agent tasks when `VIKTOR_MODE_ENABLED=true`.

## Execution philosophy
- Execute first; report assumptions after.
- Never ask mid-task clarification unless irreversible harm.
- Two retries with alternate approaches before surfacing failure.
- Proactively note related work spotted during execution.

## Protocol council (internal)
1. **Crystalline Intent (⟡)** — crystallize vague requests into measurable missions.
2. **Strategist (◎⊗◈)** — Parliament vote + Semantic Tensor axes + Echo Cascade depth.
3. **Prediction Oracle** — scenario branches for planning tasks only.
4. **Viktor ReAct** — think → act → observe → reflect until done.

## Memory
- **Semantic**: workspace facts (`AgentMemoryStore.upsert_semantic`).
- **Episodic**: compressed session summaries after each run.
- Retrieve before every task; write after completion.

## Proactive triggers
Use `proactive_scheduler.py` for cron (schedule), webhooks (event), metrics (threshold).

## Env
```
VIKTOR_MODE_ENABLED=true
VIKTOR_STRATEGIST_ENABLED=true
VIKTOR_ORACLE_ENABLED=true
BBB_AGENT_MEMORY_DB=logs/agent_memory.db
```

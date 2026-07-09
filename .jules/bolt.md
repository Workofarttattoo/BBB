## 2025-05-27 - Expert System Optimization
**Learning:** Found a missing class definition (`ChemistryExpert` etc.) in `expert_system.py` that caused runtime errors, masked by lack of test coverage for that specific path. Also realized that querying multiple specialized experts individually triggers redundant vector embedding computations.
**Action:** Always verify that referenced classes exist, even if imports succeed. Use global vector search to identify domain first, then query specific expert to avoid N+1 problem.

## 2025-05-27 - Task Dependency Optimization
**Learning:** Nested loops for dependency checking in task queues can become a bottleneck (O(N^2)). Python's `any()` inside `all()` generator expressions is elegant but slow for large N.
**Action:** Pre-compute lookup sets (e.g., `completed_task_ids`) to reduce complexity to O(N).

## 2025-05-27 - Task Queue Management
**Learning:** Task status iteration can be brittle. `if task.status != TaskStatus.PENDING: continue` incorrectly ignored `BLOCKED` tasks forever, leading to tasks never being retried even if dependencies were met.
**Action:** When managing stateful queues, explicitly handle all relevant states (e.g., `PENDING` and `BLOCKED`) and consider using a separate data structure (like `pending_tasks` deque) for active items to avoid O(N) scans of historical data.

## 2025-05-27 - ChromaDB Parallel Search
**Learning:** `ChromaDB` (and potentially other vector stores) executes collection queries serially if iterating domains in Python. This is an IO-bound operation that blocks even in `asyncio` executors unless explicitly threaded.
**Action:** Use `ThreadPoolExecutor` inside synchronous IO-bound methods that iterate over multiple resources (like collections) to parallelize latency.
## 2026-03-03 - Optimize AutonomousBusinessOrchestrator Metrics Gathering
**Learning:** Found O(N) list comprehensions being used to calculate task statuses in `get_metrics_dashboard`, `_report_progress`, and `_check_bottlenecks` by iterating over the unbounded `task_queue`. This causes measurable event loop blocking as the business runs.
**Action:** Centralized task status updates into `_set_task_status` which maintains an O(1) `task_status_counts` dictionary, eliminating the need to iterate over history.

## 2026-03-04 - Optimize WebSocket Metrics Gathering
**Learning:** In `_get_business_metrics_sync` (used heavily by periodic websocket connections), multiple `func.sum(case(...))` clauses within a single SQLAlchemy `.query()` can be slow and put unnecessary load on the DB engine due to table scanning. It's an anti-pattern when pulling segmented aggregates.
**Action:** When gathering status counts across an entire associated table, use a much more efficient `GROUP BY` query (`group_by(AgentTask.status)`) combined with a simple Python iteration mapping the output. This greatly mitigates event loop blocking risks from synchronous IO delays under load.
## 2025-05-27 - Fast String Matching Optimization
**Learning:** Python's `any()` function combined with a generator expression introduces significant overhead for simple string containment checks due to generator setup and function calls. When placed inside hot loops or tightly processing queues, this overhead compounds and creates micro-bottlenecks.
**Action:** Replace `any(kw in text for kw in [...]` with explicit, short-circuiting nested `for` loops and extract the inline lists to module-level constant tuples. This provides a ~3.5x speedup and avoids redundant memory allocations inside the hot path.

## 2025-05-27 - Fast String Matching Optimization Re-eval
**Learning:** Found that unrolling `any()` into complex, deeply nested imperative `for` loops explicitly degrades maintainability and violates the persona rule against unreadable micro-optimizations.
**Action:** Extract inline lists into module-level constant tuples to save memory allocations, but retain the clean and idiomatic `any(kw in string for kw in CONSTANT_TUPLE)` expression instead of breaking it down into raw loops, striking the right balance between performance and readability.

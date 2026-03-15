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

## 2026-03-04 - Optimize SmartLeadScorer Interaction Loop
**Learning:** Found O(4N) generator expressions iterating over the `interactions` list to calculate event counts. This can become a bottleneck for leads with extensive history.
**Action:** Replaced generators with a single O(N) loop iterating over `interactions` to tally all event counts simultaneously, eliminating redundant loops.

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

## 2026-04-10 - O(N) to O(1) Dashboard Metric Calculations in AutonomousBusinessOrchestrator
**Learning:** Generating the user dashboard required computing the count of tasks in various states (Pending, Completed, Failed). Originally, this was done via multiple O(N) list comprehensions over the entire `task_queue` every time the dashboard was requested. As the autonomous business generated thousands of tasks, this blocked the event loop and caused unacceptable latency.
**Action:** Centralized all state mutations into a `_set_task_status` method. This method updates an internal `task_status_counts` dictionary in O(1) time whenever a state transition occurs. The dashboard now returns these pre-computed metrics instantly.

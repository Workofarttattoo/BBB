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

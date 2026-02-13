## 2025-02-18 - Synchronous Blocking in Async Code
**Learning:** `asyncio.gather` does not parallelize tasks if the underlying calls are synchronous (blocking).
**Action:** Always wrap synchronous I/O or CPU-bound operations in `loop.run_in_executor` when calling them from `async` functions to enable true concurrency.

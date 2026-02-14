## 2026-02-14 - Python Generator Performance
**Learning:** `any(...)` over a list of 5000 items is fast (milliseconds) but doing it repeatedly (N times) leads to quadratic behavior. Replacing O(N) lookup with O(1) set lookup is a massive win for orchestrators.
**Action:** Always use sets for ID lookups in tight loops, especially for dependency resolution.

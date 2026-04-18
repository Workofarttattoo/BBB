1. **Optimize `manage_marketing_campaigns` in `src/blank_business_builder/level6_agent.py`**
   - Currently, it fetches all active businesses and iterates over them, making an N+1 database query in `_needs_marketing_campaign` to check if a marketing campaign was created in the last 30 days.
   - I will replace this N+1 query loop with a single `LEFT OUTER JOIN` and `GROUP BY` query to efficiently fetch all businesses without recent campaigns in one shot.
2. **Verify changes to `src/blank_business_builder/level6_agent.py`**
   - Run `python -m py_compile src/blank_business_builder/level6_agent.py` to ensure syntax is correct.
3. **Update `_map_task_to_domain` in `src/blank_business_builder/expert_integration.py`**
   - The current implementation uses sequential `any()` keyword searches which is inefficient O(N*M).
   - I will optimize it by defining a module-level `DOMAIN_KEYWORD_MAPPING` constant and using a short-circuiting nested loop, achieving significant performance gains.
4. **Verify changes to `src/blank_business_builder/expert_integration.py`**
   - Run `python -m py_compile src/blank_business_builder/expert_integration.py` to ensure syntax is correct.
5. **Run Tests**
   - Run `PYTHONPATH=src python -m pytest tests/test_expert_integration.py` to ensure `expert_integration.py` changes are correct and haven't introduced regressions. Since there is no `test_level6_agent.py`, the compilation test in Step 2 is the primary test for that file.
6. **Complete pre-commit steps**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
7. **Create PR & Submit**
   - Use `run_in_bash_session` to execute `git checkout -b bolt-optimizations`, `git add .`, `git commit -m "⚡ Bolt: N+1 queries & O(N) optimizations"`, and `gh pr create --title "⚡ Bolt: N+1 queries & O(N) optimizations" --body "Performance optimization"` to create a PR.
   - Call the `submit` tool to finish.

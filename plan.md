1. **Analyze `_needs_marketing_campaign` in `src/blank_business_builder/level6_agent.py`:**
    - Currently, `_needs_marketing_campaign` issues a database query for each business to count `MarketingCampaign`s within the last 30 days. This creates an N+1 query problem when iterating over all businesses in `manage_marketing_campaigns`.
2. **Optimize `manage_marketing_campaigns`:**
    - I will pre-fetch the count of recent campaigns for all relevant businesses at once before the loop using `group_by`.
    - I'll collect the IDs of active businesses and perform a single grouped query to get campaign counts.
    - I'll pass the pre-calculated count to `_needs_marketing_campaign` or adjust the logic to avoid querying inside the loop.
3. **Analyze `_needs_onboarding` in `src/blank_business_builder/level6_agent.py`:**
    - Currently, `_needs_onboarding` uses `user.businesses`. This relies on lazy loading, which creates an N+1 query problem inside the `manage_customer_lifecycle` loop.
    - `manage_customer_lifecycle` already pre-fetches `business_counts`. I can pass this count to `_needs_onboarding` instead of checking `user.businesses`.
4. **Implement fixes using `replace_with_git_merge_diff`:**
    - Update `manage_marketing_campaigns` and `_needs_marketing_campaign` in `src/blank_business_builder/level6_agent.py` to use a bulk query.
    - Update `manage_customer_lifecycle` and `_needs_onboarding` in `src/blank_business_builder/level6_agent.py` to use the already pre-fetched `business_counts`.
5. **Verify changes:**
    - View changes with `git diff`.
    - Run my test script to ensure `manage_marketing_campaigns` functions without error and doesn't hit the N+1.
6. **Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.**
7. **Create PR:**
    - Title: "⚡ Bolt: Fix N+1 queries in Level6Agent loops"
    - Description:
        - 💡 What: Fixed N+1 queries in `manage_marketing_campaigns` and `manage_customer_lifecycle`.
        - 🎯 Why: Iterating over objects and performing DB queries or lazy loads inside loops degrades performance with large numbers of users/businesses.
        - 📊 Impact: Significantly reduces database queries during autonomous loops, changing O(N) queries to O(1) bulk queries.
        - 🔬 Measurement: Observe DB query logs during Level-6-Agent execution; verify fewer queries for active users and businesses.
    - Journal: Append learning about implicit N+1 queries via lazy loading to `.jules/bolt.md`.

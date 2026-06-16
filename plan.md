1. **Refactor `manage_marketing_campaigns` to use pre-fetching (IN clause)**
   - Extract `business_ids` from the fetched active businesses.
   - Run a single query to count recent marketing campaigns for these businesses using `Business.id.in_(business_ids)` and `group_by(MarketingCampaign.business_id)`.
   - Store the result in a dictionary mapping `business_id` to count.
   - Check the pre-fetched count in the loop directly and bypass `_needs_marketing_campaign`.
   - This changes an O(N) database query pattern to an O(1) query pattern inside the loop, optimizing DB usage and preventing event loop blocking.
   - I will use `replace_with_git_merge_diff` to modify `manage_marketing_campaigns`.
   - Verify the changes using `git diff`.

2. **Replace deprecated `datetime.utcnow()` with timezone-aware `datetime.now(timezone.utc).replace(tzinfo=None)`**
   - In `level6_agent.py`, replace all instances of `datetime.utcnow()` with the timezone-aware alternative to fix deprecation warnings and align with Python 3.12 best practices.
   - I will use `sed` to insert the `from datetime import timezone` import.
   - I will use `sed` to replace `datetime.utcnow()` with `datetime.now(timezone.utc).replace(tzinfo=None)`.
   - Verify the changes using `git diff`.

3. **Add Bolt Journal Entry**
   - Record the learning about N+1 query patterns in autonomous loops and timezone-aware datetimes in `.jules/bolt.md` using `run_in_bash_session`.
   - Verify using `cat .jules/bolt.md`.

4. **Create PR Body**
   - Generate `pr_body.txt` with Bolt's specific formatting using `run_in_bash_session`.
   - Verify using `cat pr_body.txt`.

5. **Run relevant tests**
   - Execute `pytest tests/test_autonomous_agents.py` to ensure core agent functionality isn't broken.

6. **Pre-commit checks**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.

7. **Submit**
   - Submit the PR.

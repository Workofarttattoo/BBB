💡 **What:**
The optimization resolves an N+1 query problem inside the `manage_marketing_campaigns` method of `Level6Agent`. Previously, the code fetched all active businesses and then executed a separate query for each business to check if it had a recent marketing campaign. I replaced this with a single query that joins the `Business` and `MarketingCampaign` tables, groups by the business ID, and uses a `HAVING` clause to filter out businesses that already have recent campaigns.

🎯 **Why:**
The previous implementation performed $1 + N$ queries for $N$ active businesses. For a database with thousands of active businesses, this would cause significant latency and excessive database load. The new implementation requires only two queries (one to find the IDs of businesses needing a campaign, and one to fetch the required `Business` objects), reducing latency drastically and lowering database connection overhead.

📊 **Measured Improvement:**
I created a benchmark script `tests/benchmark_n_plus_one.py` to test the performance improvement using an in-memory SQLite database populated with 2000 active businesses (80% having a recent campaign, so 400 needed one). The results are as follows:
* **Baseline (before optimization):** ~6.055 seconds
* **Optimized (after optimization):** ~2.198 seconds
* **Improvement:** 2.75x faster (-63.7% execution time).

*Note: In a real-world scenario with network latency to a remote PostgreSQL database, the N+1 problem would be far more severe, so the actual performance improvement would be significantly higher.*

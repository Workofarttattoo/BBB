import asyncio
import time
import sys
import os
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
import random

sys.path.append(os.path.join(os.getcwd(), 'src'))

from blank_business_builder.level6_agent import Level6Agent, AutonomyLevel
from blank_business_builder.database import User, Business

# Mock classes to make the function work without a real DB but with delays
class MockQuery:
    def __init__(self, delay=0.001, results=None, count_result=0):
        self.delay = delay
        self.results = results if results is not None else []
        self.count_result = count_result

    def filter(self, *args, **kwargs):
        # We don't actually filter, we just simulate the delay and return self
        return self

    def order_by(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def all(self):
        time.sleep(self.delay)  # Simulate DB IO latency
        return self.results

    def count(self):
        time.sleep(self.delay)  # Simulate DB IO latency
        return self.count_result

def create_mock_session(num_users=1000, latency=0.001):
    session = MagicMock(spec=Session)

    users = []
    business_counts = {}

    # Create mock users
    for i in range(num_users):
        mock_user = MagicMock(spec=User)
        mock_user.id = f"user-{i}"
        mock_user.email = f"user{i}@example.com"

        # Distribute subscription tiers
        tier_rand = random.random()
        if tier_rand < 0.6:
            mock_user.subscription_tier = "free"
            num_businesses = random.randint(0, 2)
        elif tier_rand < 0.9:
            mock_user.subscription_tier = "starter"
            num_businesses = random.randint(1, 4)
        else:
            mock_user.subscription_tier = "pro"
            num_businesses = random.randint(3, 8)

        users.append(mock_user)
        business_counts[mock_user.id] = num_businesses

    def side_effect(model, *columns):
        # Determine what's being queried.
        # If columns are passed, it's a specific select, likely the optimized bulk query
        if columns and "Business" in str(model):
            # This is the optimized query: db.query(Business.user_id, func.count(Business.id))
            # We return a list of tuples like [(user_id, count), ...]
            mock_results = [(uid, count) for uid, count in business_counts.items()]
            return MockQuery(delay=latency, results=mock_results)

        # N+1 unoptimized query
        if "Business" in str(model):
            # Since we can't easily parse the filter in this simple mock, we'll just return a random count
            # or the average count to simulate the delay of a single count query.
            # In a real test, the filter would give the user_id. Here we just want the latency.
            return MockQuery(delay=latency, count_result=1) # Random static result for N+1 count

        if "User" in str(model):
            # The query to get the users to iterate over
            return MockQuery(delay=latency, results=users)

        return MockQuery()

    session.query.side_effect = side_effect
    return session

async def main():
    print("Starting benchmark for optimize_revenue...")

    # Simulated DB latency per query (e.g., 1ms)
    DB_LATENCY = 0.001
    NUM_USERS = 1000

    session = create_mock_session(num_users=NUM_USERS, latency=DB_LATENCY)
    agent = Level6Agent(autonomy_level=AutonomyLevel.FULL)

    start_time = time.time()

    # Run the function under test
    print(f"Calling optimize_revenue with {NUM_USERS} users...")
    try:
        results = await agent.optimize_revenue(session)
    except Exception as e:
        print(f"Error calling optimize_revenue: {e}")
        return

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\nResults:")
    print(f"Total execution time: {total_time:.4f}s")
    print(f"Found {len(results)} upsell decisions.")

    if total_time > (NUM_USERS * DB_LATENCY):
        print(f"\nConclusion: N+1 query issue detected! Found {total_time/DB_LATENCY:.0f} queries instead of expected 2 queries.")
    else:
        print(f"\nConclusion: Optimized! Expected queries: 2. Execution time reflects this.")

if __name__ == "__main__":
    asyncio.run(main())

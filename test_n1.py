import asyncio
from unittest.mock import MagicMock
from blank_business_builder.level6_agent import Level6Agent, AgentDecision
from datetime import datetime, timedelta

async def test():
    db = MagicMock()

    # Mock business objects
    businesses = []
    for i in range(100):
        b = MagicMock()
        b.id = str(i)
        b.business_name = f"Biz {i}"
        businesses.append(b)

    db.query.return_value.filter.return_value.all.return_value = businesses

    # We want to see how many times db.query is called for recent_campaigns
    # In the original code, it's called 100 times, once for each business

    agent = Level6Agent.__new__(Level6Agent)
    agent.openai = MagicMock()

    await agent.manage_marketing_campaigns(db)

    print(f"db.query called {db.query.call_count} times")

if __name__ == "__main__":
    asyncio.run(test())

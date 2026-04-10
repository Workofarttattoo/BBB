import asyncio
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import uuid
import sys
import os

# Add src to path to allow importing from blank_business_builder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from blank_business_builder.database import Base, Business, MarketingCampaign, get_db_engine
from blank_business_builder.level6_agent import Level6Agent, AutonomyLevel

# Use an in-memory SQLite database for the benchmark
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_data(db, num_businesses=1000):
    print(f"Setting up data for benchmark with {num_businesses} businesses...")
    for i in range(num_businesses):
        business = Business(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            business_name=f"Test Business {i}",
            status="active"
        )
        db.add(business)

        # Give 80% of them a recent campaign, so 20% need one
        if i < (num_businesses * 0.8):
            campaign = MarketingCampaign(
                business_id=business.id,
                campaign_name=f"Recent Campaign {i}",
                created_at=datetime.now(timezone.utc) - timedelta(days=5)
            )
            db.add(campaign)

    db.commit()

# Mock the OpenAI service to avoid actual API calls and isolate DB performance
class MockOpenAI:
    def generate_marketing_copy(self, *args, **kwargs):
        return "Mock marketing copy"

class MockBuffer:
    pass

class MockSendGrid:
    pass

class MockIntegrationFactory:
    @staticmethod
    def get_openai_service():
        return MockOpenAI()

    @staticmethod
    def get_sendgrid_service():
        return MockSendGrid()

    @staticmethod
    def get_buffer_service():
        return MockBuffer()

async def run_benchmark():
    db = SessionLocal()
    setup_data(db, 2000)

    # Patch IntegrationFactory to use mocks
    import blank_business_builder.level6_agent
    blank_business_builder.level6_agent.IntegrationFactory = MockIntegrationFactory

    agent = Level6Agent(autonomy_level=AutonomyLevel.FULL)

    # Warmup
    print("Running warmup...")
    await agent.manage_marketing_campaigns(db)

    # Reset any changes made during warmup
    db.rollback()
    db.query(MarketingCampaign).filter(MarketingCampaign.campaign_name.like("Auto-generated%")).delete()
    db.commit()

    # Benchmark
    print("Running benchmark...")

    # Run multiple iterations for a better average
    iterations = 5
    total_time = 0

    for i in range(iterations):
        # Reset any changes made during warmup/previous iterations
        db.rollback()
        db.query(MarketingCampaign).filter(MarketingCampaign.campaign_name.like("Auto-generated%")).delete()
        db.commit()

        start_time = time.perf_counter()
        decisions = await agent.manage_marketing_campaigns(db)
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        total_time += elapsed

        if i == 0:
            print(f"Generated {len(decisions)} campaigns in first iteration")

    avg_time = total_time / iterations
    print(f"Average time taken: {avg_time:.4f} seconds (over {iterations} runs)")

    db.close()
    return avg_time

if __name__ == "__main__":
    asyncio.run(run_benchmark())

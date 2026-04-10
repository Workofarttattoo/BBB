import asyncio
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.blank_business_builder.database import Base, User, Subscription, Business
from src.blank_business_builder.level6_agent import Level6Agent, AutonomyLevel
import uuid
from datetime import datetime, timedelta

def setup_test_db(num_users=3000):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print(f"Generating {num_users} users, subscriptions, and businesses...")
    users = []
    subscriptions = []
    businesses = []

    now = datetime.utcnow()

    for i in range(num_users):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"user{i}@example.com",
            hashed_password="hash",
            last_login=now - timedelta(days=(i % 40)) # mix of active and inactive
        )
        users.append(user)

        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=user_id,
            status="active",
            plan_name="pro"
        )
        subscriptions.append(subscription)

        num_businesses = i % 3
        for j in range(num_businesses):
            business = Business(
                id=uuid.uuid4(),
                user_id=user_id,
                business_name=f"Business {i}-{j}",
                status="active"
            )
            businesses.append(business)

    db.bulk_save_objects(users)
    db.bulk_save_objects(subscriptions)
    db.bulk_save_objects(businesses)
    db.commit()

    return db

async def run_benchmark():
    db = setup_test_db(num_users=3000)
    agent = Level6Agent(autonomy_level=AutonomyLevel.FULL)

    # Mocking external calls to avoid SendGrid/OpenAI
    class MockService:
        def generate_email_campaign(self, *args, **kwargs):
            return {"subject": "subject", "body": "body"}
        def send_email(self, *args, **kwargs):
            pass

    agent.openai = MockService()
    agent.sendgrid = MockService()

    print("Running baseline benchmark...")

    # warmup
    await agent.manage_churn_prevention(db)

    start_time = time.time()

    decisions = await agent.manage_churn_prevention(db)

    end_time = time.time()
    duration = end_time - start_time

    print(f"Processed {len(decisions)} churn prevention decisions.")
    print(f"Execution time: {duration:.4f} seconds")

    db.close()

if __name__ == "__main__":
    asyncio.run(run_benchmark())

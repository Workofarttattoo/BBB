import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from src.blank_business_builder.database import Base, Business, AgentTask
from src.blank_business_builder.websockets import _get_business_metrics_sync, _metrics_cache, CACHE_TTL

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_metrics_caching(db_session):
    # Setup test data
    user_id = str(uuid.uuid4())
    business_id = str(uuid.uuid4())
    b = Business(id=business_id, business_name="Test Business", user_id=user_id)
    db_session.add(b)

    t = AgentTask(id=str(uuid.uuid4()), business_id=business_id, agent_role="test", task_type="test", status="completed")
    db_session.add(t)
    db_session.commit()

    # Clear cache before test
    _metrics_cache.clear()

    # First call - should hit DB and populate cache
    assert business_id not in _metrics_cache
    metrics1 = _get_business_metrics_sync(business_id, db_session)
    assert business_id in _metrics_cache
    assert metrics1["tasks"]["completed"] == 1

    # Modify DB directly (bypassing normal flow)
    t2 = AgentTask(id=str(uuid.uuid4()), business_id=business_id, agent_role="test", task_type="test", status="completed")
    db_session.add(t2)
    db_session.commit()

    # Second call - should hit cache and NOT reflect the DB change yet
    metrics2 = _get_business_metrics_sync(business_id, db_session)
    assert metrics2["tasks"]["completed"] == 1 # Still 1 because cached

    # Manually expire cache
    _metrics_cache[business_id]["expires_at"] = time.time() - 1

    # Third call - should hit DB because cache expired
    metrics3 = _get_business_metrics_sync(business_id, db_session)
    assert metrics3["tasks"]["completed"] == 2 # Now 2 because DB was queried

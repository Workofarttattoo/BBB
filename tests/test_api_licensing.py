
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import uuid

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db, User
from blank_business_builder.api_licensing import RevenueReport, LicenseAgreement
from blank_business_builder.auth import get_current_user

# Setup in-memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock user
mock_user_id = str(uuid.uuid4())
mock_user = User(
    id=mock_user_id,
    email="test@example.com",
    hashed_password="pw",
    full_name="Test User",
    license_status="revenue_share",
    subscription_tier="starter"
)

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.expire_on_commit = False
    db.add(mock_user)

    # Add an active agreement
    agreement = LicenseAgreement(
        user_id=mock_user_id,
        agreement_type="revenue_share",
        status="active",
        accepted_at=datetime.utcnow()
    )
    db.add(agreement)
    db.commit()

    yield

    db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_license_status_revenue_aggregation():
    db = TestingSessionLocal()

    # Create revenue reports
    # 1. Paid report
    r1 = RevenueReport(
        user_id=mock_user_id,
        report_month="2023-01",
        gross_revenue=1000.0,
        revenue_share_owed=500.0,
        payment_due_date=datetime.utcnow() - timedelta(days=30),
        status="paid",
        payment_amount=500.0,
        submitted_at=datetime.utcnow()
    )

    # 2. Pending report (not overdue)
    r2 = RevenueReport(
        user_id=mock_user_id,
        report_month="2023-02",
        gross_revenue=2000.0,
        revenue_share_owed=1000.0,
        payment_due_date=datetime.utcnow() + timedelta(days=10),
        status="pending",
        submitted_at=datetime.utcnow()
    )

    # 3. Overdue report
    r3 = RevenueReport(
        user_id=mock_user_id,
        report_month="2023-03",
        gross_revenue=3000.0,
        revenue_share_owed=1500.0,
        payment_due_date=datetime.utcnow() - timedelta(days=5),
        status="pending",
        submitted_at=datetime.utcnow()
    )

    db.add_all([r1, r2, r3])
    db.commit()

    response = client.get("/api/licensing/status")
    assert response.status_code == 200
    data = response.json()

    # Check aggregations
    # Total reported: 1000 + 2000 + 3000 = 6000
    assert data["total_revenue_reported"] == 6000.0

    # Total owed: 500 + 1000 + 1500 = 3000
    assert data["total_revenue_share_owed"] == 3000.0

    # Total paid: 500
    assert data["total_revenue_share_paid"] == 500.0

    # Outstanding: 3000 - 500 = 2500
    assert data["outstanding_balance"] == 2500.0

    # Overdue reports: 1 (r3)
    assert data["overdue_reports"] == 1

def test_get_license_status_empty_reports():
    response = client.get("/api/licensing/status")
    assert response.status_code == 200
    data = response.json()

    assert data["total_revenue_reported"] == 0.0
    assert data["total_revenue_share_owed"] == 0.0
    assert data["total_revenue_share_paid"] == 0.0
    assert data["outstanding_balance"] == 0.0
    assert data["overdue_reports"] == 0

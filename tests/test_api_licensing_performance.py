import pytest
import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from blank_business_builder.database import Base, User, UUIDType
from blank_business_builder.api_licensing import RevenueReport, LicenseAgreement, get_license_status

# Setup database
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

class MockUser:
    def __init__(self, id, email, license_status, trial_expires_at):
        self.id = str(id)
        self.email = email
        self.license_status = license_status
        self.trial_expires_at = trial_expires_at
        self.subscription_tier = "free"

@pytest.fixture(scope="module")
def current_user(db):
    # We use a mock user with string ID to ensure compatibility with SQLite
    # comparisons against String columns in api_licensing.py
    user_id = uuid.uuid4()
    return MockUser(
        id=user_id,
        email="test_agg@example.com",
        license_status="revenue_share",
        trial_expires_at=datetime.utcnow() + timedelta(days=30)
    )

@pytest.mark.asyncio
async def test_get_license_status_aggregation(db, current_user):
    # Setup data
    reports = []
    base_date = datetime.utcnow()

    # 1. Paid report
    reports.append(RevenueReport(
        user_id=str(current_user.id),
        report_month="2023-01",
        gross_revenue=1000.0,
        revenue_share_owed=500.0,
        payment_due_date=base_date - timedelta(days=30),
        status="paid",
        payment_amount=500.0
    ))

    # 2. Pending overdue report
    reports.append(RevenueReport(
        user_id=str(current_user.id),
        report_month="2023-02",
        gross_revenue=2000.0,
        revenue_share_owed=1000.0,
        payment_due_date=base_date - timedelta(days=5),
        status="pending",
        payment_amount=0.0
    ))

    # 3. Pending future due report
    reports.append(RevenueReport(
        user_id=str(current_user.id),
        report_month="2023-03",
        gross_revenue=3000.0,
        revenue_share_owed=1500.0,
        payment_due_date=base_date + timedelta(days=10),
        status="pending",
        payment_amount=0.0
    ))

    # 4. Another paid report
    reports.append(RevenueReport(
        user_id=str(current_user.id),
        report_month="2023-04",
        gross_revenue=4000.0,
        revenue_share_owed=2000.0,
        payment_due_date=base_date + timedelta(days=20),
        status="paid",
        payment_amount=2000.0
    ))

    # Add agreement to simulate active status
    agreement = LicenseAgreement(
        user_id=str(current_user.id),
        agreement_type="revenue_share",
        accepted_at=datetime.utcnow(),
        status="active"
    )
    db.add(agreement)

    db.add_all(reports)
    db.commit()

    # Call the function
    # Note: get_license_status is async
    response = await get_license_status(current_user=current_user, db=db)

    # Verify aggregations

    # Total reported: 1000 + 2000 + 3000 + 4000 = 10000
    assert response.total_revenue_reported == 10000.0

    # Total owed: 500 + 1000 + 1500 + 2000 = 5000
    assert response.total_revenue_share_owed == 5000.0

    # Total paid: 500 + 2000 = 2500
    assert response.total_revenue_share_paid == 2500.0

    # Outstanding: 5000 - 2500 = 2500
    assert response.outstanding_balance == 2500.0

    # Overdue reports: only 2023-02 is pending and due < now
    assert response.overdue_reports == 1

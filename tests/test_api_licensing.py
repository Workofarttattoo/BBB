
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
from blank_business_builder.auth import get_current_user, AuthService

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

# Mock user ID
mock_user_id = str(uuid.uuid4())

def override_get_current_user_id():
    return mock_user_id

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[AuthService.get_current_user_id] = override_get_current_user_id

client = TestClient(app)

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create the user in the DB
    user = User(
        id=mock_user_id,
        email="test@example.com",
        hashed_password="pw",
        full_name="Test User",
        license_status="revenue_share",
        subscription_tier="starter",
        trial_expires_at=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    db.add(user)
    db.commit()

    yield

    db.close()
    Base.metadata.drop_all(bind=engine)

def create_active_agreement(db):
    agreement = LicenseAgreement(
        user_id=mock_user_id,
        agreement_type="revenue_share",
        status="active",
        accepted_at=datetime.utcnow()
    )
    db.add(agreement)
    db.commit()
    return agreement

def get_user(db):
    return db.query(User).filter(User.id == mock_user_id).first()

def test_get_license_status_revenue_aggregation():
    db = TestingSessionLocal()
    create_active_agreement(db)

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
    db = TestingSessionLocal()
    create_active_agreement(db)

    response = client.get("/api/licensing/status")
    assert response.status_code == 200
    data = response.json()

    assert data["total_revenue_reported"] == 0.0
    assert data["total_revenue_share_owed"] == 0.0
    assert data["total_revenue_share_paid"] == 0.0
    assert data["outstanding_balance"] == 0.0
    assert data["overdue_reports"] == 0


# --- New Tests ---

def test_accept_revenue_share_success():
    # Ensure no existing agreement
    db = TestingSessionLocal()
    db.query(LicenseAgreement).delete()

    # Reset status
    user = get_user(db)
    user.license_status = "trial"
    db.commit()

    payload = {
        "company_name": "Test Corp",
        "legal_entity_type": "LLC",
        "address": "123 Test St",
        "phone": "555-0123",
        "confirmation": "I AGREE to 50% revenue share terms"
    }

    response = client.post("/api/licensing/accept-revenue-share", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["license_status"] == "revenue_share"
    assert "agreement_id" in data

    # Verify DB
    agreement = db.query(LicenseAgreement).filter_by(user_id=mock_user_id).first()
    assert agreement is not None
    assert agreement.status == "active"
    assert agreement.company_name == "Test Corp"

    # Cleanup not strictly needed as init_db resets

def test_accept_revenue_share_invalid_confirmation():
    payload = {
        "confirmation": "I kinda agree"
    }
    response = client.post("/api/licensing/accept-revenue-share", json=payload)
    assert response.status_code == 400
    assert "Invalid confirmation" in response.json()["detail"]

def test_accept_revenue_share_duplicate():
    # Create active agreement first
    db = TestingSessionLocal()
    create_active_agreement(db)

    payload = {
        "confirmation": "I AGREE to 50% revenue share terms"
    }
    response = client.post("/api/licensing/accept-revenue-share", json=payload)
    assert response.status_code == 400
    assert "already have an active" in response.json()["detail"]

def test_submit_revenue_report_success():
    # Ensure user is revenue_share
    db = TestingSessionLocal()
    user = get_user(db)
    user.license_status = "revenue_share"
    db.commit()

    payload = {
        "report_month": "2023-04",
        "product_sales": 1000.0,
        "service_fees": 500.0,
        "subscription_revenue": 0.0,
        "consulting_fees": 0.0,
        "advertising_revenue": 0.0,
        "affiliate_commissions": 0.0,
        "other_revenue": 0.0,
        "notes": "Good month"
    }

    response = client.post("/api/licensing/submit-revenue-report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["gross_revenue"] == 1500.0
    assert data["revenue_share_owed"] == 750.0 # 50%

    # Verify due date (15 days after month end)
    # 2023-04 -> Due 2023-05-15
    due_date = datetime.fromisoformat(data["payment_due_date"])
    assert due_date.year == 2023
    assert due_date.month == 5
    assert due_date.day == 15

def test_submit_revenue_report_duplicate():
    # Submit once
    payload = {
        "report_month": "2023-05",
        "product_sales": 100.0
    }
    client.post("/api/licensing/submit-revenue-report", json=payload)

    # Submit again
    response = client.post("/api/licensing/submit-revenue-report", json=payload)
    assert response.status_code == 400
    assert "already submitted" in response.json()["detail"]

def test_submit_revenue_report_forbidden():
    # Change user status
    db = TestingSessionLocal()
    user = get_user(db)
    user.license_status = "trial"
    db.commit()

    payload = {
        "report_month": "2023-06",
        "product_sales": 100.0
    }
    response = client.post("/api/licensing/submit-revenue-report", json=payload)
    assert response.status_code == 403
    assert "only for revenue share" in response.json()["detail"]


def test_get_revenue_reports():
    db = TestingSessionLocal()
    # Create some reports
    r1 = RevenueReport(user_id=mock_user_id, report_month="2023-01", gross_revenue=100.0, revenue_share_owed=50.0, payment_due_date=datetime.utcnow(), status="paid", submitted_at=datetime.utcnow())
    r2 = RevenueReport(user_id=mock_user_id, report_month="2023-02", gross_revenue=200.0, revenue_share_owed=100.0, payment_due_date=datetime.utcnow(), status="pending", submitted_at=datetime.utcnow())
    db.add_all([r1, r2])
    db.commit()

    response = client.get("/api/licensing/revenue-reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) == 2
    assert data["reports"][0]["month"] == "2023-02" # Ordered by desc
    assert data["reports"][1]["month"] == "2023-01"

def test_purchase_license_pricing():
    # Starter
    payload = {
        "license_type": "starter",
        "max_users": 10,
        "max_businesses": 5,
        "support_level": "basic",
        "billing_email": "bill@example.com"
    }
    # Calculation:
    # Base: 2999
    # Users: 10 * 99 = 990
    # Businesses: 5 * 149 = 745
    # Support: 0
    # Total: 2999 + 990 + 745 = 4734

    response = client.post("/api/licensing/purchase-license", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 4734.0

    # Enterprise with Premium support
    payload2 = {
        "license_type": "enterprise",
        "max_users": 100,
        "max_businesses": 50,
        "support_level": "premium",
        "billing_email": "ent@example.com"
    }
    # Base: 29999
    # Users: 100 * 299 = 29900
    # Businesses: 50 * 499 = 24950
    # Support: 1999
    # Total: 29999 + 29900 + 24950 + 1999 = 86848

    response = client.post("/api/licensing/purchase-license", json=payload2)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 86848.0

def test_terminate_agreement():
    db = TestingSessionLocal()
    create_active_agreement(db)

    # Add some outstanding reports
    r1 = RevenueReport(user_id=mock_user_id, report_month="2023-01", revenue_share_owed=500.0, status="pending", payment_due_date=datetime.utcnow(), submitted_at=datetime.utcnow(), gross_revenue=1000.0)
    db.add(r1)
    db.commit()

    response = client.post("/api/licensing/terminate-agreement?reason=Going%20out%20of%20business")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["outstanding_payments"] == 1
    assert data["outstanding_amount"] == 500.0

    # Verify DB status
    agreement = db.query(LicenseAgreement).filter_by(user_id=mock_user_id).first()
    assert agreement.status == "terminated"
    assert agreement.termination_reason == "Going out of business"

    # Verify user status reverted (trial still valid)
    user = get_user(db)
    assert user.license_status == "trial"

def test_get_agreement_document():
    db = TestingSessionLocal()
    create_active_agreement(db)

    response = client.get("/api/licensing/agreement-document")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["type"] == "revenue_share"

def test_get_agreement_document_not_found():
    db = TestingSessionLocal()
    db.query(LicenseAgreement).delete()
    db.commit()

    response = client.get("/api/licensing/agreement-document")
    assert response.status_code == 404

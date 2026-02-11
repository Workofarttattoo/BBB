
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from blank_business_builder.main import app
from blank_business_builder.database import get_db, User
from blank_business_builder.auth import get_current_user
from blank_business_builder.api_licensing import PurchaseLicenseRequest

# Mock database dependency
def override_get_db():
    try:
        yield MagicMock()
    finally:
        pass

# Mock current user dependency
def override_get_current_user():
    return User(
        id="test-user-id",
        email="test@example.com",
        license_status="trial",
        is_active=True
    )

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_generate_license_quote():
    payload = {
        "license_type": "professional",
        "max_users": 5,
        "max_businesses": 2,
        "support_level": "premium",
        "company_name": "Acme Corp",
        "billing_email": "billing@acmecorp.com"
    }

    response = client.post("/api/licensing/purchase-license", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # The message should clearly state it is a quote
    assert "License quote generated" in data["message"]
    # Amount validation
    assert data["amount"] > 0
    # Payment URL should be None as per current implementation
    assert data["payment_url"] is None

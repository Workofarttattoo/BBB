"""
Better Business Builder - Authentication Tests
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db
from blank_business_builder.auth import (
    AuthService,
    RoleBasedAccessControl,
    require_license_access,
    require_quantum_access,
    rate_limit
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and teardown test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestAuthentication:
    """Test authentication endpoints."""

    def test_register_user(self):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        # Duplicate registration
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass456"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self):
        """Test successful login."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "testpass123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self):
        """Test getting current user information."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )
        token = register_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["subscription_tier"] == "free"

    def test_get_current_user_invalid_token(self):
        """Test getting user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        """Test password verification."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrongpassword", hashed)


class TestJWTTokens:
    """Test JWT token functionality."""

    def test_create_access_token(self):
        """Test access token creation."""
        token = AuthService.create_access_token(data={"sub": "user123"})

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self):
        """Test token decoding."""
        user_id = "user123"
        token = AuthService.create_access_token(data={"sub": user_id})

        payload = AuthService.decode_token(token)

        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = AuthService.create_refresh_token(data={"sub": "user123"})

        assert isinstance(token, str)
        assert len(token) > 0

        payload = AuthService.decode_token(token)
        assert payload["type"] == "refresh"

    def test_create_access_token_with_custom_expiry(self):
        """Custom expiry uses provided timedelta."""
        token = AuthService.create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(minutes=5)
        )
        payload = AuthService.decode_token(token)
        assert payload["type"] == "access"

    def test_decode_token_expired(self):
        """Expired token raises 401."""
        expired_token = AuthService.create_access_token(
            data={"sub": "expired-user"},
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(HTTPException) as exc:
            AuthService.decode_token(expired_token)
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail


class TestAccessControl:
    """Test RBAC utilities and license requirements."""

    def test_role_based_access_limits(self):
        """Starter tier allows fewer than 3 businesses."""
        assert RoleBasedAccessControl.check_permission("starter", "businesses", 2)
        assert not RoleBasedAccessControl.check_permission("starter", "businesses", 3)
        assert RoleBasedAccessControl.check_permission("enterprise", "campaigns_per_month", 500)

    def test_role_based_access_features(self):
        """Only Pro+ tiers include quantum feature access."""
        assert RoleBasedAccessControl.has_feature("pro", "quantum")
        assert not RoleBasedAccessControl.has_feature("starter", "quantum")

    def test_require_license_access_enforces_payment(self):
        """Users with expired trials must upgrade."""
        user = UserFactory(license_status="trial", trial_expires_at=None)
        with pytest.raises(HTTPException) as exc:
            require_license_access(current_user=user)
        assert exc.value.status_code == 402

    def test_require_quantum_access_enforces_pro_tier(self):
        """Starter tier blocked from quantum endpoints."""
        user = UserFactory(subscription_tier="starter", license_status="licensed")
        with pytest.raises(HTTPException) as exc:
            require_quantum_access(current_user=user)
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_rate_limit_decorator_blocks_after_threshold():
    """Rate limiter should reject requests beyond quota."""
    calls = []

    @rate_limit(max_requests=2, window_seconds=60)
    async def protected_endpoint(current_user=None):
        calls.append("hit")
        return "ok"

    user = UserFactory(id="rate-user", license_status="licensed")
    assert await protected_endpoint(current_user=user) == "ok"
    assert await protected_endpoint(current_user=user) == "ok"

    with pytest.raises(HTTPException) as exc:
        await protected_endpoint(current_user=user)
    assert exc.value.status_code == 429
    assert len(calls) == 2


def UserFactory(**overrides):
    """Create a lightweight user object for auth helpers."""
    defaults = {
        "id": overrides.get("id", "user-id"),
        "license_status": overrides.get("license_status", "trial"),
        "trial_expires_at": overrides.get("trial_expires_at"),
        "subscription_tier": overrides.get("subscription_tier", "free"),
        "is_active": overrides.get("is_active", True),
    }

    class _User:
        def __init__(self, attrs):
            self.__dict__.update(attrs)

    return _User(defaults)


class TestLicensingFlows:
    """Test license and tier enforcement."""

    def test_accept_revenue_share_unlocks_access(self):
        """New users can accept revenue share to leave trial mode."""
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "share@example.com",
                "password": "testpass123",
                "full_name": "Share User"
            }
        )
        token = register_response.json()["access_token"]

        accept_response = client.post(
            "/api/license/accept-revenue-share",
            headers={"Authorization": f"Bearer {token}"},
            json={"percentage": 50.0}
        )
        assert accept_response.status_code == 200
        data = accept_response.json()
        assert data["status"] == "accepted"
        assert data["license_status"] == "revenue_share"
        assert data["revenue_share_percentage"] == 50.0

        status_response = client.get(
            "/api/license/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status_response.status_code == 200
        assert status_response.json()["license_status"] == "revenue_share"

    def test_quantum_endpoints_require_pro_tier(self):
        """Quantum API should reject Starter/trial users."""
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "quantum@example.com",
                "password": "testpass123"
            }
        )
        token = register_response.json()["access_token"]

        response = client.get(
            "/api/quantum/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        assert "Upgrade to Pro" in response.json()["detail"]

    def test_activate_license_promotes_subscription(self):
        """Users can activate paid licenses and change subscription tier."""
        # Setup license
        from blank_business_builder.api_licensing import PurchasedLicense
        from datetime import datetime

        db = TestingSessionLocal()
        license = PurchasedLicense(
            license_key="PRO-LICENSE-KEY",
            purchase_date=datetime.utcnow(),
            purchase_amount=100.0,
            payment_method="test",
            transaction_id="tx_test",
            license_type="pro",
            max_users=1,
            max_businesses=5,
            support_level="premium",
            support_expires_at=datetime.utcnow(),
            is_active=True,
            billing_email="pro@example.com"
        )
        db.add(license)
        db.commit()
        db.close()

        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "pro@example.com",
                "password": "testpass123"
            }
        )
        token = register_response.json()["access_token"]

        activate_response = client.post(
            "/api/license/activate",
            headers={"Authorization": f"Bearer {token}"},
            json={"license_key": "PRO-LICENSE-KEY"}
        )
        assert activate_response.status_code == 200
        data = activate_response.json()
        assert data["status"] == "activated"
        assert data["subscription_tier"] == "pro"

        status_response = client.get(
            "/api/license/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["subscription_tier"] == "pro"
        assert status_data["license_status"] == "licensed"

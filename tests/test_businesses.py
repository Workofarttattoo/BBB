"""
Better Business Builder - Business Operations Tests
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db, User

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


@pytest.fixture
def authenticated_user():
    """Create and return authenticated user with token."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    token = response.json()["access_token"]
    return {"token": token, "email": "test@example.com"}


class TestBusinessOperations:
    """Test business CRUD operations."""

    def test_create_business(self, authenticated_user):
        """Test creating a business."""
        response = client.post(
            "/api/businesses",
            json={
                "business_name": "Test Business",
                "industry": "Technology",
                "description": "A test business",
                "website_url": "https://testbusiness.com"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["business_name"] == "Test Business"
        assert data["industry"] == "Technology"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_business_unauthorized(self):
        """Test creating business without authentication."""
        response = client.post(
            "/api/businesses",
            json={
                "business_name": "Test Business",
                "industry": "Technology",
                "description": "A test business"
            }
        )

        assert response.status_code == 403

    def test_list_businesses(self, authenticated_user):
        """Test listing user's businesses."""
        # Create multiple businesses
        for i in range(3):
            client.post(
                "/api/businesses",
                json={
                    "business_name": f"Business {i}",
                    "industry": "Technology",
                    "description": f"Test business {i}"
                },
                headers={"Authorization": f"Bearer {authenticated_user['token']}"}
            )

        # List businesses
        response = client.get(
            "/api/businesses",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("business_name" in b for b in data)

    def test_list_businesses_empty(self, authenticated_user):
        """Test listing businesses when user has none."""
        response = client.get(
            "/api/businesses",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_business_limit_free_tier(self, authenticated_user):
        """Test business creation limit for free tier."""
        # Free tier allows 1 business
        response1 = client.post(
            "/api/businesses",
            json={
                "business_name": "Business 1",
                "industry": "Technology",
                "description": "First business"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response1.status_code == 200

        # Second business should fail
        response2 = client.post(
            "/api/businesses",
            json={
                "business_name": "Business 2",
                "industry": "Technology",
                "description": "Second business"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response2.status_code == 403
        assert "limit" in response2.json()["detail"].lower()


class TestAIGeneration:
    """Test AI-powered content generation."""

    def test_generate_business_plan_unauthorized(self):
        """Test business plan generation without auth."""
        response = client.post(
            "/api/ai/generate-business-plan",
            json={
                "business_id": "test-id",
                "target_market": "Small businesses"
            }
        )

        assert response.status_code == 403

    def test_generate_marketing_copy_unauthorized(self):
        """Test marketing copy generation without auth."""
        response = client.post(
            "/api/ai/generate-marketing-copy",
            json={
                "business_id": "test-id",
                "platform": "twitter",
                "campaign_goal": "Brand awareness",
                "target_audience": "Tech entrepreneurs"
            }
        )

        assert response.status_code == 403

    def test_generate_email_campaign_unauthorized(self):
        """Test email campaign generation without auth."""
        response = client.post(
            "/api/ai/generate-email-campaign",
            json={
                "business_id": "test-id",
                "campaign_goal": "Product launch",
                "target_audience": "Existing customers",
                "key_points": ["New features", "Limited offer"]
            }
        )

        assert response.status_code == 403


class TestBusinessValidation:
    """Test business data validation."""

    def test_create_business_missing_fields(self, authenticated_user):
        """Test business creation with missing required fields."""
        response = client.post(
            "/api/businesses",
            json={
                "business_name": "Test Business"
                # Missing industry and description
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        assert response.status_code == 422  # Validation error

    def test_create_business_invalid_url(self, authenticated_user):
        """Test business creation with invalid website URL."""
        response = client.post(
            "/api/businesses",
            json={
                "business_name": "Test Business",
                "industry": "Technology",
                "description": "A test business",
                "website_url": "not-a-url"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        # Should either validate or accept (depends on validation rules)
        # For now, just ensure it doesn't crash
        assert response.status_code in [200, 422]

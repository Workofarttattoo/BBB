from fastapi.testclient import TestClient

from src.blank_business_builder.bbb_unified_business_library import BBBUnifiedLibrary
from src.blank_business_builder.config import settings
from src.blank_business_builder.echo_prime_api import app as echo_prime_app
from src.blank_business_builder.main import app as bbb_app


def test_packaged_unified_library_loads_cloud_data():
    library = BBBUnifiedLibrary()
    summary = library.generate_summary_report()

    assert summary["total_businesses"] == 31
    assert summary["ai_automation_count"] == 21
    assert summary["legacy_count"] == 10


def test_echo_prime_defaults_to_fine_tuned_ollama_model():
    assert settings.OLLAMA_MODEL == "ech0-fine-tuned-v2:latest"


def test_echo_prime_service_exposes_recommendations():
    client = TestClient(echo_prime_app)

    response = client.post(
        "/v1/businesses/recommendations",
        json={
            "budget": 5000,
            "available_hours_week": 15,
            "experience_level": "beginner",
        },
    )

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert recommendations
    assert "business" in recommendations[0]
    assert "match_score" in recommendations[0]


def test_bbb_api_exposes_echo_prime_health():
    client = TestClient(bbb_app)

    response = client.get("/api/v1/echo-prime/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["businesses_available"] == 31

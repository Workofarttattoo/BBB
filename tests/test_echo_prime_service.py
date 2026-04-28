from fastapi.testclient import TestClient

from src.blank_business_builder.echo_prime_service import app


client = TestClient(app)


def test_outreach_decision_steers_by_lead_context():
    response = client.post(
        "/internal/echo/outreach-decision",
        json={
            "lead_event": {
                "full_name": "Morgan Lee",
                "company": "Acme Growth",
                "title": "VP Marketing",
                "phone": "+15555550123",
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["department"] == "marketing"
    assert payload["should_call"] is True
    assert payload["steered_by"] == "echo_prime"
    assert "Morgan Lee" in payload["task"]


def test_post_call_decision_books_interested_lead():
    response = client.post(
        "/internal/echo/post-call-decision",
        json={
            "call_event": {
                "status": "completed",
                "department": "sales",
                "transcript": "The prospect is interested and asked to book a demo.",
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_action"] == "schedule_meeting"
    assert payload["follow_up_in_minutes"] == 30
    assert payload["steered_by"] == "echo_prime"

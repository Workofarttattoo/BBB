"""
Tests for the GUI Server and API endpoints.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import json
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.blank_business_builder.gui_server import app, update_app_state, STATE_FILE, fiduciary, get_app_state

client = TestClient(app)

def reset_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    fiduciary.state = {
        "license": {
            "tier": "free",
            "active": False,
            "revenue_share_percentage": 0.0,
            "start_date": "2025-01-01T00:00:00",
            "bypass_used": False
        },
        "wallet": 0.0,
        "revenue_total": 0.0
    }

def setup_function(function):
    reset_state()

def setup_module(module):
    # Ensure clean state
    reset_state()

def teardown_module(module):
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Business Builder" in response.text

def test_onboarding_flow():
    profile = {
        "name": "Test User",
        "location_state": "NY",
        "preferred_industry": "Finance",
        "weekly_hours": 30,
        "startup_budget": 5000.0,
        "risk_posture": "bold"
    }
    response = client.post("/api/v1/onboarding", json=profile)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_onboarding_to_active_dashboard_flow():
    profile = {
        "name": "Dashboard User",
        "location_state": "CA",
        "preferred_industry": "Technology",
        "weekly_hours": 40,
        "startup_budget": 10000.0,
        "risk_posture": "balanced"
    }

    onboarding = client.post("/api/v1/onboarding", json=profile)
    assert onboarding.status_code == 200

    research = client.get("/api/v1/research")
    assert research.status_code == 200
    recommendations = research.json()["recommendations"]
    assert recommendations

    selected_name = recommendations[0]["name"]
    selection = client.post("/api/v1/select-business", json={"business_name": selected_name})
    assert selection.status_code == 200
    assert selection.json()["selected"] == selected_name

    license_response = client.post("/api/v1/license", json={"tier": "paid"})
    assert license_response.status_code == 200
    assert license_response.json()["active"] is True

    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["active"] is True
    assert data["status"] == "Running"
    assert data["business_name"] == selected_name
    assert data["license"]["tier"] == "paid"
    assert data["user_share"] == data["revenue_today"]

def test_acquisition_setup_after_owner_tier_does_not_persist_keys():
    profile = {
        "name": "Acquisition User",
        "location_state": "CA",
        "preferred_industry": "Technology",
        "weekly_hours": 40,
        "startup_budget": 10000.0,
        "risk_posture": "balanced"
    }
    client.post("/api/v1/onboarding", json=profile)
    client.post("/api/v1/select-business", json={"business_name": "No-Code App Development Agency"})
    client.post("/api/v1/license", json={"tier": "paid"})

    payload = {
        "target_customer": "small business owners",
        "lead_keywords": "founder owner operator",
        "service_offer": "AI automation setup package",
        "github_repo_url": "https://github.com/example/no-code-agency",
        "github_pages_url": "https://example.github.io/no-code-agency",
        "google_workspace_email": "sales@example.com",
        "google_drive_folder_url": "https://drive.google.com/drive/folders/demo",
        "apollo_api_key": "apollo-secret",
        "bland_api_key": "bland-secret",
        "bland_webhook_url": "https://example.com/api/webhooks/bland/post-call"
    }

    response = client.post("/api/v1/acquisition/setup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert data["run"]["business_name"] == "No-Code App Development Agency"
    assert data["run"]["toolchain"]["headhunter"]["status"] == "ready"
    assert data["run"]["toolchain"]["bland"]["status"] == "ready"
    assert data["run"]["toolchain"]["delivery"]["status"] == "ready"

    state = get_app_state()
    serialized_state = json.dumps(state)
    assert "apollo-secret" not in serialized_state
    assert "bland-secret" not in serialized_state

    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["acquisition"]["status"] == "running"
    assert "Search and enrich prospects" in dashboard["acquisition"]["pipeline"][0]

def test_recommendations():
    # Set profile first to influence recommendations
    profile = {
        "name": "Test User",
        "location_state": "NY",
        "preferred_industry": "Technology",
        "weekly_hours": 40,
        "startup_budget": 10000.0,
        "risk_posture": "balanced"
    }
    client.post("/api/v1/onboarding", json=profile)

    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if len(data) > 0:
        assert "name" in data[0]
        assert "expected_monthly_revenue" in data[0]

def test_license_bypass():
    code = "F00lpr00f596!"
    response = client.post("/api/v1/admin-bypass", json={"code": code})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify dashboard reflects this
    dash = client.get("/api/v1/dashboard").json()
    assert dash["license"]["tier"] == "paid"
    assert dash["license"]["bypass_used"] is True

def test_invalid_bypass():
    response = client.post("/api/v1/admin-bypass", json={"code": "WRONG_CODE"})
    assert response.status_code == 403

def test_license_partner_tier():
    # Reset state for this test
    fiduciary.state["license"]["tier"] = "free"
    fiduciary.state["license"]["active"] = False

    response = client.post("/api/v1/license", json={"tier": "partner"})
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "partner"
    assert data["revenue_share_percentage"] == 0.50

def test_dashboard_unlicensed():
    # Reset state
    fiduciary.state["license"]["active"] = False

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False
    assert data["status"] == "Pending License"

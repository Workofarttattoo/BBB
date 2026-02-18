"""
Tests for the GUI Server and API endpoints.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import json
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.blank_business_builder.gui_server import app, update_app_state, STATE_FILE, fiduciary

client = TestClient(app)

def setup_module(module):
    # Ensure clean state
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    # Reset fiduciary state
    fiduciary.state = {
        "license": {
            "tier": "free",
            "active": False,
            "revenue_share_percentage": 0.0,
            "start_date": "2025-01-01T00:00:00",
            "bypass_used": False
        }
    }

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
    response = client.post("/api/onboarding", json=profile)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

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
    client.post("/api/onboarding", json=profile)

    response = client.get("/api/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if len(data) > 0:
        assert "name" in data[0]
        assert "expected_monthly_revenue" in data[0]

def test_license_bypass():
    code = "F00lpr00f596!"
    response = client.post("/api/admin-bypass", json={"code": code})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify dashboard reflects this
    dash = client.get("/api/dashboard").json()
    assert dash["license"]["tier"] == "paid"
    assert dash["license"]["bypass_used"] is True

def test_invalid_bypass():
    response = client.post("/api/admin-bypass", json={"code": "WRONG_CODE"})
    assert response.status_code == 403

def test_license_partner_tier():
    # Reset state for this test
    fiduciary.state["license"]["tier"] = "free"
    fiduciary.state["license"]["active"] = False

    response = client.post("/api/license", json={"tier": "partner"})
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "partner"
    assert data["revenue_share_percentage"] == 0.50

def test_dashboard_unlicensed():
    # Reset state
    fiduciary.state["license"]["active"] = False

    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False
    assert data["status"] == "Pending License"

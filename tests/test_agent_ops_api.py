"""
Tests for agent-ops GUI API endpoints.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.blank_business_builder.gui_server import app, STATE_FILE, fiduciary

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
            "bypass_used": False,
        },
        "wallet": 0.0,
        "revenue_total": 0.0,
    }


def setup_function(function):
    reset_state()


def test_agent_ops_settings_get_and_patch():
    res = client.get("/api/v1/agent-ops/settings")
    assert res.status_code == 200
    data = res.json()
    assert "viktor_mode_enabled" in data
    assert "memory_db" in data

    patch_res = client.patch(
        "/api/v1/agent-ops/settings",
        json={"viktor_mode_enabled": True, "viktor_strategist_enabled": False},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["viktor_mode_enabled"] is True
    assert updated["viktor_strategist_enabled"] is False


def test_agent_ops_memory_seed_and_preview():
    seed = client.post("/api/v1/agent-ops/memory/seed", json={"overwrite": False})
    assert seed.status_code == 200
    body = seed.json()
    assert "seeded" in body
    assert body["semantic_count"] >= 0

    preview = client.get("/api/v1/agent-ops/memory")
    assert preview.status_code == 200
    pdata = preview.json()
    assert "status" in pdata
    assert "preview" in pdata


def test_proactive_schedule_and_inline_run():
    sched = client.get("/api/v1/agent-ops/proactive/schedule")
    assert sched.status_code == 200
    jobs = sched.json()["jobs"]
    assert any(j["job_id"] == "arxiv-ingest" for j in jobs)
    assert any(j["job_id"] == "daily-ops" for j in jobs)

    with patch(
        "src.blank_business_builder.agent_ops_service._celery_broker_reachable",
        return_value=False,
    ), patch(
        "src.blank_business_builder.agent_ops_service.ProactiveScheduler.run_job",
        new_callable=AsyncMock,
        return_value="mock proactive output",
    ):
        run = client.post(
            "/api/v1/agent-ops/proactive/run",
            json={"job_id": "daily-ops"},
        )
    assert run.status_code == 200
    assert run.json()["status"] in ("completed", "queued")

    runs = client.get("/api/v1/agent-ops/proactive/runs")
    assert runs.status_code == 200
    assert isinstance(runs.json()["runs"], list)


def test_chat_returns_viktor_flag():
    client.patch("/api/v1/agent-ops/settings", json={"viktor_mode_enabled": True})
    with patch(
        "src.blank_business_builder.gui_server.ech0.chat",
        new_callable=AsyncMock,
        return_value="hello from echo",
    ):
        res = client.post("/api/v1/chat", json={"message": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert data["viktor_mode"] is True
    assert "response" in data

"""Tests for agent memory seed and proactive Celery beat wiring."""

from pathlib import Path

from blank_business_builder.agent_memory import AgentMemoryStore
from blank_business_builder.agent_memory_seed import ensure_seeded, seed_workspace
from blank_business_builder.proactive_scheduler import ProactiveScheduler


def test_ensure_seeded_idempotent(tmp_path: Path):
    db = tmp_path / "mem.db"
    store = AgentMemoryStore(db_path=db)
    first = ensure_seeded(store, workspaces=["saas-micro-tools"])
    second = ensure_seeded(store, workspaces=["saas-micro-tools"])
    assert first["saas-micro-tools"] > 0
    assert second["saas-micro-tools"] == 0


def test_seed_overwrite(tmp_path: Path):
    store = AgentMemoryStore(db_path=tmp_path / "mem.db")
    seed_workspace(store, "saas-micro-tools", overwrite=False)
    store.upsert_semantic("saas-micro-tools", "company_mission", "OLD")
    n = seed_workspace(store, "saas-micro-tools", overwrite=True)
    assert n > 0
    chunks = store.retrieve("saas-micro-tools", "mission")
    assert any("micro-SaaS" in c.content for c in chunks)


def test_celery_beat_schedule_keys():
    sched = ProactiveScheduler().celery_beat_schedule()
    assert "viktor-arxiv-ingest" in sched
    assert "viktor-daily-ops" in sched
    assert sched["viktor-arxiv-ingest"]["task"] == "blank_business_builder.tasks.viktor_proactive_job"
    assert sched["viktor-arxiv-ingest"]["kwargs"]["job_id"] == "arxiv-ingest"

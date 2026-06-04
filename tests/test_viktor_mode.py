"""Tests for Viktor mode: memory, ambiguity, protocol council (mock LLM)."""

import asyncio
from pathlib import Path

import pytest

from blank_business_builder.agent_memory import AgentMemoryStore
from blank_business_builder.protocol_council import ProtocolCouncil
from blank_business_builder.viktor_execution import (
    PreparedMission,
    ViktorExecutor,
    needs_strategist_pass,
    score_ambiguity,
)


@pytest.fixture
def memory_db(tmp_path: Path) -> AgentMemoryStore:
    return AgentMemoryStore(db_path=tmp_path / "mem.db")


def test_semantic_and_episodic_memory(memory_db: AgentMemoryStore):
    memory_db.upsert_semantic("ws", "slack_mktg", "Marketing channel is #mktg")
    memory_db.write_episode(
        "ws",
        "Shipped landing page v2",
        assumptions=["used Next.js"],
        outcome="success",
    )
    block = memory_db.context_block("ws", "marketing slack")
    assert "mktg" in block.lower() or "marketing" in block.lower()


def test_ambiguity_scoring():
    assert score_ambiguity("build the landing page for tool X") < score_ambiguity("maybe do X or Y?")
    assert needs_strategist_pass("create a quarterly roadmap for three products with tradeoffs")


@pytest.mark.asyncio
async def test_viktor_executor_completes():
    calls = {"n": 0}

    async def fake_gen(prompt: str, system=None) -> str:
        calls["n"] += 1
        if "Reflect" in prompt or "related proactive" in prompt:
            return '["noticed stale CI config"]' if "related" in prompt else "matched expectation"
        return (
            '{"think":"done","action":"complete","complete":true,'
            '"final_output":"Task finished.","assumptions":["used default branch"],'
            '"confidence":0.9}'
        )

    mission = PreparedMission(
        raw_request="fix tests",
        crystallized_intent="Run pytest and fix failures",
        constraints=["no force push"],
    )
    ex = ViktorExecutor(fake_gen, max_steps=3)
    result = await ex.run(mission)
    assert result.success
    assert "finished" in result.output.lower() or result.output
    assert result.assumptions


@pytest.mark.asyncio
async def test_protocol_council_pipeline(memory_db: AgentMemoryStore):
    stage = {"crystalline": 0, "strategist": 0, "execute": 0}

    async def fake_gen(prompt: str, system=None) -> str:
        sys = system or ""
        if "ReAct" in prompt or ("Step " in prompt and "complete" in prompt):
            stage["execute"] += 1
            return (
                '{"think":"ok","action":"complete","complete":true,'
                '"final_output":"Deployed to staging.","assumptions":[],"confidence":0.9}'
            )
        if "related proactive" in prompt:
            return "[]"
        if "Reflect" in prompt:
            return "matched expectation"
        if "Crystalline" in sys:
            stage["crystalline"] += 1
            return (
                '{"core_intent":"Deploy staging","constraints":["no prod"],'
                '"assumptions":["staging env exists"],"confidence":0.85}'
            )
        if "Strategist" in sys or "Parliament" in sys:
            stage["strategist"] += 1
            return (
                '{"parliament_consensus":"moderate","consensus_score":5,'
                '"recommended_path":"build, test, deploy",'
                '"cascade_insight":"infra is the bottleneck","tensor_insights":["temporal: high"],'
                '"risks":["downtime"],"dissent":"none"}'
            )
        if "Prediction Oracle" in sys:
            return '{"robust_strategy":"canary","branches":[]}'
        return '{"think":"reflect","action":"complete","complete":true,"final_output":"ok"}'

    council = ProtocolCouncil(
        fake_gen,
        memory=memory_db,
        workspace="test-ws",
        enable_oracle=False,
    )
    result = await council.run_task(
        "Plan and deploy the new micro-tool to staging with a full roadmap",
        system_context="company context",
        agent_id="exec",
        task_id="t1",
    )
    assert stage["crystalline"] >= 1
    assert stage["strategist"] >= 1
    assert stage["execute"] >= 1
    assert "Done" in result.output or "Deployed" in result.output

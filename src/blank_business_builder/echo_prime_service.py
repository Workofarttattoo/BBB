"""
Internal echo_prime steering service.

This app runs as a private Kubernetes service. BBB calls it for outreach
decisions while keeping deterministic fallback logic in the public API process.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from .echo_master_brain import EchoMasterBrain


app = FastAPI(
    title="echo_prime Steering Service",
    description="Private decisioning service for Better Business Builder.",
    version="1.0.0",
)


class OutreachDecisionRequest(BaseModel):
    lead_event: Dict[str, Any]


class PostCallDecisionRequest(BaseModel):
    call_event: Dict[str, Any]


def _clamp_priority(priority: int) -> int:
    return max(0, min(priority, 100))


def _priority_for_department(department: str, has_phone: bool) -> int:
    base_priority = {
        "exec": 90,
        "marketing": 78,
        "ops": 74,
        "support": 68,
        "sales": 72,
    }.get(department, 70)
    return _clamp_priority(base_priority if has_phone else base_priority - 20)


def _steering_department(lead_event: Dict[str, Any]) -> str:
    text = " ".join(
        [
            str(lead_event.get("title", "")),
            str(lead_event.get("company", "")),
            str(lead_event.get("notes", "")),
        ]
    ).lower()
    if any(token in text for token in ("marketing", "growth", "brand", "demand gen")):
        return "marketing"
    if any(token in text for token in ("finance", "cfo", "board", "vp", "ceo")):
        return "exec"
    if any(token in text for token in ("support", "helpdesk", "success")):
        return "support"
    if any(token in text for token in ("ops", "operations", "supply")):
        return "ops"
    return "sales"


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "echo_prime",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/internal/echo/outreach-decision")
@app.post("/v1/outreach/decision")
@app.post("/outreach/decision")
async def outreach_decision(request: OutreachDecisionRequest) -> Dict[str, Any]:
    lead_event = request.lead_event
    department = _steering_department(lead_event)
    full_name = lead_event.get("full_name") or "there"
    company = lead_event.get("company") or "your team"
    title = lead_event.get("title") or "prospect"
    notes = lead_event.get("notes") or ""
    has_phone = bool(lead_event.get("phone"))

    task = (
        f"Call {full_name} at {company}. Open with their {title} context, "
        "qualify business pain, confirm urgency, and secure the next-step meeting."
    )
    if notes:
        task = f"{task} Lead notes: {notes}"

    return {
        "source": "echo_prime",
        "steered_by": "echo_prime",
        "department": department,
        "outreach_priority": _priority_for_department(department, has_phone),
        "should_call": has_phone,
        "task": task,
        "script": (
            "Use concise discovery: confirm role, ask about the highest-friction "
            "workflow, quantify impact, then offer a concrete implementation review."
        ),
        "slack_summary": f"echo_prime routed {full_name} ({company}) to {department}.",
        "next_action": "queue_follow_up" if has_phone else "enrich_phone",
    }


@app.post("/internal/echo/post-call-decision")
@app.post("/v1/outreach/post-call")
@app.post("/outreach/post-call")
async def post_call_decision(request: PostCallDecisionRequest) -> Dict[str, Any]:
    call_event = request.call_event
    status = str(call_event.get("status", "")).lower()
    transcript = " ".join(
        str(call_event.get(key) or "")
        for key in ("transcript", "summary", "outcome")
    ).lower()
    department = str(call_event.get("department") or "sales").lower()

    if status in {"completed", "success"} and any(
        token in transcript for token in ("interested", "book", "meeting", "demo", "proposal")
    ):
        next_action = "schedule_meeting"
        follow_up_minutes = 30
        summary = "echo_prime detected buying intent. Meeting follow-up queued."
    elif any(token in transcript for token in ("not now", "later", "next quarter")):
        next_action = "nurture"
        follow_up_minutes = 7 * 24 * 60
        summary = "echo_prime detected delayed timing. Long nurture queued."
    else:
        next_action = "nurture"
        follow_up_minutes = 24 * 60
        summary = "echo_prime completed call review. Standard nurture queued."

    return {
        "source": "echo_prime",
        "steered_by": "echo_prime",
        "next_action": next_action,
        "follow_up_in_minutes": follow_up_minutes,
        "department": department,
        "slack_summary": summary,
    }

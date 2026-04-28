"""
Private Echo Prime API for in-cluster BBB reasoning.

This service exposes the internal decision routes used by BBB's
EchoMasterBrain client. It keeps deterministic fallback behavior available even
when an external LLM endpoint is unavailable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .echo_master_brain import EchoMasterBrain
from .ech0_service import ECH0Service


app = FastAPI(
    title="Echo Prime API",
    description="Private reasoning service for BBB autonomous operations",
    version="1.0.0",
)

brain = EchoMasterBrain(base_url="")
ech0_service = ECH0Service()


class OutreachDecisionRequest(BaseModel):
    lead_event: Dict[str, Any] = Field(default_factory=dict)


class PostCallDecisionRequest(BaseModel):
    call_event: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Kubernetes health endpoint."""
    return {
        "service": "echo-prime",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/internal/echo/outreach-decision")
@app.post("/v1/outreach/decision")
@app.post("/outreach/decision")
async def decide_outreach(request: OutreachDecisionRequest) -> Dict[str, Any]:
    """Choose outbound department, priority, script, and next action."""
    return brain.decide_outreach(request.lead_event)


@app.post("/internal/echo/post-call-decision")
@app.post("/v1/outreach/post-call")
@app.post("/outreach/post-call")
async def decide_post_call_action(request: PostCallDecisionRequest) -> Dict[str, Any]:
    """Choose follow-up action after a call provider posts final results."""
    return brain.decide_post_call_action(request.call_event)


@app.post("/v1/chat")
async def chat(request: ChatRequest) -> Dict[str, str]:
    """Small private chat endpoint for operational checks and future tools."""
    response = await ech0_service.chat(request.message)
    return {"response": response}

"""
Private Echo Prime API for in-cluster BBB reasoning.

This service exposes the internal decision routes used by BBB's
EchoMasterBrain client. It keeps deterministic fallback behavior available even
when an external LLM endpoint is unavailable.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .bbb_unified_business_library import BBBUnifiedLibrary
from .echo_master_brain import EchoMasterBrain
from .ech0_service import ECH0Service
from .ech0_prime_validation import BBBParliamentValidator


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


class RecommendationRequest(BaseModel):
    budget: int = Field(..., ge=0)
    available_hours_week: int = Field(..., ge=0)
    experience_level: str = "beginner"
    preferred_categories: Optional[List[str]] = None


class ValidateBusinessRequest(BaseModel):
    business_name: str


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


@app.get("/v1/businesses/summary")
async def business_summary() -> Dict[str, Any]:
    """Return BBB's packaged business-library summary for cloud checks."""
    return BBBUnifiedLibrary().generate_summary_report()


@app.post("/v1/businesses/recommendations")
async def business_recommendations(request: RecommendationRequest) -> Dict[str, Any]:
    """Rank BBB businesses using installable library data."""
    recommendations = BBBUnifiedLibrary().get_recommendations(
        budget=request.budget,
        available_hours_week=request.available_hours_week,
        experience_level=request.experience_level,
        preferred_categories=request.preferred_categories,
    )
    return {
        "recommendations": [
            {
                "business": item["business"].to_dict(),
                "match_score": item["match_score"],
            }
            for item in recommendations
        ]
    }


@app.post("/v1/businesses/validate")
async def validate_business(request: ValidateBusinessRequest) -> Dict[str, Any]:
    """Run Echo Prime truth and Parliament validation for a named BBB business."""
    library = BBBUnifiedLibrary()
    business = next(
        (
            candidate
            for candidate in library.get_all_businesses()
            if candidate.name.lower() == request.business_name.lower()
        ),
        None,
    )
    if business is None:
        return {"overall_status": "NOT_FOUND", "business_name": request.business_name}
    return await BBBParliamentValidator().validate_business_model(business)


def build_echo_prime_router():
    """Expose Echo Prime routes inside BBB for single-process cloud runtimes."""
    from fastapi import APIRouter

    router = APIRouter(prefix="/api/v1/echo-prime", tags=["echo-prime"])

    @router.get("/health")
    async def embedded_health_check() -> Dict[str, str]:
        return await health_check()

    @router.get("/businesses/summary")
    async def embedded_business_summary() -> Dict[str, Any]:
        return await business_summary()

    @router.post("/businesses/recommendations")
    async def embedded_business_recommendations(request: RecommendationRequest) -> Dict[str, Any]:
        return await business_recommendations(request)

    @router.post("/businesses/validate")
    async def embedded_validate_business(request: ValidateBusinessRequest) -> Dict[str, Any]:
        return await validate_business(request)

    @router.post("/chat")
    async def embedded_chat(request: ChatRequest) -> Dict[str, str]:
        return await chat(request)

    return router

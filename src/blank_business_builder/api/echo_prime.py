"""BBB-facing routes that proxy packaged Echo Prime capabilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..bbb_unified_business_library import BBBUnifiedLibrary
from ..config import settings
from ..ech0_prime_validation import BBBParliamentValidator
from ..ech0_service import ECH0Service

router = APIRouter(prefix="/api/v1/echo-prime", tags=["echo-prime"])


class EchoPrimeChatRequest(BaseModel):
    message: str


class EchoPrimeRecommendationRequest(BaseModel):
    budget: int = Field(..., ge=0)
    available_hours_week: int = Field(..., ge=0)
    experience_level: str = "beginner"
    preferred_categories: Optional[List[str]] = None


class EchoPrimeValidationRequest(BaseModel):
    business_name: str


@router.get("/health")
async def echo_prime_health() -> Dict[str, Any]:
    """Return package-level readiness for BBB's Echo Prime integration."""
    summary = BBBUnifiedLibrary().generate_summary_report()
    return {
        "service": "echo-prime",
        "status": "healthy",
        "businesses_available": summary["total_businesses"],
        "llm_provider": settings.ECH0_LLM_PROVIDER,
        "cloud_inference": "configured" if settings.ECH0_LLM_ENDPOINT else "local",
    }


@router.get("/businesses/summary")
async def business_summary() -> Dict[str, Any]:
    return BBBUnifiedLibrary().generate_summary_report()


@router.post("/businesses/recommendations")
async def business_recommendations(request: EchoPrimeRecommendationRequest) -> Dict[str, Any]:
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


@router.post("/businesses/validate")
async def validate_business(request: EchoPrimeValidationRequest) -> Dict[str, Any]:
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


@router.post("/chat")
async def chat(request: EchoPrimeChatRequest) -> Dict[str, str]:
    return {"response": await ECH0Service().chat(request.message)}

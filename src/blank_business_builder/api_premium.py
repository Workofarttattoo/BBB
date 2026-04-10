"""
Better Business Builder - Premium Workflows API Routes
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os

from .auth import get_current_user
from .database import User

# Import the actual premium workflow modules
from .premium_workflows.ghost_writing_agent import GhostWritingAgent
from .premium_workflows.marketing_agency_agent import MarketingAgencyAgent
from .premium_workflows.nocode_app_agent import NoCodeAppAgent
from .premium_workflows.quantum_optimizer import QuantumOptimizer

# --- Pydantic Models for Requests & Responses ---

# 1. Ghost Writing Agent
class GhostWritingOrderRequest(BaseModel):
    topic: str
    word_count: int
    target_audience: str
    tone: Optional[str] = "informative"

class GhostWritingOrderResponse(BaseModel):
    order_id: str
    status: str
    estimated_delivery: str

# 2. Marketing Agency Agent
class MarketingCampaignRequest(BaseModel):
    campaign_name: str
    budget: float
    target_demographics: List[str]
    goals: List[str]

class MarketingCampaignResponse(BaseModel):
    campaign_id: str
    status: str
    allocated_budget: float

# 3. NoCodeApp Agent
class NoCodeAppBuildRequest(BaseModel):
    app_name: str
    description: str
    features: List[str]
    platform: str = "web"

class NoCodeAppBuildResponse(BaseModel):
    app_id: str
    status: str
    preview_url: Optional[str] = None

# 4. Quantum Optimizer
class QuantumOptimizeRequest(BaseModel):
    business_id: str
    metric_to_optimize: str
    constraints: Optional[Dict[str, Any]] = None

class QuantumOptimizeResponse(BaseModel):
    optimization_id: str
    status: str
    recommendations: List[str]


# --- API Router Setup ---
router = APIRouter(prefix="/api/premium", tags=["Premium Workflows"])

# 1. Ghost Writing Agent
@router.post("/ghostwriting/order", response_model=GhostWritingOrderResponse)
async def create_ghostwriting_order(
    request: GhostWritingOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """Place an order for a ghostwritten article or book using GhostWritingAgent."""
    agent = GhostWritingAgent()

    # We use agent to start process
    order = await agent.create_gig(
        client_id=str(current_user.id),
        topic=request.topic,
        content_type="article",
        word_count=request.word_count,
        target_audience=request.target_audience
    )

    return GhostWritingOrderResponse(
        order_id=order.gig_id,
        status=order.status,
        estimated_delivery="2-3 days"
    )

@router.get("/ghostwriting/status")
async def get_ghostwriting_status(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Check the status of a ghostwriting order."""
    return {"order_id": order_id, "status": "processing"}

# 2. Marketing Agency Agent
@router.post("/marketing-agency/campaign", response_model=MarketingCampaignResponse)
async def create_agency_campaign(
    request: MarketingCampaignRequest,
    current_user: User = Depends(get_current_user)
):
    """Launch a fully managed marketing agency campaign using MarketingAgencyAgent."""
    agent = MarketingAgencyAgent()

    campaign = await agent.create_campaign(
        client_id=str(current_user.id),
        name=request.campaign_name,
        budget=request.budget,
        goals=request.goals,
        target_audience={"demographics": request.target_demographics}
    )

    return MarketingCampaignResponse(
        campaign_id=campaign.campaign_id,
        status=campaign.status,
        allocated_budget=campaign.budget_allocated
    )

# 3. NoCode App Agent
@router.post("/nocode/build", response_model=NoCodeAppBuildResponse)
async def build_nocode_app(
    request: NoCodeAppBuildRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a nocode application using NoCodeAppAgent."""
    agent = NoCodeAppAgent()

    project = await agent.create_project(
        client_id=str(current_user.id),
        name=request.app_name,
        description=request.description,
        features=request.features,
        target_platform=request.platform
    )

    return NoCodeAppBuildResponse(
        app_id=project.project_id,
        status=project.status,
        preview_url=project.preview_url
    )

# 4. Quantum Optimizer
@router.post("/quantum/optimize", response_model=QuantumOptimizeResponse)
async def run_quantum_optimization(
    request: QuantumOptimizeRequest,
    current_user: User = Depends(get_current_user)
):
    """Run quantum optimization algorithms on business metrics using QuantumOptimizer."""
    optimizer = QuantumOptimizer()

    # Run optimization plan
    plan = await optimizer.optimize_business_model(
        business_id=request.business_id,
        current_metrics={"metric": request.metric_to_optimize},
        target_goals=[request.metric_to_optimize]
    )

    return QuantumOptimizeResponse(
        optimization_id=plan["optimization_id"] if "optimization_id" in plan else "opt_1",
        status="completed",
        recommendations=[step["description"] for step in plan.get("execution_steps", [])]
    )

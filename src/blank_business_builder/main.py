"""
Better Business Builder - FastAPI Application
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import uvicorn
import os
from pathlib import Path

from .database import get_db, User, Business, BusinessPlan, MarketingCampaign
from .auth import (
    AuthService,
    get_current_user,
    RoleBasedAccessControl,
    rate_limit,
    require_license_access,
    require_quantum_access
)
from .payments import StripeService, handle_webhook_event
from .integrations import IntegrationFactory
from .self_healing import build_self_healing_orchestrator, self_healing_enabled
from pydantic import BaseModel
try:
    from pydantic import EmailStr as _EmailStr  # type: ignore
    from pydantic.networks import import_email_validator  # type: ignore
    import_email_validator()
    EmailStr = _EmailStr
except Exception:  # pragma: no cover
    EmailStr = str  # type: ignore

# Initialize FastAPI app
app = FastAPI(
    title="Better Business Builder API",
    description="AI-powered business planning and marketing automation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def start_self_healing():
    if not self_healing_enabled():
        return
    orchestrator = build_self_healing_orchestrator()
    app.state.self_healing_orchestrator = orchestrator
    app.state.self_healing_task = asyncio.create_task(orchestrator.run())


@app.on_event("shutdown")
async def stop_self_healing():
    orchestrator = getattr(app.state, "self_healing_orchestrator", None)
    task = getattr(app.state, "self_healing_task", None)
    if orchestrator:
        await orchestrator.stop()
    if task:
        task.cancel()

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[2]
LAB_PAGES = {
    "business-builder": PACKAGE_DIR / "business_builder_gui.html",
    "dashboard": PACKAGE_DIR / "dashboard.html",
    "quantum-features": PACKAGE_DIR / "quantum_features_dashboard.html",
    "bbb-realtime": REPO_ROOT / "bbb_realtime_dashboard.html",
    "bbb-unified-library": REPO_ROOT / "bbb_unified_library_dashboard.html",
    "disaster-recovery": REPO_ROOT / "disaster_recovery_dashboard.html",
    "quantum-analysis": REPO_ROOT / "quantum_analysis_dashboard.html",
    "test-dashboard": REPO_ROOT / "test_dashboard.html",
    "website-status": REPO_ROOT / "website_status_dashboard.html",
    "zero-touch-businesses": REPO_ROOT / "zero_touch_businesses_dashboard.html",
}
LAB_ASSETS = {
    "quantum_optimization_results.json": REPO_ROOT / "quantum_optimization_results.json",
    "PHASE_2_COMPLETE.md": REPO_ROOT / "PHASE_2_COMPLETE.md",
}


@app.get("/labs")
async def list_labs():
    """List available lab dashboards."""
    return {
        "labs": [
            {"slug": slug, "path": f"/labs/{slug}"}
            for slug in sorted(LAB_PAGES.keys())
        ]
    }


@app.get("/labs/{lab_slug}")
async def serve_lab(lab_slug: str):
    """Serve lab dashboards as static HTML."""
    lab_path = LAB_PAGES.get(lab_slug)
    if not lab_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found.")
    if not lab_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab file missing on server."
        )
    return FileResponse(lab_path)


@app.get("/labs/assets/{asset_name}")
async def serve_lab_asset(asset_name: str):
    """Serve data files referenced by lab dashboards."""
    asset_path = LAB_ASSETS.get(asset_name)
    if not asset_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    if not asset_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file missing on server."
        )
    return FileResponse(asset_path)


# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class BusinessCreate(BaseModel):
    business_name: str
    industry: str
    description: str
    website_url: Optional[str] = None


class BusinessPlanGenerate(BaseModel):
    business_id: str
    target_market: Optional[str] = None


class MarketingCopyGenerate(BaseModel):
    business_id: str
    platform: str
    campaign_goal: str
    target_audience: str
    tone: str = "professional"


class EmailCampaignGenerate(BaseModel):
    business_id: str
    campaign_goal: str
    target_audience: str
    key_points: List[str]


class LicenseActivateRequest(BaseModel):
    tier: str  # starter, pro, enterprise
    agreed_terms_version: str = "v1"


class RevenueShareAcceptRequest(BaseModel):
    percentage: float = 50.0
    agreed_terms_version: str = "v1"


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Authentication endpoints
@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_password = AuthService.hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        subscription_tier="free",
        license_status="trial",
        trial_expires_at=datetime.utcnow() + timedelta(days=7),
        revenue_share_percentage=None,
        license_terms_version="v1"
    )

    # Create Stripe customer
    try:
        stripe_customer = StripeService.create_customer(
            email=user_data.email,
            name=user_data.full_name,
            metadata={"source": "better_business_builder"}
        )
        new_user.stripe_customer_id = stripe_customer.id
    except:
        pass  # Continue without Stripe if it fails

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(new_user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(new_user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user."""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not AuthService.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "subscription_tier": current_user.subscription_tier,
        "license_status": current_user.license_status,
        "license_agreed_at": current_user.license_agreed_at.isoformat() if current_user.license_agreed_at else None,
        "trial_expires_at": current_user.trial_expires_at.isoformat() if current_user.trial_expires_at else None,
        "revenue_share_percentage": float(current_user.revenue_share_percentage) if current_user.revenue_share_percentage else None,
        "created_at": current_user.created_at.isoformat()
    }


# Business endpoints
@app.post("/api/businesses")
async def create_business(
    business_data: BusinessCreate,
    current_user: User = Depends(require_license_access),
    db: Session = Depends(get_db)
):
    """Create a new business."""
    # Check subscription limits
    business_count = db.query(Business).filter(Business.user_id == current_user.id).count()

    if not RoleBasedAccessControl.check_permission(
        current_user.subscription_tier, "businesses", business_count
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Business limit reached for {current_user.subscription_tier} tier"
        )

    new_business = Business(
        user_id=current_user.id,
        business_name=business_data.business_name,
        business_concept=business_data.business_name,
        industry=business_data.industry,
        description=business_data.description,
        website_url=business_data.website_url,
        status="active"
    )

    db.add(new_business)
    db.commit()
    db.refresh(new_business)

    return {
        "id": str(new_business.id),
        "business_name": new_business.business_name,
        "industry": new_business.industry,
        "status": new_business.status
    }


@app.get("/api/businesses")
async def list_businesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's businesses."""
    businesses = db.query(Business).filter(Business.user_id == current_user.id).all()

    return [
        {
            "id": str(b.id),
            "business_name": b.business_name,
            "industry": b.industry,
            "status": b.status,
            "created_at": b.created_at.isoformat()
        }
        for b in businesses
    ]


# AI-powered endpoints
@app.post("/api/ai/generate-business-plan")
@rate_limit(max_requests=10, window_seconds=3600)
async def generate_business_plan(
    request_data: BusinessPlanGenerate,
    current_user: User = Depends(require_license_access),
    db: Session = Depends(get_db)
):
    """Generate business plan using AI."""
    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == request_data.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Generate plan using OpenAI
    openai_service = IntegrationFactory.get_openai_service()
    plan_data = openai_service.generate_business_plan(
        business_name=business.business_name,
        industry=business.industry,
        description=business.description,
        target_market=request_data.target_market
    )

    # Save plan to database
    business_plan = BusinessPlan(
        business_id=business.id,
        plan_name=f"{business.business_name} Plan - {datetime.utcnow().strftime('%Y-%m-%d')}",
        executive_summary=plan_data.get("executive_summary"),
        market_analysis=plan_data.get("market_analysis"),
        financial_projections=plan_data.get("financial_projections"),
        marketing_strategy=plan_data.get("marketing_strategy"),
        operations_plan=plan_data.get("operations_plan")
    )

    db.add(business_plan)
    db.commit()
    db.refresh(business_plan)

    return {
        "id": str(business_plan.id),
        "plan_data": plan_data
    }


@app.post("/api/ai/generate-marketing-copy")
@rate_limit(max_requests=20, window_seconds=3600)
async def generate_marketing_copy(
    request_data: MarketingCopyGenerate,
    current_user: User = Depends(require_license_access),
    db: Session = Depends(get_db)
):
    """Generate marketing copy using AI."""
    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == request_data.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Generate copy using OpenAI
    openai_service = IntegrationFactory.get_openai_service()
    marketing_copy = openai_service.generate_marketing_copy(
        business_name=business.business_name,
        platform=request_data.platform,
        campaign_goal=request_data.campaign_goal,
        target_audience=request_data.target_audience,
        tone=request_data.tone
    )

    return {
        "platform": request_data.platform,
        "copy": marketing_copy
    }


@app.post("/api/ai/generate-email-campaign")
@rate_limit(max_requests=10, window_seconds=3600)
async def generate_email_campaign(
    request_data: EmailCampaignGenerate,
    current_user: User = Depends(require_license_access),
    db: Session = Depends(get_db)
):
    """Generate email campaign using AI."""
    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == request_data.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Generate email using OpenAI
    openai_service = IntegrationFactory.get_openai_service()
    email_data = openai_service.generate_email_campaign(
        business_name=business.business_name,
        campaign_goal=request_data.campaign_goal,
        target_audience=request_data.target_audience,
        key_points=request_data.key_points
    )

    return email_data


# Payment endpoints
@app.post("/api/payments/create-checkout-session")
async def create_checkout_session(
    plan_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session."""
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe customer not found"
        )

    # Get price ID for plan (these would be configured in Stripe dashboard)
    price_ids = {
        "starter": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise")
    }

    price_id = price_ids.get(plan_name)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan name"
        )

    # Create checkout session
    session = StripeService.create_checkout_session(
        customer_id=current_user.stripe_customer_id,
        price_id=price_id,
        success_url="https://betterbusinessbuilder.com/success",
        cancel_url="https://betterbusinessbuilder.com/cancel",
        trial_days=7,
        metadata={"user_id": str(current_user.id)}
    )

    return {"checkout_url": session.url}


@app.post("/api/payments/create-portal-session")
async def create_portal_session(
    current_user: User = Depends(require_license_access),
    db: Session = Depends(get_db)
):
    """Create Stripe billing portal session."""
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe customer not found"
        )

    session = StripeService.create_billing_portal_session(
        customer_id=current_user.stripe_customer_id,
        return_url="https://betterbusinessbuilder.com/dashboard"
    )

    return {"portal_url": session.url}


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = StripeService.verify_webhook_signature(payload, sig_header)
        handle_webhook_event(event, db)
        return {"status": "success"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# WebSocket endpoint
from .websockets import websocket_endpoint

@app.websocket("/ws/dashboard/{business_id}")
async def dashboard_websocket(websocket: WebSocket, business_id: str, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time dashboard."""
    await websocket_endpoint(websocket, business_id, token, db)


# Metrics endpoint
from .metrics import metrics_endpoint, metrics_middleware

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


# Add metrics middleware
app.middleware("http")(metrics_middleware)


# Include Quantum Features API Router
# Quantum endpoints require Pro tier or higher
from .api_quantum_features import router as quantum_router
from .api_licensing import router as licensing_router

app.include_router(quantum_router)
app.include_router(licensing_router)


# License endpoints
@app.get("/api/license/status")
async def license_status(current_user: User = Depends(get_current_user)):
    """Return current license status for authenticated user."""
    return {
        "license_status": current_user.license_status,
        "subscription_tier": current_user.subscription_tier,
        "license_terms_version": current_user.license_terms_version,
        "license_agreed_at": current_user.license_agreed_at.isoformat() if current_user.license_agreed_at else None,
        "trial_expires_at": current_user.trial_expires_at.isoformat() if current_user.trial_expires_at else None,
        "revenue_share_percentage": float(current_user.revenue_share_percentage) if current_user.revenue_share_percentage else None
    }


@app.post("/api/license/accept-revenue-share")
async def accept_revenue_share(
    request: RevenueShareAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept revenue share agreement to unlock the platform."""
    if request.percentage < 1 or request.percentage > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revenue share percentage must be between 1 and 90."
        )

    current_user.license_status = "revenue_share"
    current_user.revenue_share_percentage = request.percentage
    current_user.license_agreed_at = datetime.utcnow()
    current_user.license_terms_version = request.agreed_terms_version
    current_user.trial_expires_at = None

    if current_user.subscription_tier == "free":
        current_user.subscription_tier = "starter"

    db.commit()
    db.refresh(current_user)

    return {
        "status": "accepted",
        "license_status": current_user.license_status,
        "revenue_share_percentage": float(current_user.revenue_share_percentage)
    }


@app.post("/api/license/activate")
async def activate_license(
    request: LicenseActivateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate paid license."""
    tier = request.tier.lower()
    if tier not in {"starter", "pro", "enterprise"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license tier."
        )

    current_user.license_status = "licensed"
    current_user.subscription_tier = tier
    current_user.license_agreed_at = datetime.utcnow()
    current_user.license_terms_version = request.agreed_terms_version
    current_user.trial_expires_at = None
    current_user.revenue_share_percentage = None

    db.commit()
    db.refresh(current_user)

    return {
        "status": "activated",
        "license_status": current_user.license_status,
        "subscription_tier": current_user.subscription_tier
    }


# Run application
if __name__ == "__main__":
    import os

    # Secure defaults: debug mode disabled, environment is production
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # Only enable reload in development environment
    should_reload = debug_mode or environment == "development"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=should_reload
    )

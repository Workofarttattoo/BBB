"""
FastAPI Backend for the Blank Business Builder GUI.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import json
import logging
import os
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .business_data import BusinessIdea, default_ideas
from .fiduciary import FiduciaryManager
from .features.market_research import MarketResearch
from .ech0_service import ECH0Service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Business Builder API")

# Initialize Services
ech0 = ECH0Service()

# CORS configuration
cors_origins_str = os.getenv("CORS_ORIGINS", "")
if cors_origins_str:
    allow_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
else:
    allow_origins = []

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Fiduciary Manager
fiduciary = FiduciaryManager()

# --- Pydantic Models ---

class ProfileModel(BaseModel):
    name: str
    location_state: str
    preferred_industry: str
    weekly_hours: int
    startup_budget: float
    risk_posture: str

class LicenseRequest(BaseModel):
    tier: str  # "partner" or "paid"

class BypassRequest(BaseModel):
    code: str

class BusinessSelection(BaseModel):
    business_name: str

class ChatRequest(BaseModel):
    message: str

class AcquisitionSetupRequest(BaseModel):
    target_customer: str
    lead_keywords: str
    service_offer: str
    github_repo_url: Optional[str] = None
    github_pages_url: Optional[str] = None
    google_workspace_email: Optional[str] = None
    google_drive_folder_url: Optional[str] = None
    apollo_api_key: Optional[str] = None
    bland_api_key: Optional[str] = None
    bland_webhook_url: Optional[str] = None

# --- State Management (Simple In-Memory + JSON Sync) ---
STATE_FILE = "business_state.json"

def get_app_state():
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def update_app_state(key: str, value: any):
    state = get_app_state()
    state[key] = value

    # Reload to get latest license info
    current_state = fiduciary._load_state()
    current_state[key] = value

    with open(STATE_FILE, "w") as f:
        json.dump(current_state, f, indent=2)

    # Reload fiduciary so it sees the changes
    fiduciary.state = fiduciary._load_state()

# --- Real Analysis Engine ---

class RealAnalysisEngine:
    """Performs real-time evaluation of business concepts against user constraints."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.budget = float(profile.get("startup_budget", 10000))
        self.hours = float(profile.get("weekly_hours", 40))
        self.industry = profile.get("preferred_industry", "")
        self.state = profile.get("location_state", "Unknown")
        self.risk = profile.get("risk_posture", "balanced")

        # Try to initialize real market research if keys are present (env vars would be needed)
        self.researcher = MarketResearch(api_key="")

    async def evaluate_ideas(self) -> Dict[str, any]:
        """Run comprehensive analysis on all available business ideas."""
        logs = []
        logs.append(f"Initiating analysis for {self.profile['name']} in {self.state}...")

        # 1. Fetch Candidates
        candidates = default_ideas()
        logs.append(f"Loaded {len(candidates)} potential business models from internal database.")

        scored_candidates = []

        for idea in candidates:
            score = 0
            reasons = []

            # Constraint: Budget
            if idea.startup_cost > self.budget * 1.2:
                reasons.append(f"Over Budget (${idea.startup_cost} > ${self.budget})")
                score -= 100 # Hard reject
            else:
                score += 20
                if idea.startup_cost < self.budget * 0.5:
                    score += 10 # Bonus for being well under budget

            # Constraint: Time
            if idea.time_commitment_hours_per_week > self.hours * 1.2:
                reasons.append(f"Requires too much time ({idea.time_commitment_hours_per_week}h > {self.hours}h)")
                score -= 100
            else:
                score += 20

            # Constraint: Industry
            if self.industry and self.industry != "Generalist":
                if self.industry in idea.industry:
                    score += 30
                    reasons.append(f"Matches preferred industry: {self.industry}")
                else:
                    score -= 10

            # Factor: Profitability vs Risk
            roi = (idea.expected_monthly_revenue - idea.expected_monthly_expenses) / (idea.startup_cost + 1)
            if self.risk == "bold":
                score += roi * 10
            elif self.risk == "conservative":
                if idea.startup_cost < 2000:
                    score += 15
                else:
                    score -= 5

            # Logging specific decisions
            if score > 0:
                logs.append(f"Evaluating '{idea.name}': Fit Score {score:.1f}. {', '.join(reasons)}")
            else:
                logs.append(f"Rejected '{idea.name}': {', '.join(reasons)}")

            if score > 0:
                scored_candidates.append({"idea": asdict(idea), "score": score})

        # 2. Sort results
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_3 = [item["idea"] for item in scored_candidates[:3]]

        logs.append(f"Analysis complete. Identified {len(top_3)} optimal candidates.")

        return {
            "logs": logs,
            "recommendations": top_3
        }

def _link_runtime_env(request: AcquisitionSetupRequest) -> Dict[str, bool]:
    """Load provided tool keys into this Uvicorn process without writing secrets to disk."""
    if request.apollo_api_key:
        os.environ["APOLLO_API_KEY"] = request.apollo_api_key
    if request.bland_api_key:
        os.environ["BLAND_API_KEY"] = request.bland_api_key

    return {
        "apollo_configured": bool(os.getenv("APOLLO_API_KEY")),
        "bland_configured": bool(os.getenv("BLAND_API_KEY")),
        "github_pages_configured": bool(request.github_pages_url or request.github_repo_url),
        "google_workspace_configured": bool(request.google_workspace_email),
        "google_drive_configured": bool(request.google_drive_folder_url),
    }

def _build_acquisition_run(state: Dict[str, Any], setup: Dict[str, Any]) -> Dict[str, Any]:
    selected_business = state.get("selected_business", "Unknown Business")
    profile = state.get("profile", {})
    env_status = setup["env_status"]
    target_customer = setup["target_customer"]
    lead_keywords = setup["lead_keywords"]
    service_offer = setup["service_offer"]

    return {
        "business_name": selected_business,
        "status": "running",
        "toolchain": {
            "headhunter": {
                "provider": "Apollo.io",
                "status": "ready" if env_status["apollo_configured"] else "needs_api_key",
                "query": f"{lead_keywords} in {profile.get('location_state', 'target market')}",
                "target_customer": target_customer,
                "planned_leads": 25,
            },
            "bland": {
                "provider": "Bland",
                "status": "ready" if env_status["bland_configured"] else "needs_api_key",
                "outreach_goal": f"Book discovery calls for {service_offer}",
                "webhook_url": setup.get("bland_webhook_url") or "/api/webhooks/bland/post-call",
            },
            "website": {
                "provider": "GitHub Pages",
                "status": "ready" if env_status["github_pages_configured"] else "needs_github_pages_url",
                "repo_url": setup.get("github_repo_url"),
                "pages_url": setup.get("github_pages_url"),
            },
            "delivery": {
                "providers": ["Google Workspace", "Google Drive", "BBB", "Echo AI"],
                "status": "ready" if (
                    env_status["google_workspace_configured"] and env_status["google_drive_configured"]
                ) else "needs_google_workspace_or_drive",
                "delivery_path": "Email service/product deliverables with Google Drive links",
            },
        },
        "pipeline": [
            "Search and enrich prospects with Headhunter/Apollo",
            "Qualify leads and queue Bland cold-call outreach",
            "Send qualified prospects to BBB/Echo for proposal and product generation",
            "Deliver ordered products by email and Google Drive link",
            "Repeat this acquisition run for each newly selected business",
        ],
    }

# --- Routes ---

@app.get("/")
async def get_gui():
    """Serve the main HTML interface."""
    html_path = Path(__file__).parent / "business_builder_gui.html"
    if not html_path.exists():
        return JSONResponse({"error": "GUI file not found"}, status_code=404)
    return FileResponse(html_path)

@app.post("/api/v1/onboarding")
async def save_profile(profile: ProfileModel):
    """Save user profile from onboarding wizard."""
    update_app_state("profile", profile.model_dump())
    return {"status": "success", "message": "Profile saved"}

@app.get("/api/v1/research")
async def run_research():
    """Perform REAL analysis of business ideas against user profile."""
    state = get_app_state()
    profile = state.get("profile", {})
    if not profile:
        return {"logs": ["Error: Profile not found. Please complete step 1."], "recommendations": []}

    engine = RealAnalysisEngine(profile)
    result = await engine.evaluate_ideas()

    # Store the results for the next step
    update_app_state("analysis_results", result["recommendations"])
    update_app_state("research_logs", result["logs"])

    # Return both logs AND recommendations so the frontend can render immediately
    # without needing a second fetch (which caused a race condition / silent hang)
    return {"logs": result["logs"], "recommendations": result["recommendations"]}

@app.get("/api/v1/recommendations")
async def get_recommendations():
    """Return the results of the research phase."""
    state = get_app_state()
    # Return stored results from the research phase
    recs = state.get("analysis_results", [])

    if not recs:
        # Fallback if research wasn't run (shouldn't happen in flow)
        return []

    return recs

@app.post("/api/v1/select-business")
async def select_business(selection: BusinessSelection):
    """Save the selected business concept."""
    update_app_state("selected_business", selection.business_name)
    return {"status": "success", "selected": selection.business_name}

@app.get("/api/v1/license")
async def get_license_status():
    """Get current license info."""
    return fiduciary.get_license_info()

@app.post("/api/v1/license")
async def set_license(request: LicenseRequest):
    """Set the license tier (Partner vs Paid)."""
    try:
        if request.tier == "partner":
            info = fiduciary.activate_revenue_share()
        elif request.tier == "paid":
            info = fiduciary.purchase_paid_license()
        else:
            raise HTTPException(status_code=400, detail="Invalid tier")
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/admin-bypass")
async def admin_bypass(request: BypassRequest):
    """Apply admin code to unlock features."""
    success = fiduciary.apply_admin_bypass(request.code)
    if success:
        return {"status": "success", "message": "Admin bypass applied"}
    raise HTTPException(status_code=403, detail="Invalid admin code")

@app.post("/api/v1/acquisition/setup")
async def setup_acquisition(request: AcquisitionSetupRequest):
    """Configure the post-license acquisition toolchain for the selected business."""
    state = get_app_state()
    selected = state.get("selected_business")
    license_info = fiduciary.get_license_info()
    if not license_info.get("active"):
        raise HTTPException(status_code=400, detail="Activate Owner Tier before acquisition setup.")
    if not selected:
        raise HTTPException(status_code=400, detail="Select a business before acquisition setup.")

    env_status = _link_runtime_env(request)
    setup = {
        "business_name": selected,
        "target_customer": request.target_customer,
        "lead_keywords": request.lead_keywords,
        "service_offer": request.service_offer,
        "github_repo_url": request.github_repo_url,
        "github_pages_url": request.github_pages_url,
        "google_workspace_email": request.google_workspace_email,
        "google_drive_folder_url": request.google_drive_folder_url,
        "bland_webhook_url": request.bland_webhook_url,
        "env_status": env_status,
    }
    run = _build_acquisition_run(state, setup)
    update_app_state("acquisition_setup", setup)
    update_app_state("acquisition_run", run)
    return {"status": "started", "setup": setup, "run": run}

@app.get("/api/v1/dashboard")
async def get_dashboard():
    """Get simulated dashboard metrics."""
    state = get_app_state()
    selected = state.get("selected_business", "Unknown Business")
    license_info = fiduciary.get_license_info()

    # Mock data
    if not license_info.get("active"):
        return {
            "active": False,
            "business_name": selected,
            "status": "Pending License"
        }

    revenue_today = random.randint(100, 500)
    user_share_today = revenue_today * (1 - license_info.get("revenue_share_percentage", 0.0))

    # Simulate running agents
    return {
        "active": True,
        "business_name": selected,
        "status": "Running",
        "agents_active": 3,
        "revenue_today": revenue_today,
        "total_revenue": state.get("revenue_total", 0.0),
        "user_share": user_share_today,
        "license": license_info,
        "acquisition": state.get("acquisition_run")
    }

@app.post("/api/v1/chat")
async def chat_with_echo(request: ChatRequest):
    """Chat with Echo via Ollama."""
    try:
        response = await ech0.chat(request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "I'm having trouble connecting to my brain right now. Please check if Ollama is running."}

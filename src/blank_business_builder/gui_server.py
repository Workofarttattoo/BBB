"""
FastAPI Backend for the Blank Business Builder GUI.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import json
import logging
import random
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .business_data import BusinessIdea, default_ideas
from .fiduciary import FiduciaryManager
from .features.market_research import MarketResearch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Business Builder API")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# --- State Management (Simple In-Memory + JSON Sync) ---
STATE_FILE = "business_state.json"

def get_app_state():
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
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

# --- Routes ---

@app.get("/")
async def get_gui():
    """Serve the main HTML interface."""
    html_path = Path(__file__).parent / "business_builder_gui.html"
    if not html_path.exists():
        return JSONResponse({"error": "GUI file not found"}, status_code=404)
    return FileResponse(html_path)

@app.post("/api/onboarding")
async def save_profile(profile: ProfileModel):
    """Save user profile from onboarding wizard."""
    update_app_state("profile", profile.model_dump())
    return {"status": "success", "message": "Profile saved"}

@app.get("/api/research")
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

    return {"logs": result["logs"]}

@app.get("/api/recommendations")
async def get_recommendations():
    """Return the results of the research phase."""
    state = get_app_state()
    # Return stored results from the research phase
    recs = state.get("analysis_results", [])

    if not recs:
        # Fallback if research wasn't run (shouldn't happen in flow)
        return []

    return recs

@app.post("/api/select-business")
async def select_business(selection: BusinessSelection):
    """Save the selected business concept."""
    update_app_state("selected_business", selection.business_name)
    return {"status": "success", "selected": selection.business_name}

@app.get("/api/license")
async def get_license_status():
    """Get current license info."""
    return fiduciary.get_license_info()

@app.post("/api/license")
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

@app.post("/api/admin-bypass")
async def admin_bypass(request: BypassRequest):
    """Apply admin code to unlock features."""
    success = fiduciary.apply_admin_bypass(request.code)
    if success:
        return {"status": "success", "message": "Admin bypass applied"}
    raise HTTPException(status_code=403, detail="Invalid admin code")

@app.get("/api/dashboard")
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

    # Simulate running agents
    return {
        "active": True,
        "business_name": selected,
        "status": "Running",
        "agents_active": 3,
        "revenue_today": random.randint(100, 500),
        "total_revenue": state.get("revenue_total", 0.0),
        "user_share": state.get("wallet", 0.0),
        "license": license_info
    }

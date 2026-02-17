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
# In a real app, use a proper database. Here we piggyback on fiduciary state or a separate file.

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
    # Merge with fiduciary state if needed, but fiduciary manages its own file.
    # We'll just use the same file for simplicity since FiduciaryManager also reads/writes it.
    # Actually, let's keep them separate or merge carefully.
    # FiduciaryManager writes the whole file. Let's let FiduciaryManager handle "license" key,
    # and we handle "profile", "selected_business", "research_logs".

    # Reload to get latest license info
    current_state = fiduciary._load_state()
    current_state[key] = value

    with open(STATE_FILE, "w") as f:
        json.dump(current_state, f, indent=2)

    # Reload fiduciary so it sees the changes
    fiduciary.state = fiduciary._load_state()

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
    """Simulate OSINT research delay and return logs."""
    # Simulate time delay for "deep research"
    await asyncio.sleep(2.0)

    logs = [
        "Scanning county records for permit data...",
        "Analyzing local competitive density...",
        "Querying Google Trends for regional interest...",
        "Cross-referencing demographic income levels...",
        "Identifying underserved niches in chosen industry...",
        "Optimization complete."
    ]

    update_app_state("research_complete", True)
    return {"logs": logs}

@app.get("/api/recommendations")
async def get_recommendations():
    """Return filtered business ideas based on profile."""
    state = get_app_state()
    profile = state.get("profile", {})

    budget = profile.get("startup_budget", 10000)
    hours = profile.get("weekly_hours", 40)
    industry = profile.get("preferred_industry", "")

    all_ideas = default_ideas()
    filtered = []

    for idea in all_ideas:
        if idea.startup_cost <= budget * 1.2:
             if idea.time_commitment_hours_per_week <= hours * 1.2:
                 if not industry or industry == "Generalist" or industry in idea.industry:
                     filtered.append(asdict(idea))

    # Fallback if too strict
    if not filtered:
        filtered = [asdict(i) for i in all_ideas[:3]]

    # Return top 3 sorted by revenue/cost ratio (simple heuristic)
    filtered.sort(key=lambda x: x["expected_monthly_revenue"] / (x["startup_cost"] + 1), reverse=True)
    return filtered[:3]

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

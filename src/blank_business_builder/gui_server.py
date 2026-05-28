"""
FastAPI Backend for the Blank Business Builder GUI.
Viktor-Style Autonomous Business Operations Dashboard.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import json
import logging
import os
import random
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .business_data import BusinessIdea, default_ideas
from .fiduciary import FiduciaryManager
from .features.market_research import MarketResearch
from .ech0_service import ECH0Service
from .role_agent_runner import RoleAgentRunner
from .auto_judge_loop import AutoJudgeLoop
from .enterprise_agent_policy import EnterpriseAgentPolicy
from .paperclip_work_source import PaperclipWorkSourceSync
from .task_locks import TaskLockManager
from .knowledge_vault import get_vault
from .firebase_knowledge_sync import FirebaseKnowledgeSync, sync_to_firebase, sync_from_firebase
from .integrations.elevenlabs_voice import router as voice_router
from .tasks import app as celery_app  # Celery task queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BBB Autonomous Business Dashboard")

# Initialize Services
ech0 = ECH0Service()
role_runner = RoleAgentRunner()
judge_loop = AutoJudgeLoop()
policy_engine = EnterpriseAgentPolicy()
paperclip_sync = PaperclipWorkSourceSync()
lock_manager = TaskLockManager()
firebase_sync = FirebaseKnowledgeSync()

# Include ElevenLabs Voice Router
app.include_router(voice_router, prefix="/api/v1", tags=["voice"])

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

# Viktor-Style Autonomous Business Models

class PaperclipSyncRequest(BaseModel):
    issues_json: str
    business_id: str = "saas-micro-tools"

class TaskExecuteRequest(BaseModel):
    task_id: str
    role: str = "sales"
    instruction: str
    artifact_type: str = "lead_batch"

class ApprovalResolveRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None

class AgentOpsSettings(BaseModel):
    viktor_mode_enabled: bool = True
    assume_forward: bool = True
    max_revises: int = 3
    proactive_schedule: str = "07:00 UTC"

class HiveMindTask(BaseModel):
    task_id: str
    intent: str
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None

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

# --- Viktor-Style Autonomous Business API Endpoints ---

@app.get("/api/v1/agent-ops/settings")
async def get_agent_ops_settings():
    """Get Viktor mode and agent ops settings from business_state.json"""
    state = get_app_state()
    return state.get("agent_ops", {
        "viktor_mode_enabled": True,
        "assume_forward": True,
        "max_revises": 3,
        "proactive_schedule": "07:00 UTC"
    })

@app.post("/api/v1/agent-ops/settings")
async def update_agent_ops_settings(settings: AgentOpsSettings):
    """Update Viktor mode and agent ops settings"""
    update_app_state("agent_ops", settings.model_dump())
    logger.info(f"Updated agent_ops settings: viktor_mode={settings.viktor_mode_enabled}, assume_forward={settings.assume_forward}")
    return {"status": "success", "settings": settings.model_dump()}

@app.get("/api/v1/enterprise/policy/{business_id}")
async def get_enterprise_policy(business_id: str):
    """Get capability matrix and approval gates for a business"""
    policy = policy_engine.get_policy(business_id)
    return policy

@app.get("/api/v1/enterprise/approvals")
async def get_pending_approvals():
    """Get all pending approval gates"""
    state = get_app_state()
    return state.get("pending_approvals", [])

@app.post("/api/v1/enterprise/approvals/{approval_id}/resolve")
async def resolve_approval(approval_id: str, request: ApprovalResolveRequest):
    """Approve or reject a pending action"""
    state = get_app_state()
    approvals = state.get("pending_approvals", [])
    
    found = None
    for i, appr in enumerate(approvals):
        if appr.get("id") == approval_id:
            found = appr
            approvals.pop(i)
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Record resolution
    resolution = {
        "id": approval_id,
        "approved": request.approved,
        "notes": request.notes,
        "resolved_at": datetime.utcnow().isoformat(),
        "original_request": found
    }
    
    # Add to task history
    task_history = state.get("task_history", [])
    task_history.append(resolution)
    update_app_state("task_history", task_history)
    update_app_state("pending_approvals", approvals)
    
    logger.info(f"Resolved approval {approval_id}: approved={request.approved}")
    
    return {"status": "resolved", "resolution": resolution}

@app.post("/api/v1/enterprise/paperclip/sync-issues")
async def sync_paperclip_issues(request: PaperclipSyncRequest, background_tasks: BackgroundTasks):
    """Sync Paperclip issues to autonomous task queue"""
    try:
        issues = json.loads(request.issues_json)
        if not isinstance(issues, list):
            issues = [issues]
        
        synced_count = 0
        for issue in issues:
            # Check for planner-only labels (skip execution)
            labels = issue.get("labels", [])
            if any(lbl.startswith("plan:") for lbl in labels):
                logger.info(f"Skipping planner issue {issue.get('number')}: {labels}")
                continue
            
            # Only process bbb:execute or judge:* labels
            if "bbb:execute" in labels or any(lbl.startswith("judge:") for lbl in labels):
                task_id = f"paperclip-{issue.get('number', 'unknown')}"
                
                # Check task lock
                if lock_manager.is_locked(task_id):
                    logger.warning(f"Task {task_id} is locked, skipping")
                    continue
                
                # Acquire lock
                lock_manager.acquire(task_id, "gui_sync")
                
                # Create autonomous task
                task = {
                    "task_id": task_id,
                    "role": "sales" if "bbb:execute" in labels else "meta_manager",
                    "instruction": issue.get("body", ""),
                    "artifact_type": "lead_batch",
                    "source": "paperclip",
                    "issue_number": issue.get("number"),
                    "labels": labels,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "queued"
                }
                
                # Add to active tasks
                state = get_app_state()
                active_tasks = state.get("active_tasks", [])
                active_tasks.append(task)
                update_app_state("active_tasks", active_tasks)
                
                # Execute in background
                background_tasks.add_task(execute_autonomous_task, task)
                
                synced_count += 1
        
        return {"status": "success", "synced": synced_count, "message": f"Synced {synced_count} issues to task queue"}
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

async def execute_autonomous_task(task: Dict):
    """Execute an autonomous task with judge loop"""
    task_id = task["task_id"]
    logger.info(f"Executing task {task_id} with role={task['role']}")
    
    try:
        # Update status
        state = get_app_state()
        for t in state.get("active_tasks", []):
            if t["task_id"] == task_id:
                t["status"] = "running"
                break
        update_app_state("active_tasks", state.get("active_tasks", []))
        
        # Run through role agent
        result = await role_runner.execute_role_task(
            role=task["role"],
            instruction=task["instruction"],
            artifact_type=task["artifact_type"]
        )
        
        # Run through judge loop
        judge_result = await judge_loop.evaluate_with_retries(
            artifact=result,
            role=task["role"],
            instruction=task["instruction"],
            max_revises=state.get("agent_ops", {}).get("max_revises", 3)
        )
        
        # Check if approval needed
        if judge_result["verdict"] == "pass":
            # Check if this requires approval (outbound actions)
            requires_approval = policy_engine.requires_approval(task["role"], task["artifact_type"])
            
            if requires_approval:
                # Create pending approval
                approval = {
                    "id": f"approval-{task_id}-{datetime.utcnow().timestamp()}",
                    "task_id": task_id,
                    "action_type": task["artifact_type"],
                    "payload": result.get("content", {}),
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "pending"
                }
                state = get_app_state()
                approvals = state.get("pending_approvals", [])
                approvals.append(approval)
                update_app_state("pending_approvals", approvals)
                
                logger.info(f"Task {task_id} passed judge, awaiting approval")
            else:
                # Auto-complete
                logger.info(f"Task {task_id} completed successfully (no approval needed)")
            
            # Update task status
            for t in state.get("active_tasks", []):
                if t["task_id"] == task_id:
                    t["status"] = "completed"
                    t["judge_verdict"] = judge_result["verdict"]
                    t["revises"] = judge_result.get("revises", 0)
                    break
            update_app_state("active_tasks", state.get("active_tasks", []))
            
            # Update judge stats
            update_judge_stats("pass")
        
        elif judge_result["verdict"] == "revise":
            logger.info(f"Task {task_id} needs revision (attempt {judge_result.get('attempt', 1)})")
            # Could re-queue here for revision loop
        
        else:  # fail
            logger.warning(f"Task {task_id} failed judge: {judge_result.get('reason', 'unknown')}")
            for t in state.get("active_tasks", []):
                if t["task_id"] == task_id:
                    t["status"] = "failed"
                    t["judge_reason"] = judge_result.get("reason", "")
                    break
            update_app_state("active_tasks", state.get("active_tasks", []))
            update_judge_stats("fail")
        
        # Release lock
        lock_manager.release(task_id)
        
    except Exception as e:
        logger.error(f"Task {task_id} execution error: {e}")
        lock_manager.release(task_id)
        # Mark as failed
        state = get_app_state()
        for t in state.get("active_tasks", []):
            if t["task_id"] == task_id:
                t["status"] = "error"
                t["error"] = str(e)
                break
        update_app_state("active_tasks", state.get("active_tasks", []))

def update_judge_stats(verdict: str):
    """Update judge statistics"""
    state = get_app_state()
    stats = state.get("judge_stats", {
        "total_evaluations": 0,
        "pass_count": 0,
        "revise_count": 0,
        "fail_count": 0,
        "revise_rate": 0.0
    })
    
    stats["total_evaluations"] += 1
    if verdict == "pass":
        stats["pass_count"] += 1
    elif verdict == "revise":
        stats["revise_count"] += 1
    else:
        stats["fail_count"] += 1
    
    # Calculate revise rate
    if stats["total_evaluations"] > 0:
        stats["revise_rate"] = stats["revise_count"] / stats["total_evaluations"]
    
    update_app_state("judge_stats", stats)

@app.get("/api/v1/enterprise/tasks")
async def get_active_tasks():
    """Get all active and recent tasks"""
    state = get_app_state()
    return {
        "active": state.get("active_tasks", []),
        "history": state.get("task_history", [])[-20:]  # Last 20 tasks
    }

@app.post("/api/v1/hive-mind/tasks")
async def submit_hive_mind_task(request: HiveMindTask, background_tasks: BackgroundTasks):
    """Submit a task via Hive Mind Intel Mesh - bridges to orchestrator"""
    task_id = request.task_id
    
    # Check if already exists
    state = get_app_state()
    for t in state.get("active_tasks", []):
        if t["task_id"] == task_id:
            raise HTTPException(status_code=409, detail="Task already exists")
    
    # Create unified task (same structure as Paperclip-synced tasks)
    task = {
        "task_id": task_id,
        "role": "sales",  # Default, could be in metadata
        "instruction": request.intent,
        "artifact_type": "lead_batch",
        "source": "hive_mind",
        "priority": request.priority,
        "metadata": request.metadata,
        "created_at": datetime.utcnow().isoformat(),
        "status": "queued"
    }
    
    # Add to active tasks
    active_tasks = state.get("active_tasks", [])
    active_tasks.append(task)
    update_app_state("active_tasks", active_tasks)
    
    # Execute in background (same pipeline as Paperclip)
    background_tasks.add_task(execute_autonomous_task, task)
    
    logger.info(f"Hive Mind task {task_id} submitted and queued for execution")
    
    return {"status": "submitted", "task_id": task_id}

@app.get("/api/v1/hive-mind/status")
async def get_hive_mind_status():
    """Get Hive Mind Intel Mesh status"""
    state = get_app_state()
    active_tasks = state.get("active_tasks", [])
    
    return {
        "status": "operational",
        "active_tasks": len([t for t in active_tasks if t.get("status") in ["queued", "running"]]),
        "completed_today": len([t for t in active_tasks if t.get("status") == "completed"]),
        "viktor_mode": state.get("agent_ops", {}).get("viktor_mode_enabled", False)
    }

@app.post("/api/v1/enterprise/chat")
async def enterprise_chat(request: ChatRequest):
    """Chat with CEO/agents - supports natural language commands"""
    message = request.message.lower()
    
    # Detect commands
    if "approve" in message and ("latest" in message or "all" in message):
        # Auto-approve pending approvals
        state = get_app_state()
        approvals = state.get("pending_approvals", [])
        approved_count = 0
        for appr in approvals:
            appr["status"] = "approved"
            approved_count += 1
        update_app_state("pending_approvals", approvals)
        return {"response": f"Approved {approved_count} pending action(s)."}
    
    elif "task" in message and ("status" in message or "list" in message):
        state = get_app_state()
        active = state.get("active_tasks", [])
        return {"response": f"Active tasks: {len(active)}. " + ", ".join([f"{t['task_id']} ({t['status']})" for t in active[-5:]])}
    
    elif "viktor" in message and ("enable" in message or "on" in message):
        settings = AgentOpsSettings(viktor_mode_enabled=True)
        update_app_state("agent_ops", settings.model_dump())
        return {"response": "Viktor mode enabled. Agents will execute proactively."}
    
    elif "viktor" in message and ("disable" in message or "off" in message):
        settings = AgentOpsSettings(viktor_mode_enabled=False)
        update_app_state("agent_ops", settings.model_dump())
        return {"response": "Viktor mode disabled. Agents will wait for explicit commands."}
    
    elif "knowledge" in message and ("search" in message or "find" in message):
        # Extract search query (simple approach: everything after 'search' or 'find')
        query = request.message
        for keyword in ["knowledge search", "knowledge find", "search", "find"]:
            if keyword in query.lower():
                query = query[query.lower().find(keyword) + len(keyword):].strip()
                break
        
        vault = get_vault()
        results = vault.search(query)
        if results:
            response = f"Found {len(results)} result(s) in Knowledge Vault:\n"
            for i, r in enumerate(results, 1):
                response += f"\n{i}. [{r['source']}] {r['snippet']}"
            return {"response": response}
        else:
            return {"response": f"No results found for '{query}' in Knowledge Vault."}
    
    elif "who are we" in message or "what do we do" in message or "what do we sell" in message:
        # Return company identity from Knowledge Vault
        vault = get_vault()
        context = vault.get_system_prompt_context()
        return {"response": context[:2000]}  # Truncate for chat
    
    else:
        # Regular chat with Echo
        try:
            response = await ech0.chat(request.message)
            return {"response": response}
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {"response": "I'm having trouble connecting to my brain right now. Please check if Ollama is running."}


# --- Knowledge Vault API Endpoints ---

@app.get("/api/v1/knowledge-vault/context")
async def get_knowledge_context():
    """Get full company context for agents"""
    vault = get_vault()
    return {"context": vault.get_system_prompt_context()}

@app.get("/api/v1/knowledge-vault/get/{key}")
async def get_knowledge_item(key: str):
    """Get specific item from Knowledge Vault by key"""
    vault = get_vault()
    value = vault.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "value": value}

@app.post("/api/v1/knowledge-vault/search")
class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/api/v1/knowledge-vault/search")
async def search_knowledge(request: SearchRequest):
    """Search Knowledge Vault"""
    vault = get_vault()
    results = vault.search(request.query, limit=request.limit)
    return {"query": request.query, "results": results}

@app.post("/api/v1/knowledge-vault/reload")
async def reload_knowledge():
    """Force reload Knowledge Vault from disk"""
    vault = get_vault()
    result = vault.reload()
    return result

@app.post("/api/v1/knowledge-vault/sync/firebase/upload")
async def sync_to_firebase_endpoint():
    """Upload company pack to Firebase"""
    result = sync_to_firebase("companies/saas-micro-tools")
    if result["status"] == "success":
        return result
    raise HTTPException(status_code=500, detail=result.get("reason", "Unknown error"))

@app.post("/api/v1/knowledge-vault/sync/firebase/download")
async def sync_from_firebase_endpoint():
    """Download company pack from Firebase"""
    result = sync_from_firebase("companies/saas-micro-tools")
    if result["status"] == "success":
        return result
    raise HTTPException(status_code=500, detail=result.get("reason", "Unknown error"))

@app.get("/api/v1/knowledge-vault/firebase/status")
async def get_firebase_status():
    """Get Firebase sync status"""
    sync = FirebaseKnowledgeSync()
    return {
        "enabled": sync.enabled,
        "company_id": sync.company_id,
        "remote_version": sync.get_remote_version() if sync.enabled else None
    }

# --- Original Routes ---

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
    # Check for Viktor dashboard first (new autonomous UI)
    viktor_path = Path(__file__).parent / "viktor_dashboard.html"
    if viktor_path.exists():
        return FileResponse(viktor_path)
    
    # Fallback to legacy GUI
    html_path = Path(__file__).parent / "business_builder_gui.html"
    if not html_path.exists():
        return JSONResponse({"error": "GUI file not found"}, status_code=404)
    return FileResponse(html_path)

@app.get("/dashboard")
async def get_viktor_dashboard():
    """Serve the Viktor autonomous dashboard."""
    html_path = Path(__file__).parent / "viktor_dashboard.html"
    if not html_path.exists():
        return JSONResponse({"error": "Viktor dashboard not found"}, status_code=404)
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

@app.post("/api/v1/chat")
async def chat_with_echo(request: ChatRequest):
    """Chat with Echo via Ollama."""
    try:
        response = await ech0.chat(request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "I'm having trouble connecting to my brain right now. Please check if Ollama is running."}

"""Enterprise operations API: policy, approvals, Paperclip sync, lead routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..approval_gates import ApprovalGateError, ApprovalStatus, ApprovalStore, GateAction
from ..enterprise_agent_policy import resolve_business_policy
from ..enterprise_nl_router import execute_intent, parse_intent
from ..lead_huntress import LeadHuntress

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])

_orchestrators: Dict[str, Any] = {}


class ApprovalResolveRequest(BaseModel):
    status: str = Field(..., description="approved or rejected")


class LeadSearchRequest(BaseModel):
    criteria: str
    count: int = Field(5, ge=1, le=100)
    mode: str = Field("manual", description="manual or agent")
    business_name: str = "SaaS Micro-Tools Empire"
    approval_id: Optional[str] = None


class LeadIngestRequest(BaseModel):
    leads: List[Dict[str, Any]]
    business_name: str = "SaaS Micro-Tools Empire"
    role: str = "sales"
    approval_id: Optional[str] = None


class PaperclipSyncRequest(BaseModel):
    business_name: str
    issues: List[Dict[str, Any]]


class EnterpriseChatRequest(BaseModel):
    message: str
    business_name: str = "SaaS Micro-Tools Empire"
    context: Optional[Dict[str, Any]] = None


class EnterpriseChatResponse(BaseModel):
    reply: str
    intent: str
    actions: List[str] = Field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class MilestoneReviewRequest(BaseModel):
    business_name: str
    milestone_id: str
    title: str
    summary: str
    artifact_type: str = "milestone_pack"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class JudgeArtifactRequest(BaseModel):
    business_name: str
    artifact_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MiddleManagerHeartbeatRequest(BaseModel):
    business_name: str = "SaaS Micro-Tools Empire"
    mission: Optional[str] = None


def _get_orchestrator(business_name: str):
    from ..autonomous_business import AutonomousBusinessOrchestrator

    if business_name not in _orchestrators:
        _orchestrators[business_name] = AutonomousBusinessOrchestrator(
            business_concept=business_name,
            founder_name="enterprise-board",
        )
    return _orchestrators[business_name]


@router.post("/chat", response_model=EnterpriseChatResponse)
async def enterprise_chat(body: EnterpriseChatRequest) -> EnterpriseChatResponse:
    """
    Natural-language interface for CEO, agents, and enterprise ops.
    Examples: "what needs my approval?", "CEO: review pipeline", "find 5 SaaS leads".
    """
    orchestrator = _get_orchestrator(body.business_name)
    intent = parse_intent(body.message, body.business_name)
    reply, meta = await execute_intent(
        intent,
        orchestrator=orchestrator,
        business_name=body.business_name,
        context=body.context or {},
    )
    ctx = dict(body.context or {})
    ctx.update(meta.get("context_updates") or {})
    return EnterpriseChatResponse(
        reply=reply,
        intent=meta.get("intent", intent.name),
        actions=meta.get("actions", []),
        data=meta.get("data"),
        context=ctx or None,
    )


@router.get("/policy/{business_name}")
async def get_automation_policy(business_name: str) -> Dict[str, Any]:
    return resolve_business_policy(business_name).to_dict()


@router.get("/approvals")
async def list_pending_approvals(business_name: Optional[str] = None) -> Dict[str, Any]:
    pending = ApprovalStore.list_pending(business_name)
    return {"pending": [r.to_dict() for r in pending]}


@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval(
    approval_id: str, body: ApprovalResolveRequest
) -> Dict[str, Any]:
    status = body.status.lower()
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")
    record = ApprovalStore.resolve(
        approval_id,
        ApprovalStatus.APPROVED if status == "approved" else ApprovalStatus.REJECTED,
    )
    if not record:
        raise HTTPException(status_code=404, detail="approval not found")
    return record.to_dict()


@router.post("/leads/search")
async def search_leads(body: LeadSearchRequest) -> Dict[str, Any]:
    orchestrator = _get_orchestrator(body.business_name)
    huntress = LeadHuntress(orchestrator, business_name=body.business_name)
    try:
        leads = huntress.find_leads(
            body.criteria,
            body.count,
            mode=body.mode,
            approval_id=body.approval_id,
        )
    except ApprovalGateError as exc:
        raise HTTPException(
            status_code=403,
            detail={"message": str(exc), "approval_id": exc.approval_id},
        ) from exc
    return {"leads": leads, "count": len(leads), "mode": body.mode}


@router.post("/leads/ingest")
async def ingest_leads(body: LeadIngestRequest) -> Dict[str, Any]:
    orchestrator = _get_orchestrator(body.business_name)
    huntress = LeadHuntress(orchestrator, business_name=body.business_name)
    try:
        count = huntress.ingest_leads_to_crm(
            body.leads,
            role=body.role,
            approval_id=body.approval_id,
        )
    except ApprovalGateError as exc:
        raise HTTPException(
            status_code=403,
            detail={"message": str(exc), "approval_id": exc.approval_id},
        ) from exc
    return {"ingested": count}


@router.post("/paperclip/sync-issues")
async def sync_paperclip_issues(body: PaperclipSyncRequest) -> Dict[str, Any]:
    orchestrator = _get_orchestrator(body.business_name)
    return orchestrator.sync_paperclip_issues(body.issues)


@router.post("/middle-manager/heartbeat")
async def middle_manager_heartbeat(body: MiddleManagerHeartbeatRequest) -> Dict[str, Any]:
    from ..middle_manager_loop import MiddleManagerLoop

    orchestrator = _get_orchestrator(body.business_name)
    report = await MiddleManagerLoop(orchestrator).run_heartbeat(mission=body.mission)
    return report.to_dict()


@router.get("/middle-manager/last-report")
async def middle_manager_last_report(
    business_name: Optional[str] = None,
) -> Dict[str, Any]:
    from ..middle_manager_loop import load_last_report

    report = load_last_report(business_name)
    if not report:
        raise HTTPException(status_code=404, detail="no middle manager reports yet")
    return report


@router.post("/middle-manager/judge")
async def middle_manager_judge(body: JudgeArtifactRequest) -> Dict[str, Any]:
    from ..middle_manager_loop import MiddleManagerLoop

    orchestrator = _get_orchestrator(body.business_name)
    return await MiddleManagerLoop(orchestrator).judge_artifact(
        artifact_type=body.artifact_type,
        content=body.content,
        metadata=body.metadata,
    )


@router.post("/middle-manager/milestone-review")
async def middle_manager_milestone_review(body: MilestoneReviewRequest) -> Dict[str, Any]:
    from ..middle_manager_loop import MiddleManagerLoop
    from ..milestone_parliament import MilestonePack

    orchestrator = _get_orchestrator(body.business_name)
    pack = MilestonePack(
        milestone_id=body.milestone_id,
        business_name=body.business_name,
        title=body.title,
        summary=body.summary,
        artifact_type=body.artifact_type,
        content=body.content,
        metadata=body.metadata or {},
    )
    return await MiddleManagerLoop(orchestrator).review_milestone(pack)


@router.get("/mcp-bridge")
async def mcp_bridge_manifest() -> Dict[str, Any]:
    """
    Lightweight manifest for Hermes HTTP MCP — documents callable BBB surfaces.
    Point hermes mcp_servers.bbb_ops.url at this host path prefix.
    """
    return {
        "name": "bbb_ops",
        "endpoints": {
            "policy": "/api/v1/enterprise/policy/{business_name}",
            "approvals": "/api/v1/enterprise/approvals",
            "leads_search": "/api/v1/enterprise/leads/search",
            "leads_ingest": "/api/v1/enterprise/leads/ingest",
            "paperclip_sync": "/api/v1/enterprise/paperclip/sync-issues",
            "middle_manager_heartbeat": "/api/v1/enterprise/middle-manager/heartbeat",
            "middle_manager_judge": "/api/v1/enterprise/middle-manager/judge",
            "middle_manager_milestone": "/api/v1/enterprise/middle-manager/milestone-review",
            "enterprise_chat": "/api/v1/enterprise/chat",
            "echo_prime_health": "/api/v1/echo-prime/health",
            "echo_prime_chat": "/api/v1/echo-prime/chat",
        },
    }


@router.get("/routing/labels")
async def paperclip_routing_labels() -> Dict[str, Any]:
    """Issue label conventions for Paperclip + Hermes MCP routing."""
    return {
        "labels": {
            "echo:strategy": {
                "target": "echo_prime",
                "mcp_server": "echo_prime",
                "description": "Strategic reasoning via Echo Prime /api/v1/echo-prime",
            },
            "bbb:execute": {
                "target": "bbb",
                "mcp_server": "bbb_ops",
                "description": "Business execution via BBB enterprise API and Celery",
            },
            "human:apollo": {
                "target": "human",
                "description": "Founder runs Apollo in BBB GUI; no agent heartbeat",
            },
        },
        "role_prefix": "role:<agent_role>",
    }

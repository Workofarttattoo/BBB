"""
Bland webhook and voice tool endpoints.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..agents.voice_agent import VoiceAgent
from ..database import (
    CallSession,
    DepartmentRoute,
    LeadEnrichment,
    LeadRecord,
    OutreachAttempt,
    get_db,
)
from ..echo_master_brain import EchoMasterBrain
from ..integrations import IntegrationFactory
from ..task_queue import task_queue

router = APIRouter(prefix="/api", tags=["Webhooks"])


class LeadLookupRequest(BaseModel):
    lead_id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class AppointmentSlotsRequest(BaseModel):
    timezone: Optional[str] = "UTC"
    duration_minutes: Optional[int] = 30


class QuoteStatusRequest(BaseModel):
    quote_id: str


class VoiceOutreachRequest(BaseModel):
    lead_id: str
    webhook_url: str
    force_department: Optional[str] = None
    force_task: Optional[str] = None
    force_script: Optional[str] = None


class ElevenLabsOutreachRequest(BaseModel):
    lead_id: str
    consent_confirmed: bool = Field(
        False,
        description="Operator confirms a lawful basis/consent for B2B outreach to this lead.",
    )
    force_script: Optional[str] = None
    voice_id: Optional[str] = None
    model_id: Optional[str] = None


class ApolloDiscoverRequest(BaseModel):
    keywords: str = Field(..., description="Search terms for Apollo people search")
    organization_name: Optional[str] = None
    per_page: int = 10


class ApolloVoiceDraftRequest(ApolloDiscoverRequest):
    consent_confirmed: bool = Field(
        False,
        description="Operator confirms a lawful basis/consent before generating outreach audio.",
    )
    voice_id: Optional[str] = None
    model_id: Optional[str] = None
    b2b_site_queries: List[str] = Field(
        default_factory=list,
        description="Optional extra B2B directory/site keywords to append to the Apollo search.",
    )


def _get_route_channel(db: Session, department: str) -> Optional[str]:
    route = (
        db.query(DepartmentRoute)
        .filter(DepartmentRoute.department == department.lower(), DepartmentRoute.is_active.is_(True))
        .first()
    )
    if route:
        return route.slack_channel_id
    return IntegrationFactory.get_slack_service().resolve_channel(department)


@router.post("/webhooks/bland/post-call")
async def bland_post_call_webhook(request: Request, db: Session = Depends(get_db)):
    payload_bytes = await request.body()
    signature = request.headers.get("x-bland-signature")
    bland = IntegrationFactory.get_bland_service()
    if not bland.verify_webhook_signature(payload_bytes, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    try:
        payload = json.loads(payload_bytes.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {exc}") from exc

    voice = VoiceAgent()
    result = voice.handle_post_call_webhook(db, payload=payload)
    return {"ok": True, "result": result}


@router.post("/webhooks/bland/live-tool")
async def bland_live_tool_webhook(payload: Dict[str, Any]):
    tool_name = str(payload.get("tool") or payload.get("tool_name") or "")
    if not tool_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tool name")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return VoiceAgent.handle_live_tool(tool_name, data)


@router.post("/tools/lead-lookup")
async def lead_lookup_tool(request: LeadLookupRequest):
    return VoiceAgent.handle_live_tool(
        "lead-lookup",
        {
            "lead_id": request.lead_id,
            "name": request.name,
            "company": request.company,
            "notes": request.notes,
        },
    )


@router.post("/tools/appointment-slots")
async def appointment_slots_tool(request: AppointmentSlotsRequest):
    return VoiceAgent.handle_live_tool(
        "appointment-slots",
        {"timezone": request.timezone, "duration_minutes": request.duration_minutes},
    )


@router.post("/tools/quote-status")
async def quote_status_tool(request: QuoteStatusRequest):
    return VoiceAgent.handle_live_tool("quote-status", {"quote_id": request.quote_id})


@router.post("/v1/outreach/discover")
async def discover_and_store_leads(payload: ApolloDiscoverRequest, db: Session = Depends(get_db)):
    """
    Apollo first: search and then enrich each person before storing lead records.
    """
    apollo = IntegrationFactory.get_apollo_service()
    search = apollo.search_people(
        q_keywords=payload.keywords,
        q_organization_name=payload.organization_name,
        per_page=payload.per_page,
    )
    people = search.get("people") or search.get("contacts") or []

    stored = []
    for person in people:
        enrich = {}
        try:
            enrich = apollo.enrich_person(
                email=person.get("email"),
                linkedin_url=person.get("linkedin_url"),
                first_name=person.get("first_name"),
                last_name=person.get("last_name"),
                company_name=(person.get("organization") or {}).get("name")
                if isinstance(person.get("organization"), dict)
                else person.get("organization_name"),
            )
        except Exception:
            enrich = {}

        payload_person = (
            enrich.get("person")
            if isinstance(enrich, dict) and isinstance(enrich.get("person"), dict)
            else person
        )
        lead = LeadRecord(
            external_id=str(payload_person.get("id") or person.get("id") or ""),
            source="apollo",
            first_name=payload_person.get("first_name"),
            last_name=payload_person.get("last_name"),
            full_name=(
                payload_person.get("name")
                or f"{payload_person.get('first_name', '')} {payload_person.get('last_name', '')}".strip()
            ),
            company=payload_person.get("organization_name")
            or (payload_person.get("organization") or {}).get("name")
            if isinstance(payload_person.get("organization"), dict)
            else payload_person.get("company"),
            title=payload_person.get("title") or payload_person.get("headline"),
            email=payload_person.get("email"),
            phone=payload_person.get("phone") or payload_person.get("phone_number"),
            status="new",
        )
        db.add(lead)
        db.flush()
        db.add(
            LeadEnrichment(
                lead_id=lead.id,
                provider="apollo",
                payload=enrich if isinstance(enrich, dict) else {},
            )
        )
        stored.append({"lead_id": str(lead.id), "name": lead.full_name, "company": lead.company})

    db.commit()
    return {"stored": stored, "count": len(stored)}


@router.post("/v1/outreach/create-call")
async def create_outreach_call(request: VoiceOutreachRequest, db: Session = Depends(get_db)):
    lead = db.query(LeadRecord).filter(LeadRecord.id == request.lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not lead.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead does not have a phone number")

    brain = EchoMasterBrain()
    decision = brain.decide_outreach(
        {
            "lead_id": str(lead.id),
            "full_name": lead.full_name,
            "title": lead.title,
            "company": lead.company,
            "email": lead.email,
            "phone": lead.phone,
        }
    )
    department = (request.force_department or decision.get("department") or "sales").lower()
    lead.department = department
    lead.outreach_priority = int(decision.get("outreach_priority", 0))
    db.flush()

    # Opportunistically cache route config in DB to satisfy department_routes model.
    channel = _get_route_channel(db, department)
    if channel:
        route = db.query(DepartmentRoute).filter(DepartmentRoute.department == department).first()
        if not route:
            db.add(
                DepartmentRoute(
                    department=department,
                    slack_channel_id=channel,
                    owner=f"{department}-automation",
                    is_active=True,
                )
            )
            db.flush()

    voice = VoiceAgent()
    result = voice.create_outreach_call(
        db,
        lead=lead,
        webhook_url=request.webhook_url,
        department=department,
        script=request.force_script or str(decision.get("script") or ""),
        task=request.force_task or str(decision.get("task") or ""),
    )
    return {"ok": True, "decision": decision, "result": result}


@router.post("/v1/outreach/create-elevenlabs-audio")
async def create_elevenlabs_audio(request: ElevenLabsOutreachRequest, db: Session = Depends(get_db)):
    """
    Generate a personalized ElevenLabs voice asset for a lead.

    This endpoint creates an audio asset for lawful B2B outreach workflows; it does not
    place outbound calls. The caller must confirm consent/lawful basis before generation.
    """
    if not request.consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="consent_confirmed must be true before creating outreach audio",
        )

    lead = db.query(LeadRecord).filter(LeadRecord.id == request.lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not (lead.email or lead.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead must have an email or phone before outreach audio is generated",
        )

    brain = EchoMasterBrain()
    decision = brain.decide_outreach(
        {
            "lead_id": str(lead.id),
            "full_name": lead.full_name,
            "title": lead.title,
            "company": lead.company,
            "email": lead.email,
            "phone": lead.phone,
        }
    )
    script = request.force_script or str(decision.get("script") or decision.get("task") or "")
    if not script.strip():
        script = (
            f"Hi {lead.full_name or 'there'}, this is a quick note for "
            f"{lead.company or 'your team'} about improving B2B growth workflows. "
            "If this is relevant, please reply and we can schedule a short conversation."
        )

    voice = VoiceAgent()
    try:
        result = voice.create_elevenlabs_outreach_audio(
            db,
            lead=lead,
            script=script,
            voice_id=request.voice_id,
            model_id=request.model_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True, "decision": decision, "result": result}


@router.post("/v1/outreach/discover-and-create-elevenlabs-audio")
async def discover_and_create_elevenlabs_audio(
    payload: ApolloVoiceDraftRequest, db: Session = Depends(get_db)
):
    """
    Discover leads via Apollo search terms (optionally expanded with B2B site keywords)
    and generate ElevenLabs audio assets for stored leads with contact information.
    """
    if not payload.consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="consent_confirmed must be true before creating outreach audio",
        )

    expanded_keywords = " ".join(
        [payload.keywords] + [query.strip() for query in payload.b2b_site_queries if query.strip()]
    ).strip()
    discover_payload = ApolloDiscoverRequest(
        keywords=expanded_keywords or payload.keywords,
        organization_name=payload.organization_name,
        per_page=min(payload.per_page, 10),
    )
    discover_result = await discover_and_store_leads(discover_payload, db)

    generated = []
    for item in discover_result["stored"]:
        lead = db.query(LeadRecord).filter(LeadRecord.id == item["lead_id"]).first()
        if not lead or not (lead.email or lead.phone):
            continue
        audio_request = ElevenLabsOutreachRequest(
            lead_id=str(lead.id),
            consent_confirmed=True,
            voice_id=payload.voice_id,
            model_id=payload.model_id,
        )
        audio_result = await create_elevenlabs_audio(audio_request, db)
        generated.append(audio_result["result"])

    return {
        "ok": True,
        "discovered": discover_result,
        "generated": generated,
        "count": len(generated),
    }


@router.get("/v1/outreach/calls/{provider_call_id}")
async def get_call(provider_call_id: str, db: Session = Depends(get_db)):
    session = db.query(CallSession).filter(CallSession.provider_call_id == provider_call_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return {
        "id": str(session.id),
        "provider_call_id": session.provider_call_id,
        "status": session.status,
        "outcome": session.outcome,
        "summary": session.summary,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@router.get("/v1/outreach/calls")
async def list_calls(limit: int = 50, db: Session = Depends(get_db)):
    calls = (
        db.query(CallSession)
        .order_by(CallSession.created_at.desc())
        .limit(max(1, min(limit, 250)))
        .all()
    )
    return [
        {
            "id": str(call.id),
            "provider_call_id": call.provider_call_id,
            "status": call.status,
            "created_at": call.created_at.isoformat() if call.created_at else None,
        }
        for call in calls
    ]


@router.get("/v1/outreach/attempts")
async def list_attempts(limit: int = 50, db: Session = Depends(get_db)):
    attempts = (
        db.query(OutreachAttempt)
        .order_by(OutreachAttempt.created_at.desc())
        .limit(max(1, min(limit, 250)))
        .all()
    )
    return [
        {
            "id": str(attempt.id),
            "lead_id": str(attempt.lead_id),
            "status": attempt.status,
            "next_action": attempt.next_action,
            "scheduled_for": attempt.scheduled_for.isoformat() if attempt.scheduled_for else None,
        }
        for attempt in attempts
    ]


@router.post("/v1/outreach/queue-follow-up")
async def queue_follow_up(lead_id: str, next_action: str):
    task_queue.add_task(
        "voice_follow_up",
        {
            "lead_id": lead_id,
            "next_action": next_action,
            "queued_at": datetime.utcnow().isoformat(),
        },
    )
    return {"ok": True}

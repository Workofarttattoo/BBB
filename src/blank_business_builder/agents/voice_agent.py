"""
Webhook-driven voice outreach orchestration around Bland call lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urljoin
from sqlalchemy.orm import Session

from ..config import settings
from ..database import CallSession, LeadRecord, OutreachAttempt, ProviderEvent
from ..echo_master_brain import EchoMasterBrain
from ..integrations import IntegrationFactory
from ..task_queue import task_queue


class VoiceAgent:
    """Coordinates outbound attempts and post-call processing."""

    def __init__(self) -> None:
        self.bland = IntegrationFactory.get_bland_service()
        self.slack = IntegrationFactory.get_slack_service()
        self.brain = EchoMasterBrain()
        self.default_persona_id = settings.BBB_PERSONA_ID
        self.default_from_number = settings.BLAND_FROM_NUMBER
        self.default_language = settings.BLAND_DEFAULT_LANGUAGE
        self.default_max_duration = settings.BLAND_MAX_DURATION_MINUTES
        self.default_record_calls = settings.BLAND_RECORD_CALLS
        self.default_wait_for_greeting = settings.BLAND_WAIT_FOR_GREETING

    def _absolute_webhook(self, webhook_url: Optional[str]) -> str:
        """Resolve relative webhook paths against ECHO_BASE_URL when possible."""
        webhook = (webhook_url or "").strip()
        if not webhook:
            return ""
        if webhook.startswith("http://") or webhook.startswith("https://"):
            return webhook
        base = settings.ECHO_BASE_URL.strip()
        if not base:
            return webhook
        return urljoin(base.rstrip("/") + "/", webhook.lstrip("/"))

    @staticmethod
    def build_request_data_from_lead(lead: LeadRecord) -> Dict[str, Any]:
        """Map a lead record into Bland request_data fields used by BBB persona."""
        first_name = (lead.first_name or "").strip()
        last_name = (lead.last_name or "").strip()
        return {
            "first_name": first_name,
            "last_name": last_name,
            "homeowner_name": (lead.full_name or f"{first_name} {last_name}".strip()).strip(),
            "property_address": "",
            "business_name": lead.company or "",
            "company": lead.company or "",
            "city": "",
            "state": "",
            "zip_code": "",
            "storm_date": "",
            "hail_size": "",
            "storm_type": "",
            "damage_probability": "",
            "structures_hit": "",
            "image_findings": "",
            "lead_priority": str(lead.outreach_priority or ""),
            "callback_number": lead.phone or "",
        }

    def create_outreach_call(
        self,
        db: Session,
        *,
        lead: LeadRecord,
        webhook_url: str,
        department: str,
        script: str,
        task: str,
        persona_id: Optional[str] = None,
        from_number: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        max_duration: Optional[int] = None,
        record: Optional[bool] = None,
        wait_for_greeting: Optional[bool] = None,
        language: Optional[str] = None,
        analysis_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create Bland call + persist outreach/call session records."""
        outreach = OutreachAttempt(
            lead_id=lead.id,
            channel="voice",
            provider="bland",
            status="queued",
            task=task,
            script=script,
        )
        db.add(outreach)
        db.flush()

        resolved_webhook = self._absolute_webhook(webhook_url)
        call_response = self.bland.create_call(
            phone_number=lead.phone or "",
            task=task,
            webhook=resolved_webhook,
            metadata={
                "lead_id": str(lead.id),
                "outreach_attempt_id": str(outreach.id),
                "department": department,
            },
            persona_id=persona_id or self.default_persona_id or None,
            from_number=from_number or self.default_from_number or None,
            request_data=request_data or self.build_request_data_from_lead(lead),
            max_duration=max_duration if max_duration is not None else self.default_max_duration,
            record=self.default_record_calls if record is None else record,
            wait_for_greeting=self.default_wait_for_greeting
            if wait_for_greeting is None
            else wait_for_greeting,
            language=language or self.default_language,
            analysis_schema=analysis_schema,
        )
        provider_call_id = str(call_response.get("call_id") or call_response.get("id") or outreach.id)
        call = CallSession(
            outreach_attempt_id=outreach.id,
            provider="bland",
            provider_call_id=provider_call_id,
            status=str(call_response.get("status", "initiated")),
            raw_payload=call_response,
        )
        db.add(call)
        outreach.status = "in_progress"
        lead.status = "outreach_started"
        db.commit()
        return {
            "outreach_attempt_id": str(outreach.id),
            "provider_call_id": provider_call_id,
            "call_response": call_response,
        }

    def handle_post_call_webhook(
        self,
        db: Session,
        *,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist Bland webhook event, update state, route to Slack, queue follow-up."""
        call_id = str(payload.get("call_id") or payload.get("id") or "")
        metadata = payload.get("metadata") or {}
        event = ProviderEvent(
            provider="bland",
            event_type=str(payload.get("event") or "post_call"),
            external_id=call_id or None,
            payload=payload,
            processed=False,
        )
        db.add(event)

        call = None
        if call_id:
            call = db.query(CallSession).filter(CallSession.provider_call_id == call_id).first()

        if not call and metadata.get("outreach_attempt_id"):
            call = (
                db.query(CallSession)
                .filter(CallSession.outreach_attempt_id == metadata["outreach_attempt_id"])
                .first()
            )

        if not call:
            call = CallSession(
                provider="bland",
                provider_call_id=call_id or f"unknown-{int(datetime.utcnow().timestamp())}",
                status=str(payload.get("status", "completed")),
                raw_payload=payload,
            )
            db.add(call)
            db.flush()

        call.status = str(payload.get("status", call.status))
        call.transcript = payload.get("transcript") or call.transcript
        call.summary = payload.get("summary") or call.summary
        call.outcome = payload.get("outcome") or call.outcome
        call.duration_seconds = payload.get("duration") or call.duration_seconds
        call.raw_payload = payload

        outreach = None
        lead = None
        if call.outreach_attempt_id:
            outreach = db.query(OutreachAttempt).filter(OutreachAttempt.id == call.outreach_attempt_id).first()
        if outreach:
            outreach.status = "completed"
            outreach.completed_at = datetime.utcnow()
            lead = db.query(LeadRecord).filter(LeadRecord.id == outreach.lead_id).first()
        elif metadata.get("lead_id"):
            lead = db.query(LeadRecord).filter(LeadRecord.id == metadata["lead_id"]).first()

        decision_payload = {
            "call_id": call.provider_call_id,
            "status": call.status,
            "transcript": call.transcript,
            "summary": call.summary,
            "outcome": call.outcome,
            "department": metadata.get("department"),
        }
        decision = self.brain.decide_post_call_action(decision_payload)

        department = str(decision.get("department") or metadata.get("department") or "sales").lower()
        next_action = str(decision.get("next_action", "nurture"))
        follow_up_minutes = int(decision.get("follow_up_in_minutes", 60))
        if outreach:
            outreach.next_action = next_action
            outreach.scheduled_for = datetime.utcnow() + timedelta(minutes=follow_up_minutes)

        if lead:
            lead.status = "called"
            lead.department = department

        slack_channel = self.slack.resolve_channel(department)
        if slack_channel:
            summary = str(decision.get("slack_summary") or f"Call completed for lead {lead.id if lead else 'unknown'}")
            self.slack.post_message(slack_channel, summary)

        # Queue next step in Redis-backed local queue.
        if lead:
            task_queue.add_task(
                "voice_follow_up",
                {
                    "lead_id": str(lead.id),
                    "call_session_id": str(call.id),
                    "next_action": next_action,
                    "scheduled_for": (
                        datetime.utcnow() + timedelta(minutes=follow_up_minutes)
                    ).isoformat(),
                },
            )

        event.processed = True
        event.processed_at = datetime.utcnow()
        db.commit()
        return {
            "status": "processed",
            "call_session_id": str(call.id),
            "next_action": next_action,
            "department": department,
        }

    @staticmethod
    def handle_live_tool(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler used by Bland pathway webhook node for mid-call tool lookups.
        v1 returns deterministic placeholder data for tool contracts.
        """
        if tool_name == "lead-lookup":
            return {
                "lead": {
                    "id": payload.get("lead_id"),
                    "name": payload.get("name"),
                    "company": payload.get("company"),
                    "notes": payload.get("notes", ""),
                }
            }
        if tool_name == "appointment-slots":
            return {
                "slots": [
                    {"start": "2026-04-29T15:00:00Z", "end": "2026-04-29T15:30:00Z"},
                    {"start": "2026-04-29T16:00:00Z", "end": "2026-04-29T16:30:00Z"},
                ]
            }
        if tool_name == "quote-status":
            return {"quote_id": payload.get("quote_id"), "status": "pending_review"}
        return {"error": f"unknown_tool:{tool_name}"}

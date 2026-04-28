"""
Echo master brain orchestration client.

BBB remains the public control plane, while echo_prime is used as a private
reasoning service. This module encapsulates that boundary and provides safe
fallback heuristics when echo_prime is unavailable.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class EchoMasterBrain:
    """Decisioning client for outreach and follow-up actions."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout_seconds: int = 15,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("ECHO_BASE_URL", "")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.base_url:
            return None
        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json=payload,
                timeout=self.timeout_seconds,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception:
            return None

    def health(self) -> Dict[str, Any]:
        """Return steering service health without raising on network failures."""
        if not self.base_url:
            return {
                "configured": False,
                "connected": False,
                "base_url": "",
                "status": "fallback",
            }
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout_seconds,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            return {
                "configured": True,
                "connected": True,
                "base_url": self.base_url,
                "status": payload.get("status", "healthy"),
            }
        except Exception as exc:
            return {
                "configured": True,
                "connected": False,
                "base_url": self.base_url,
                "status": "unreachable",
                "error": str(exc),
            }

    @staticmethod
    def _default_department(lead_event: Dict[str, Any]) -> str:
        text = " ".join(
            [
                str(lead_event.get("title", "")),
                str(lead_event.get("company", "")),
                str(lead_event.get("notes", "")),
            ]
        ).lower()
        if any(token in text for token in ("finance", "cfo", "board", "vp", "ceo")):
            return "exec"
        if any(token in text for token in ("marketing", "growth", "brand")):
            return "marketing"
        if any(token in text for token in ("support", "helpdesk", "success")):
            return "support"
        if any(token in text for token in ("ops", "operations", "supply")):
            return "ops"
        return "sales"

    def decide_outreach(self, lead_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide who to call and what Bland task/script to run.
        """
        payload = {"lead_event": lead_event}
        # Try common internal routes, then fallback heuristics.
        for route in ("/internal/echo/outreach-decision", "/v1/outreach/decision", "/outreach/decision"):
            result = self._post(route, payload)
            if result:
                return result

        department = self._default_department(lead_event)
        full_name = lead_event.get("full_name") or "there"
        company = lead_event.get("company") or "your team"
        return {
            "department": department,
            "outreach_priority": 70,
            "should_call": bool(lead_event.get("phone")),
            "task": (
                f"Call {full_name} at {company}, qualify needs, confirm urgency, "
                "and ask for a next-step meeting."
            ),
            "script": (
                "Open with context, ask two qualifying questions, summarize pain points, "
                "and offer a clear next step."
            ),
            "slack_summary": f"Outbound call completed for {full_name} ({company}).",
            "next_action": "queue_follow_up",
        }

    def decide_post_call_action(self, call_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide what to do after Bland posts final call results.
        """
        payload = {"call_event": call_event}
        for route in ("/internal/echo/post-call-decision", "/v1/outreach/post-call", "/outreach/post-call"):
            result = self._post(route, payload)
            if result:
                return result

        status = str(call_event.get("status", "")).lower()
        transcript = str(call_event.get("transcript", "")).lower()
        if status in {"completed", "success"} and any(
            token in transcript for token in ("interested", "book", "meeting", "demo")
        ):
            return {
                "next_action": "schedule_meeting",
                "follow_up_in_minutes": 30,
                "department": call_event.get("department", "sales"),
                "slack_summary": "Lead is interested. Meeting follow-up queued.",
            }
        return {
            "next_action": "nurture",
            "follow_up_in_minutes": 24 * 60,
            "department": call_event.get("department", "sales"),
            "slack_summary": "Call complete. Added to nurture cadence.",
        }

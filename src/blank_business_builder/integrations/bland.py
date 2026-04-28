"""
Bland telephony integration.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Dict, Optional

import requests


class BlandService:
    """Thin API client for Bland call operations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        timeout_seconds: int = 20,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("BLAND_API_KEY", "")
        self.base_url = (base_url or os.getenv("BLAND_BASE_URL", "https://api.bland.ai")).rstrip("/")
        self.webhook_secret = webhook_secret or os.getenv("BLAND_WEBHOOK_SECRET", "")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("BLAND_API_KEY is required")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def create_call(
        self,
        phone_number: str,
        task: str,
        webhook: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        pathway_id: Optional[str] = None,
        from_number: Optional[str] = None,
        persona_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        max_duration: Optional[int] = None,
        record: Optional[bool] = None,
        wait_for_greeting: Optional[bool] = None,
        language: Optional[str] = None,
        analysis_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create an outbound Bland call with per-call webhook callback."""
        body: Dict[str, Any] = {
            "phone_number": phone_number,
            "task": task,
            "webhook": webhook,
        }
        if metadata:
            body["metadata"] = metadata
        if pathway_id:
            body["pathway_id"] = pathway_id
        if from_number:
            body["from"] = from_number
        if persona_id:
            body["persona_id"] = persona_id
        if request_data:
            body["request_data"] = request_data
        if max_duration is not None:
            body["max_duration"] = max_duration
        if record is not None:
            body["record"] = record
        if wait_for_greeting is not None:
            body["wait_for_greeting"] = wait_for_greeting
        if language:
            body["language"] = language
        if analysis_schema:
            body["analysis_schema"] = analysis_schema
        return self._request("POST", "/v1/calls", body)

    def get_call(self, call_id: str) -> Dict[str, Any]:
        """Fetch call details by provider call id."""
        return self._request("GET", f"/v1/calls/{call_id}")

    def list_calls(self, *, limit: int = 25, status: Optional[str] = None) -> Dict[str, Any]:
        """List recent calls."""
        body: Dict[str, Any] = {"limit": max(1, min(limit, 100))}
        if status:
            body["status"] = status
        return self._request("POST", "/v1/calls/list", body)

    def verify_webhook_signature(self, payload: bytes, signature: Optional[str]) -> bool:
        """
        Verify webhook signature when BLAND_WEBHOOK_SECRET is configured.
        Returns True when verification succeeds or no secret is set.
        """
        if not self.webhook_secret:
            return True
        if not signature:
            return False
        digest = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(digest, signature.strip())

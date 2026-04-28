"""
Slack messaging/routing integration.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import requests


class SlackService:
    """Minimal Slack client for posting messages and route resolution."""

    ROUTE_ENV_MAP = {
        "sales": "SLACK_CHANNEL_SALES",
        "marketing": "SLACK_CHANNEL_MARKETING",
        "ops": "SLACK_CHANNEL_OPS",
        "exec": "SLACK_CHANNEL_EXEC",
        "support": "SLACK_CHANNEL_SUPPORT",
    }

    def __init__(
        self,
        bot_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 20,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN", "")
        self.base_url = (base_url or os.getenv("SLACK_BASE_URL", "https://slack.com/api")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def resolve_channel(self, department: str) -> Optional[str]:
        env_key = self.ROUTE_ENV_MAP.get(department.lower())
        if not env_key:
            return None
        return os.getenv(env_key)

    def post_message(self, channel_id: str, text: str) -> Dict:
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN is required")

        response = self.session.post(
            f"{self.base_url}/chat.postMessage",
            json={"channel": channel_id, "text": text},
            headers={"Authorization": f"Bearer {self.bot_token}"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise ValueError(f"Slack API error: {payload.get('error', 'unknown_error')}")
        return payload

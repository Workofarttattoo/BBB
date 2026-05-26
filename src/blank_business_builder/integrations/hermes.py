"""
Hermes VPS Adapter
==================
Connects BBB to a NousResearch Hermes model running on a VPS via the
OpenAI-compatible API (works with Ollama, vLLM, llama.cpp server, LM Studio).

The VPS is always-on — one persistent session, heartbeat keeps it warm.

Setup on VPS:
    # Option A — Ollama (recommended, easiest)
    ollama pull hf.co/NousResearch/Hermes-3-Llama-3.1-8B-GGUF
    OLLAMA_HOST=0.0.0.0 ollama serve

    # Option B — vLLM (full precision, GPU required)
    vllm serve NousResearch/Hermes-3-Llama-3.1-8B --host 0.0.0.0 --port 8000

Then set in .env:
    HERMES_VPS_URL=http://YOUR_VPS_IP:11434   # Ollama
    HERMES_VPS_URL=http://YOUR_VPS_IP:8000    # vLLM
    HERMES_MODEL=hermes3                       # Ollama model tag
    HERMES_API_KEY=                            # optional, leave blank for Ollama
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are Hermes, the always-on autonomous intelligence core of the Better Business Builder "
    "platform. You orchestrate Level 6 AI agents that run real businesses hands-off. "
    "Be precise, decisive, and operationally focused. When given a task, produce actionable "
    "output immediately. You have full awareness of all business operations and agent states."
)


class HermesVPSAdapter:
    """
    OpenAI-compatible client for a Hermes model running on a VPS.
    Maintains a persistent keep-alive session and exposes a simple
    chat() interface that all BBB agents can call.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or os.getenv("HERMES_VPS_URL", "")).rstrip("/")
        self.model = model or os.getenv("HERMES_MODEL", "hermes3")
        self.api_key = api_key or os.getenv("HERMES_API_KEY", "")
        self.timeout = timeout
        self._last_ping: float = 0.0
        self._healthy: Optional[bool] = None

    # ── connectivity ────────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def health_check(self, force: bool = False) -> bool:
        """Ping the VPS. Caches result for 30 s to avoid hammering."""
        if not self.is_configured():
            return False
        now = time.time()
        if not force and self._healthy is not None and now - self._last_ping < 30:
            return self._healthy
        try:
            # Ollama exposes GET /api/tags; vLLM exposes GET /v1/models
            for probe in ["/api/tags", "/v1/models"]:
                req = urllib.request.Request(
                    f"{self.base_url}{probe}",
                    headers=self._headers(),
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        self._healthy = True
                        self._last_ping = now
                        logger.info("Hermes VPS healthy at %s", self.base_url)
                        return True
        except Exception as exc:
            logger.warning("Hermes VPS unreachable: %s", exc)
        self._healthy = False
        self._last_ping = now
        return False

    # ── inference ────────────────────────────────────────────────────────────

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        """
        Send a chat completion request to the Hermes VPS.
        Returns the assistant text content.
        Raises RuntimeError if the VPS is not reachable.
        """
        if not self.is_configured():
            raise RuntimeError("HERMES_VPS_URL is not set")

        messages = [
            {"role": "system", "content": system or _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # Try OpenAI-compatible endpoint (vLLM + Ollama /v1/chat/completions)
        endpoint = f"{self.base_url}/v1/chat/completions"
        try:
            data = self._post(endpoint, payload)
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message", {})
                # Handle tool calls
                if msg.get("tool_calls"):
                    tc = msg["tool_calls"][0]
                    return json.dumps({
                        "tool_call": tc.get("function", {}).get("name"),
                        "arguments": tc.get("function", {}).get("arguments", "{}"),
                    })
                return msg.get("content", "").strip()
        except urllib.error.HTTPError:
            pass  # fall through to Ollama native

        # Fall back to Ollama native /api/chat
        ollama_payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = self._post(f"{self.base_url}/api/chat", ollama_payload)
        return (data.get("message") or {}).get("content", "").strip()

    def chat_safe(
        self,
        prompt: str,
        system: Optional[str] = None,
        fallback: str = "",
        **kwargs: Any,
    ) -> str:
        """Like chat() but returns fallback string instead of raising."""
        try:
            return self.chat(prompt, system=system, **kwargs)
        except Exception as exc:
            logger.warning("Hermes chat_safe fallback: %s", exc)
            return fallback

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Single-string prompt convenience wrapper."""
        return self.chat(prompt, **kwargs)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


# Module-level singleton — shared across all agents
_hermes: Optional[HermesVPSAdapter] = None


def get_hermes() -> HermesVPSAdapter:
    global _hermes
    if _hermes is None:
        _hermes = HermesVPSAdapter()
    return _hermes

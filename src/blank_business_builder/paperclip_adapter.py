"""
Paperclip Adapter
=================
The single intelligence interface for all BBB agents and services.

Priority chain (falls through on failure):
  1. Hermes VPS   — always-on private model on your VPS (no API cost)
  2. Claude        — Anthropic API (paperclip / high quality reasoning)
  3. Ollama local  — local ECH0 model (no internet required)
  4. Deterministic — keyword-based fallback (never crashes)

All agents, planners, and services call paperclip.think() instead of
talking to providers directly. This lets you swap the brain without
touching agent code.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Provider availability flags ─────────────────────────────────────────────

def _hermes_available() -> bool:
    return bool(os.getenv("HERMES_VPS_URL", ""))

def _claude_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", ""))

def _ollama_available() -> bool:
    return bool(os.getenv("OLLAMA_BASE_URL", ""))


# ── Deterministic fallback ──────────────────────────────────────────────────

_FALLBACK_RESPONSES = {
    "research":    "Conduct market analysis: identify top 3 competitors, pricing gaps, and underserved niches.",
    "marketing":   "Launch email drip (5 emails, 3-day cadence) + post 3x/week on LinkedIn and Twitter.",
    "sales":       "Send 50 cold emails today. Follow up with phone calls on day 3. Close on day 7.",
    "fulfillment": "Process pending orders. Confirm delivery windows. Send tracking to customers.",
    "support":     "Respond to all open tickets within 2 hours. Escalate unresolved issues to manager.",
    "finance":     "Reconcile daily revenue. Invoice unpaid accounts. Review burn rate vs. MRR.",
    "hr":          "Allocate agent capacity: 40% sales, 30% delivery, 20% support, 10% research.",
    "executive":   "Review weekly KPIs. Adjust top priority to highest-ROI activity. Approve budgets.",
}

def _deterministic(prompt: str) -> str:
    p = prompt.lower()
    for key, response in _FALLBACK_RESPONSES.items():
        if key in p:
            return response
    return (
        "Action required: analyse current business metrics, identify the single highest-leverage "
        "task, and execute it immediately. Report outcome within 1 hour."
    )


# ── Provider calls ───────────────────────────────────────────────────────────

def _call_hermes(prompt: str, system: Optional[str], **kwargs: Any) -> str:
    from .integrations.hermes import get_hermes
    hermes = get_hermes()
    if not hermes.is_configured():
        raise RuntimeError("Hermes not configured")
    return hermes.chat(prompt, system=system, **kwargs)


def _call_claude(prompt: str, system: Optional[str], max_tokens: int = 1024) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msgs = [{"role": "user", "content": prompt}]
    kwargs: Dict[str, Any] = {"model": "claude-opus-4-7", "max_tokens": max_tokens, "messages": msgs}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def _call_ollama(prompt: str, system: Optional[str]) -> str:
    import json, urllib.request
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "hermes3")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(
        f"{base}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return (data.get("message") or {}).get("content", "").strip()


# ── Public API ───────────────────────────────────────────────────────────────

class PaperclipAdapter:
    """
    Single entry point for all intelligence requests inside BBB.

    Usage:
        from .paperclip_adapter import paperclip
        result = paperclip.think("Generate a cold email for a SaaS product")
        result = paperclip.think(prompt, system="You are a sales expert")
    """

    def think(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.4,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        """
        Route the prompt through the provider chain and return a string response.
        Never raises — falls back to deterministic if all providers fail.
        """
        kwargs: Dict[str, Any] = {
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        # 1. Hermes VPS
        if _hermes_available():
            try:
                result = _call_hermes(prompt, system, **kwargs)
                logger.debug("paperclip → hermes")
                return result
            except Exception as exc:
                logger.warning("Hermes unavailable: %s — trying Claude", exc)

        # 2. Claude (Anthropic / paperclip)
        if _claude_available():
            try:
                result = _call_claude(prompt, system, max_tokens=max_tokens)
                logger.debug("paperclip → claude")
                return result
            except Exception as exc:
                logger.warning("Claude unavailable: %s — trying Ollama", exc)

        # 3. Ollama local
        if _ollama_available():
            try:
                result = _call_ollama(prompt, system)
                logger.debug("paperclip → ollama")
                return result
            except Exception as exc:
                logger.warning("Ollama unavailable: %s — using deterministic fallback", exc)

        # 4. Deterministic (always works)
        logger.info("paperclip → deterministic fallback")
        return _deterministic(prompt)

    def active_provider(self) -> str:
        """Return name of the currently active provider (for status displays)."""
        if _hermes_available():
            try:
                from .integrations.hermes import get_hermes
                if get_hermes().health_check():
                    return "hermes-vps"
            except Exception:
                pass
        if _claude_available():
            return "claude"
        if _ollama_available():
            return "ollama-local"
        return "deterministic"

    def status(self) -> Dict[str, Any]:
        """Return health status of all configured providers."""
        hermes_ok = False
        if _hermes_available():
            try:
                from .integrations.hermes import get_hermes
                hermes_ok = get_hermes().health_check()
            except Exception:
                pass
        return {
            "active": self.active_provider(),
            "providers": {
                "hermes_vps":  {"configured": _hermes_available(), "healthy": hermes_ok,
                                "url": os.getenv("HERMES_VPS_URL", "not set")},
                "claude":      {"configured": _claude_available(), "healthy": _claude_available()},
                "ollama_local":{"configured": _ollama_available(), "healthy": _ollama_available()},
                "deterministic":{"configured": True, "healthy": True},
            },
        }


# Module-level singleton
paperclip = PaperclipAdapter()

"""
Board of Directors — Base Member
=================================
Abstract class all C-suite AI members inherit from.
Each member is a local Ollama model with a specific role, personality,
domain expertise, and decision-making style.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BoardDecision:
    member: str
    role: str
    model: str
    opinion: str
    recommendation: str          # "approve" | "reject" | "modify" | "abstain"
    confidence: float            # 0.0 – 1.0
    reasoning: str
    conditions: List[str] = field(default_factory=list)   # if "modify"


class BoardMember:
    """
    A single AI C-suite member running locally on Ollama (or compatible server).
    All members share the same OpenAI-compatible chat API — only the model,
    system prompt, and temperature differ.
    """

    role: str = "Board Member"
    title: str = "Board Member"
    model: str = "hermes3"
    temperature: float = 0.4
    max_tokens: int = 1024
    expertise: List[str] = []

    # Personality injected into every system prompt
    personality: str = "You are a decisive, experienced executive."

    def __init__(
        self,
        vps_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 90,
    ) -> None:
        self.vps_url = (vps_url or os.getenv("HERMES_VPS_URL", "http://localhost:11434")).rstrip("/")
        self.api_key = api_key or os.getenv("HERMES_API_KEY", "")
        self.timeout = timeout
        self._healthy: Optional[bool] = None

    # ── connectivity ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        if self._healthy is not None:
            return self._healthy
        try:
            for probe in ["/api/tags", "/v1/models"]:
                req = urllib.request.Request(
                    f"{self.vps_url}{probe}",
                    headers=self._headers(),
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        self._healthy = True
                        return True
        except Exception:
            pass
        self._healthy = False
        return False

    # ── core inference ───────────────────────────────────────────────────────

    def think(self, prompt: str, system_override: Optional[str] = None) -> str:
        """Raw chat completion — returns text string."""
        system = system_override or self._build_system()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        # Try OpenAI-compat endpoint first (vLLM + Ollama both support it)
        for endpoint in ["/v1/chat/completions", "/api/chat"]:
            try:
                data = self._post(f"{self.vps_url}{endpoint}", payload)
                # OpenAI-compat response
                choices = data.get("choices") or []
                if choices:
                    return (choices[0].get("message") or {}).get("content", "").strip()
                # Ollama native response
                msg = data.get("message") or {}
                if msg.get("content"):
                    return msg["content"].strip()
            except urllib.error.HTTPError:
                continue
            except Exception as exc:
                logger.warning("%s (%s) inference error on %s: %s", self.title, self.model, endpoint, exc)
                break
        return f"[{self.title} unavailable — model {self.model} not responding]"

    def deliberate(self, topic: str, context: Optional[str] = None) -> BoardDecision:
        """
        Structured deliberation on a business decision.
        Returns a BoardDecision with opinion, recommendation, and reasoning.
        """
        ctx_block = f"\nContext:\n{context}" if context else ""
        prompt = f"""You are the {self.title} of a BBB autonomous AI business empire.

Topic for deliberation:{ctx_block}

{topic}

Respond in this EXACT JSON format (no markdown, just JSON):
{{
  "opinion": "your 2-3 sentence view on this topic",
  "recommendation": "approve|reject|modify|abstain",
  "confidence": 0.0-1.0,
  "reasoning": "detailed reasoning from your {self.role} perspective",
  "conditions": ["condition if modifying", "..."]
}}"""

        raw = self.think(prompt)
        try:
            # Strip any markdown code fences if model adds them
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(clean)
            return BoardDecision(
                member=self.title,
                role=self.role,
                model=self.model,
                opinion=data.get("opinion", raw[:200]),
                recommendation=data.get("recommendation", "abstain"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                conditions=data.get("conditions", []),
            )
        except Exception:
            # Fallback: treat raw text as opinion
            return BoardDecision(
                member=self.title,
                role=self.role,
                model=self.model,
                opinion=raw[:300],
                recommendation="abstain",
                confidence=0.3,
                reasoning="(Could not parse structured response)",
            )

    def advise(self, question: str) -> str:
        """Quick domain-specific advice — no structured output required."""
        return self.think(
            f"As {self.title}, give concise expert advice on: {question}",
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_system(self) -> str:
        expertise_str = ", ".join(self.expertise) if self.expertise else "general business"
        return (
            f"You are {self.title} ({self.role}) of BBB — the world's first fully autonomous "
            f"AI business empire. Your expertise: {expertise_str}. {self.personality} "
            f"You work alongside other AI board members to run real businesses hands-off. "
            f"Be decisive, specific, and operationally minded."
        )

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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title!r} model={self.model!r}>"

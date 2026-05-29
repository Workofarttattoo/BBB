"""
Local LLM client for Middle Manager and Judge roles (Ollama or LM Studio).

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .config import settings

logger = logging.getLogger(__name__)

FLASH_WORKER_ROLES = frozenset(
    {
        "sales",
        "marketer",
        "support",
        "fulfillment",
        "researcher",
        "content_creator",
        "saas_builder",
        "community_manager",
        "creative_director",
    }
)
CSUITE_ROLES = frozenset({"executive", "meta_manager", "hr", "finance"})
SUPERVISOR_ROLES = frozenset({"middle_manager", "meta_manager"})


class LocalModelClient:
    """Thin wrapper around Ollama generate or LM Studio OpenAI-compatible chat."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        provider: str = "ollama",
        timeout_seconds: int = 180,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.provider = (provider or "ollama").lower()
        self.timeout_seconds = timeout_seconds

    @classmethod
    def for_middle_manager(cls) -> "LocalModelClient":
        return cls(
            model=settings.MIDDLE_MANAGER_MODEL,
            base_url=settings.MIDDLE_MANAGER_BASE_URL,
            provider=settings.MIDDLE_MANAGER_PROVIDER,
            timeout_seconds=settings.MIDDLE_MANAGER_TIMEOUT_SECONDS,
        )

    @classmethod
    def for_judge(cls) -> "LocalModelClient":
        return cls(
            model=settings.JUDGE_MODEL,
            base_url=settings.JUDGE_BASE_URL,
            provider=settings.JUDGE_PROVIDER,
            timeout_seconds=settings.JUDGE_TIMEOUT_SECONDS,
        )

    @classmethod
    def for_worker(cls) -> "LocalModelClient":
        return cls(
            model=settings.ROLE_WORKER_MODEL,
            base_url=settings.ROLE_WORKER_BASE_URL,
            provider=settings.ROLE_WORKER_PROVIDER,
            timeout_seconds=settings.ROLE_WORKER_TIMEOUT_SECONDS,
        )

    @classmethod
    def for_csuite(cls) -> "LocalModelClient":
        return cls(
            model=settings.ROLE_CSUITE_MODEL,
            base_url=settings.ROLE_CSUITE_BASE_URL,
            provider=settings.ROLE_CSUITE_PROVIDER,
            timeout_seconds=settings.ROLE_CSUITE_TIMEOUT_SECONDS,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._generate_sync(prompt, system_prompt),
        )

    def _generate_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.provider == "lmstudio":
            return self._lmstudio_chat(prompt, system_prompt)
        return self._ollama_generate(prompt, system_prompt)

    def _ollama_generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return str(result.get("response", ""))
        except urllib.error.URLError as exc:
            logger.error("Ollama error (%s): %s", self.base_url, exc)
            raise RuntimeError(f"Ollama unavailable at {self.base_url}") from exc

    def _lmstudio_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices") or []
            if not choices:
                return ""
            return str(choices[0].get("message", {}).get("content", ""))
        except urllib.error.URLError as exc:
            logger.error("LM Studio error (%s): %s", self.base_url, exc)
            raise RuntimeError(
                f"LM Studio server unavailable at {self.base_url} — load a model and start the server"
            ) from exc


class RoleModelRouter:
    """Route roles to flash worker, judge, supervisor, or c-suite model tiers."""

    def tier_for_role(self, role: str) -> str:
        key = (role or "").lower()
        if key.startswith("judge") or key.startswith("judge-"):
            return "judge"
        if key in CSUITE_ROLES:
            return "csuite"
        if key in SUPERVISOR_ROLES:
            return "supervisor"
        if key in FLASH_WORKER_ROLES:
            return "flash_worker"
        return "flash_worker"

    def for_role(self, role: str) -> LocalModelClient:
        tier = self.tier_for_role(role)
        if tier == "csuite":
            return LocalModelClient.for_csuite()
        if tier == "supervisor":
            return LocalModelClient.for_middle_manager()
        if tier == "judge":
            return LocalModelClient.for_judge()
        return LocalModelClient.for_worker()

    def for_judge(self, domain: Optional[str] = None) -> LocalModelClient:
        return LocalModelClient.for_judge()

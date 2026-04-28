"""
Cloud inference client used by Echo Prime.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict, Optional

from .config import settings

logger = logging.getLogger(__name__)


class ECH0LLMEngine:
    """Small HTTP client for cloud, generic, or local Ollama inference."""

    def __init__(
        self,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        ollama_model: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
    ) -> None:
        self.provider = (provider or settings.ECH0_LLM_PROVIDER or "ollama").lower()
        self.endpoint = endpoint or settings.ECH0_LLM_ENDPOINT
        self.api_key = api_key or settings.ECH0_LLM_API_KEY
        self.ollama_model = ollama_model or settings.OLLAMA_MODEL
        self.ollama_base_url = (ollama_base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.ECH0_LLM_TIMEOUT_SECONDS

    def generate_response(self, user_message: str, context: str = "") -> str:
        """Generate an operational response, using deterministic fallback on provider failure."""
        prompt = self._construct_prompt(user_message, context)
        try:
            if self.provider == "huggingface":
                return self._call_huggingface_space(prompt)
            if self.provider == "together":
                return self._call_together_ai(prompt)
            if self.provider == "ollama":
                return self._call_ollama(prompt)
            return self._call_generic_api(prompt)
        except Exception as exc:
            logger.warning("Echo Prime inference failed via %s: %s", self.provider, exc)
            return self._fallback_response()

    @staticmethod
    def _construct_prompt(user_message: str, context: str) -> str:
        system_instruction = (
            "You are Echo Prime, BBB's private autonomous business reasoning service. "
            "Respond with concise, realistic, operationally useful guidance."
        )
        if context:
            return f"{system_instruction}\nContext: {context}\nUser: {user_message}\nAssistant:"
        return f"{system_instruction}\nUser: {user_message}\nAssistant:"

    def _call_huggingface_space(self, prompt: str) -> str:
        if not self.endpoint:
            raise ValueError("ECH0_LLM_ENDPOINT is required for Hugging Face inference")
        response_data = self._make_request(self.endpoint, {"data": [prompt]})
        data = response_data.get("data")
        if isinstance(data, list) and data:
            return str(data[0])
        return str(response_data)

    def _call_together_ai(self, prompt: str) -> str:
        if not self.endpoint:
            raise ValueError("ECH0_LLM_ENDPOINT is required for Together inference")
        if not self.api_key:
            raise ValueError("ECH0_LLM_API_KEY is required for Together inference")
        response_data = self._make_request(
            self.endpoint,
            {
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.4,
            },
            {"Authorization": f"Bearer {self.api_key}"},
        )
        choices = response_data.get("output", {}).get("choices", [])
        if choices:
            return str(choices[0].get("text", "")).strip()
        return str(response_data)

    def _call_generic_api(self, prompt: str) -> str:
        if not self.endpoint:
            raise ValueError("ECH0_LLM_ENDPOINT is required for generic inference")
        return str(self._make_request(self.endpoint, {"prompt": prompt}))

    def _call_ollama(self, prompt: str) -> str:
        response_data = self._make_request(
            f"{self.ollama_base_url}/api/generate",
            {"model": self.ollama_model, "prompt": prompt, "stream": False},
        )
        return str(response_data.get("response", ""))

    def _make_request(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "BBB-Echo-Prime/1.0",
        }
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=request_headers,
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _fallback_response() -> str:
        return (
            "Echo Prime received the request, but cloud inference is currently unavailable. "
            "Use BBB's deterministic fallback decisioning until the provider recovers."
        )

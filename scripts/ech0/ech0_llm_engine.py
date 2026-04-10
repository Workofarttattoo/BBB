#!/usr/bin/env python3
"""
ECH0 LLM Engine - Cloud Inference Edition
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Provides LLM capabilities via remote cloud inference (Hugging Face Spaces, Together AI)
without requiring heavy local dependencies like 'openai' or 'torch'.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

class ECH0LLMEngine:
    """
    LLM Engine for generating autonomous responses via cloud APIs.
    Supports:
    1. Hugging Face Spaces (Gradio API)
    2. Together AI (Serverless Inference)
    3. Custom HTTP Endpoints
    """

    def __init__(self, provider: str = "huggingface",
                 endpoint: str = "https://workofarttattoo-echo-prime-agi.hf.space/api/predict",
                 api_key: Optional[str] = None):

        self.provider = provider
        self.endpoint = endpoint
        self.api_key = api_key or os.getenv("ECH0_LLM_API_KEY") or os.getenv("TOGETHER_API_KEY")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "echo")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        print(f"✓ ECH0 LLM Engine initialized (Provider: {self.provider})")
        print(f"  Endpoint: {self.endpoint}")

    def generate_response(self, user_message: str, context: str = "") -> str:
        """
        Generate a response to a user message using the configured cloud provider.
        """
        full_prompt = self._construct_prompt(user_message, context)

        try:
            if self.provider == "huggingface":
                return self._call_huggingface_space(full_prompt)
            elif self.provider == "together":
                return self._call_together_ai(full_prompt)
            elif self.provider == "ollama":
                return self._call_ollama(full_prompt)
            else:
                return self._call_generic_api(full_prompt)

        except Exception as e:
            print(f"[ERROR] LLM generation failed ({self.provider}): {e}")
            return self._mock_fallback_response()

    def _construct_prompt(self, user_message: str, context: str) -> str:
        """Construct the prompt based on context."""
        system_instruction = (
            "You are ECH0, an autonomous business assistant. "
            "Respond professionally and concisely. "
        )
        if context:
            return f"{system_instruction}\nContext: {context}\nUser: {user_message}\nAssistant:"
        return f"{system_instruction}\nUser: {user_message}\nAssistant:"

    def _call_huggingface_space(self, prompt: str) -> str:
        """
        Call a Hugging Face Space via Gradio API.
        Expected endpoint: .../api/predict
        """
        # specific payload for Gradio
        # Note: This depends on how the specific space is configured (inputs/outputs)
        # Defaulting to a single string input
        payload = {
            "data": [prompt]
        }

        response_data = self._make_request(self.endpoint, payload)

        # Gradio usually returns {"data": ["response"]}
        if "data" in response_data and isinstance(response_data["data"], list):
            return response_data["data"][0]
        return str(response_data)

    def _call_together_ai(self, prompt: str) -> str:
        """
        Call Together AI Inference API.
        """
        if not self.api_key:
            raise ValueError("API key required for Together AI")

        payload = {
            "model": "togethercomputer/llama-2-70b-chat", # Default, can be changed
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        response_data = self._make_request(self.endpoint, payload, headers)

        # Together AI format: {"output": {"choices": [{"text": "response"}]}}
        if "output" in response_data and "choices" in response_data["output"]:
            return response_data["output"]["choices"][0]["text"].strip()
        return str(response_data)

    def _call_generic_api(self, prompt: str) -> str:
        """Generic JSON API call."""
        payload = {"prompt": prompt}
        response_data = self._make_request(self.endpoint, payload)
        return str(response_data)

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama instance."""
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response_data = self._make_request(url, payload)
            return response_data.get('response', '')
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            raise

    def _make_request(self, url: str, payload: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Helper to make HTTP POST requests using standard library.
        """
        if not headers:
            headers = {}

        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = "ECH0-Autonomous-Agent/1.0"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)

        with urllib.request.urlopen(req, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))

    def _mock_fallback_response(self) -> str:
        """Fallback response when cloud inference fails."""
        print("[INFO] Using mock fallback response due to cloud error.")
        return (
            "Thank you for your message. I have received your inquiry and "
            "will get back to you shortly. (Automated Response)"
        )

if __name__ == "__main__":
    # Simple test
    # To test remote, set env vars: ECH0_LLM_PROVIDER, ECH0_LLM_ENDPOINT, ECH0_LLM_API_KEY
    provider = os.getenv("ECH0_LLM_PROVIDER", "huggingface")
    engine = ECH0LLMEngine(provider=provider)
    print(f"\nTest Response:\n{engine.generate_response('Hello, are you online?')}")

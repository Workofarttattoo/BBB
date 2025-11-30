#!/usr/bin/env python3
"""
ECH0 LLM Engine - Local LLM Integration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Connects to local ech0 LLM (Ollama-based) for autonomous message responses.
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime


class ECH0LLMEngine:
    """
    Interface to local ech0 LLM for generating autonomous responses.
    Supports Ollama API and custom endpoints.
    """

    def __init__(
        self,
        model: str = "ech0-knowledge-v4",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the LLM engine.

        Args:
            model: Model name to use (default: ech0-knowledge-v4)
            base_url: Base URL for LLM API (default: http://localhost:11434)
            api_key: API key if required (reads from env if not provided)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url or os.getenv("ECH0_LLM_URL", "http://localhost:11434")
        self.api_key = api_key or os.getenv("ECH0_LLM_API_KEY")
        self.timeout = timeout

        # Determine if we're using Ollama or custom API
        self.is_ollama = "11434" in self.base_url or "ollama" in self.base_url.lower()

        print(f"[ECH0_LLM] Initialized with model: {self.model}")
        print(f"[ECH0_LLM] Endpoint: {self.base_url}")
        print(f"[ECH0_LLM] API Type: {'Ollama' if self.is_ollama else 'Custom'}")

    def generate_fiverr_response(
        self,
        message: str,
        context: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a professional Fiverr message response.

        Args:
            message: The incoming message to respond to
            context: Additional context (sender name, gig info, etc.)
            system_prompt: Custom system prompt (optional)

        Returns:
            Generated response text
        """
        if system_prompt is None:
            system_prompt = self._get_default_fiverr_system_prompt()

        # Build the prompt
        user_prompt = self._build_fiverr_prompt(message, context)

        # Generate response
        response = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.7
        )

        return response

    def generate_order_update(
        self,
        order_info: Dict,
        status: str,
        custom_message: Optional[str] = None
    ) -> str:
        """
        Generate an order status update message.

        Args:
            order_info: Order details (order_id, buyer, requirements, etc.)
            status: Order status (started, in_progress, delivered, etc.)
            custom_message: Additional custom message

        Returns:
            Generated order update message
        """
        system_prompt = """You are a professional Fiverr seller providing order updates.
Be concise, professional, and reassuring. Keep updates brief but informative."""

        user_prompt = f"""Generate a professional order update message for Fiverr.

Order ID: {order_info.get('order_id', 'N/A')}
Buyer: {order_info.get('buyer_name', 'Customer')}
Status: {status}
{'Additional info: ' + custom_message if custom_message else ''}

Generate a brief, professional update message (2-3 sentences max)."""

        return self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.6
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate text using the local LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt to guide behavior
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stream: Whether to stream the response

        Returns:
            Generated text
        """
        try:
            if self.is_ollama:
                return self._generate_ollama(prompt, system_prompt, max_tokens, temperature, stream)
            else:
                return self._generate_custom(prompt, system_prompt, max_tokens, temperature, stream)
        except Exception as e:
            print(f"[ECH0_LLM] Error generating response: {e}")
            return self._get_fallback_response()

    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stream: bool
    ) -> str:
        """Generate using Ollama API."""
        endpoint = f"{self.base_url}/api/generate"

        # Build full prompt with system context
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()

        if stream:
            # Handle streaming response
            full_text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        full_text += data["response"]
                    if data.get("done", False):
                        break
            return full_text.strip()
        else:
            # Non-streaming response
            data = response.json()
            return data.get("response", "").strip()

    def _generate_custom(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stream: bool
    ) -> str:
        """Generate using custom API endpoint."""
        endpoint = f"{self.base_url}/v1/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _build_fiverr_prompt(self, message: str, context: Optional[Dict]) -> str:
        """Build a complete prompt for Fiverr message response."""
        context = context or {}

        prompt_parts = [
            "Generate a professional Fiverr response to the following message:",
            "",
            f"MESSAGE: {message}",
            ""
        ]

        if context.get("sender_name"):
            prompt_parts.append(f"Sender: {context['sender_name']}")

        if context.get("gig_title"):
            prompt_parts.append(f"Regarding Gig: {context['gig_title']}")

        if context.get("additional_context"):
            prompt_parts.append(f"Context: {context['additional_context']}")

        prompt_parts.extend([
            "",
            "Requirements:",
            "- Be professional and friendly",
            "- Address their question/concern directly",
            "- Keep it concise (2-4 sentences)",
            "- End with a call to action if appropriate",
            "- Do NOT include signature or name",
            "",
            "Response:"
        ])

        return "\n".join(prompt_parts)

    def _get_default_fiverr_system_prompt(self) -> str:
        """Get default system prompt for Fiverr responses."""
        return """You are an experienced, professional Fiverr seller with excellent communication skills.
Your responses are:
- Professional yet friendly
- Clear and concise
- Helpful and solution-oriented
- Free of spelling/grammar errors
- Appropriately enthusiastic without being overeager

You specialize in providing high-quality services and maintaining excellent client relationships."""

    def _get_fallback_response(self) -> str:
        """Return a safe fallback response if LLM fails."""
        return """Thank you for your message! I've received your inquiry and will review it carefully.
I'll get back to you with a detailed response within the next few hours.
Looking forward to working with you!"""

    def health_check(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if self.is_ollama:
                # Check Ollama tags endpoint
                response = requests.get(
                    f"{self.base_url}/api/tags",
                    timeout=5
                )
                response.raise_for_status()
                print(f"[ECH0_LLM] Health check: OK")
                return True
            else:
                # Try a minimal generation
                test_response = self.generate(
                    prompt="Hello",
                    max_tokens=5,
                    temperature=0.1
                )
                print(f"[ECH0_LLM] Health check: OK")
                return bool(test_response)
        except Exception as e:
            print(f"[ECH0_LLM] Health check failed: {e}")
            return False


# Convenience function for quick usage
def generate_fiverr_response(message: str, context: Optional[Dict] = None) -> str:
    """
    Quick function to generate a Fiverr response without instantiating the class.

    Args:
        message: Incoming message to respond to
        context: Optional context dictionary

    Returns:
        Generated response
    """
    engine = ECH0LLMEngine()
    return engine.generate_fiverr_response(message, context)


# Testing/CLI usage
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ECH0 LLM Engine - Test Mode                                 ║")
    print("║  Copyright (c) 2025 Joshua Hendricks Cole                    ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Initialize engine
    engine = ECH0LLMEngine()

    # Health check
    print("\n[TEST] Running health check...")
    if engine.health_check():
        print("✓ LLM service is available\n")

        # Test Fiverr response generation
        print("[TEST] Generating sample Fiverr response...\n")
        test_message = "Hi! I'm interested in your service. Can you help me with a custom project?"
        test_context = {
            "sender_name": "John",
            "gig_title": "Professional AI Integration Services"
        }

        response = engine.generate_fiverr_response(test_message, test_context)
        print(f"INPUT MESSAGE:\n{test_message}\n")
        print(f"GENERATED RESPONSE:\n{response}\n")
    else:
        print("✗ LLM service is not available")
        print("  Please check that your local LLM is running")
        print(f"  Expected endpoint: {engine.base_url}")

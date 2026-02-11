#!/usr/bin/env python3
"""
ECH0 LLM Engine
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Provides LLM capabilities for the autonomous business system.
"""

import os
from typing import Optional

# Try to import OpenAI, but don't crash if it's missing (for limited environments)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] OpenAI library not found. LLM engine will operate in mock mode.")


class ECH0LLMEngine:
    """
    LLM Engine for generating autonomous responses.
    Handles Fiverr messages, blog posts, and other content generation tasks.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✓ ECH0 LLM Engine initialized (OpenAI connected)")
            except Exception as e:
                print(f"[ERROR] Failed to initialize OpenAI client: {e}")
        else:
            if not OPENAI_AVAILABLE:
                print("[INFO] ECH0 LLM Engine running in MOCK mode (library missing)")
            elif not self.api_key:
                print("[INFO] ECH0 LLM Engine running in MOCK mode (API key missing)")

    def generate_response(self, user_message: str, context: str = "") -> str:
        """
        Generate a response to a user message.
        """
        if not self.client:
            return self._mock_response(user_message)

        try:
            # System prompt setup
            system_prompt = (
                "You are ECH0, an autonomous business assistant operating a Fiverr account. "
                "Respond professionally, concisely, and helpfully to the client's message. "
                "Do not promise specific delivery times unless explicitly known. "
                "If the request is unclear, ask for clarification. "
                "Keep responses under 150 words."
            )

            if context:
                system_prompt += f"\n\nContext: {context}"

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            return self._mock_fallback_response()

    def _mock_response(self, user_message: str) -> str:
        """Generate a mock response when LLM is unavailable."""
        print(f"[MOCK LLM] Generating response for: {user_message[:50]}...")
        return (
            "Thank you for your message. This is an automated response from ECH0 system. "
            "I have received your inquiry and will get back to you shortly. "
            "(Note: AI response engine is currently in offline mode)"
        )

    def _mock_fallback_response(self) -> str:
        """Fallback response in case of API errors."""
        return (
            "Thank you for your message. I'm currently experiencing high traffic but "
            "I have logged your request and will respond as soon as possible."
        )

if __name__ == "__main__":
    # Test the engine
    engine = ECH0LLMEngine()
    response = engine.generate_response("Hi, can you design a logo for me?")
    print(f"\nResponse:\n{response}")

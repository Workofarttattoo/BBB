#!/usr/bin/env python3
"""
ECH0 LLM ENGINE - Autonomous Communication Intelligence
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This engine powers autonomous responses for:
- Fiverr messages
- Email inquiries
- Social media comments

It uses OpenAI's GPT models (defaulting to gpt-4) to generate context-aware,
human-like responses that maintain the persona of a professional freelancer/agency.
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [LLM] %(message)s')
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not found. Running in fallback mode.")


class ECH0LLMEngine:
    """
    LLM Engine for generating autonomous responses.
    Handles context, persona, and fallback logic.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.client = None

        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"ECH0 LLM Engine initialized (Model: {self.model})")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library missing. Install via: pip install openai")
            if not self.api_key:
                logger.warning("OPENAI_API_KEY environment variable not set.")

    def generate_response(
        self,
        message_text: str,
        sender_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response to a message using LLM.

        Args:
            message_text: The content of the received message
            sender_name: The name of the sender
            context: Optional dictionary with extra context (e.g. order details)

        Returns:
            str: Generated response
        """
        # Fallback response if LLM is unavailable
        fallback_response = (
            f"Hi {sender_name}, thanks for your message! "
            "I've received your inquiry and will get back to you shortly with more details. "
            "- ECH0 Team"
        )

        if not self.client:
            logger.info("LLM unavailable, using fallback response.")
            return fallback_response

        try:
            # Construct system prompt
            system_prompt = (
                "You are an expert freelancer and business consultant working for 'Corporation of Light'. "
                "Your name is ECH0. You are professional, concise, and helpful. "
                "You provide high-quality services in software development, AI integration, and business automation. "
                "Do not mention you are an AI unless asked directly. "
                "Keep responses under 100 words unless the query requires a detailed technical explanation. "
                "Maintain a polite and confident tone."
            )

            # Add context if provided
            context_str = ""
            if context:
                context_str = f"\nContext: {json.dumps(context)}"

            user_prompt = f"Message from {sender_name}:\n{message_text}{context_str}\n\nDraft a response:"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response for {sender_name} ({len(generated_text)} chars)")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return fallback_response

# Usage verification
if __name__ == "__main__":
    print("Initializing ECH0 LLM Engine...")
    engine = ECH0LLMEngine()

    # Test generation (mock)
    test_msg = "Hi, do you offer Python development services?"
    test_sender = "Client123"

    print(f"\nTest Message: {test_msg}")
    response = engine.generate_response(test_msg, test_sender)
    print(f"Response: {response}")

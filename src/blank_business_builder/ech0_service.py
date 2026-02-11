"""
ECH0 Service integration for Blank Business Builder.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations
import asyncio
import random
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# It is assumed that ech0_local_brain is available in the python path
try:
    from ech0_local_brain import ECH0LocalBrain
    ECH0_AVAILABLE = True
except ImportError:
    ECH0LocalBrain = None
    ECH0_AVAILABLE = False


class ECH0Service:
    """
    Service for interacting with the ECH0 local brain.
    """

    def __init__(self, model: str = "ech0-unified-14b:latest", session_id_prefix: str = "bbb"):
        self.model = model
        self.session_id_prefix = session_id_prefix

    async def _get_ech0_response(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Get a response from the ECH0 local brain.
        """
        if not ECH0_AVAILABLE:
            logger.warning(f"ECH0 Brain Unavailable. Cannot process prompt: {prompt[:50]}...")
            return f"[ECH0 UNAVAILABLE] Context: {prompt[:50]}..."

        session_id = f"{self.session_id_prefix}_{random.randint(1000, 9999)}"
        ech0 = ECH0LocalBrain(model=self.model, session_id=session_id)
        response_data = await ech0.send_message(prompt, use_temporal=True, max_tokens=max_tokens, timeout=None)
        return response_data.get('response', '')

    async def generate_content(self, topic: str, content_type: str) -> str:
        """
        Generate content using ECH0.
        """
        prompt = f"Generate a {content_type} about {topic}."
        return await self._get_ech0_response(prompt)

    async def send_email(self, from_email: str, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email using ECH0's capabilities.
        """
        prompt = f"Send an email from {from_email} to {to_email} with subject '{subject}' and body:\n{body}"
        response = await self._get_ech0_response(prompt)
        return "success" in response.lower()

    async def post_to_social_media(self, platform: str, content: str) -> bool:
        """
        Post to social media using ECH0's capabilities.
        """
        prompt = f"Post the following content to {platform}:\n{content}"
        response = await self._get_ech0_response(prompt)
        return "success" in response.lower()

    async def scrape_url(self, url: str) -> str:
        """
        Scrape the content of a URL using ECH0.
        """
        prompt = f"Scrape the content of the URL: {url}"
        return await self._get_ech0_response(prompt)

    async def google_search(self, query: str) -> str:
        """
        Perform a Google search using ECH0.
        """
        prompt = f"Perform a Google search for: {query} and return the results."
        return await self._get_ech0_response(prompt)

    async def create_checkout_session(self, price_id: str, success_url: str, cancel_url: str) -> str:
        """
        Create a Stripe checkout session using ECH0.
        """
        prompt = f"Create a Stripe checkout session with price ID {price_id}, success URL {success_url}, and cancel URL {cancel_url}."
        return await self._get_ech0_response(prompt)

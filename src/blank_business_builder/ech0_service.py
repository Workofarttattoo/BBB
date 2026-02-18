"""
ECH0 Service integration for Blank Business Builder via Ollama.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations
import asyncio
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Optional
from .task_queue import task_queue
from .semantic_framework import semantic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ECH0Service:
    """
    Service for interacting with the ECH0 local brain via Ollama.
    """

    def __init__(self, model: str = "echo", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.system_prompt = (
            "You are Echo, an advanced autonomous business orchestrator. "
            "Your goal is to help the user build and manage a successful business empire. "
            "Be helpful, concise, and professional."
        )

    async def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call the local Ollama instance.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": system_prompt or self.system_prompt
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req).read())
            result = json.loads(response.decode('utf-8'))
            return result.get('response', '')
        except urllib.error.URLError as e:
            logger.error(f"Ollama connection error: {e}")
            return "I am currently unable to connect to my local neural core (Ollama). Please ensure it is running on port 11434."
        except Exception as e:
            logger.error(f"Error invoking ECH0: {e}")
            return f"Error: {str(e)}"

    async def generate(self, prompt: str, schema: Optional[Any] = None) -> str:
        """
        Semantic-aware generation.
        """
        if schema:
            prompt = f"Using semantic schema {str(schema)}, {prompt}"
        return await self._call_ollama(prompt)

    async def chat(self, message: str) -> str:
        """
        Direct chat interface for the GUI.
        """
        return await self._call_ollama(message)

    async def generate_content(self, topic: str, content_type: str) -> str:
        """
        Generate content using ECH0.
        """
        prompt = f"Generate a {content_type} about {topic}."
        return await self._call_ollama(prompt)

    async def send_email(self, from_email: str, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email using ECH0's capabilities (Queued via TaskQueue).
        """
        payload = {
            "to_email": to_email,
            "subject": subject,
            "html_content": body,
            "from_name": from_email
        }
        task_queue.add_task("send_email", payload)
        logger.info(f"ECH0 queued email: From {from_email} to {to_email}")
        return True

    async def post_to_social_media(self, platform: str, content: str) -> bool:
        """
        Post to social media using ECH0's capabilities.
        """
        # In a real scenario, we'd map 'platform' to a Buffer profile ID.
        # For now, we queue it with the platform name as ID.
        payload = {
            "profile_id": platform,
            "text": content
        }
        task_queue.add_task("create_post", payload)
        logger.info(f"ECH0 queued social post: {platform} -> {content}")
        return True

    async def scrape_url(self, url: str) -> str:
        """
        Scrape the content of a URL using ECH0 (Simulated).
        """
        logger.info(f"ECH0 analyzing URL: {url}")
        # In a real scenario, we might fetch the content and summarize it
        return await self._call_ollama(f"Summarize what one might find at {url}")

    async def google_search(self, query: str) -> str:
        """
        Perform a Google search using ECH0.
        """
        logger.info(f"ECH0 searching: {query}")
        return await self._call_ollama(f"What would be the top results for '{query}'?")

    async def create_checkout_session(self, price_id: str, success_url: str, cancel_url: str) -> str:
        """
        Create a Stripe checkout session using ECH0 logic (or just mocking it).
        """
        logger.info(f"ECH0 creating checkout: {price_id}")
        return "checkout_session_id_mocked"

"""
Integration container/factory for provider clients.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .apollo import ApolloService
from .legacy import (
    AnthropicService,
    BufferService,
    ECH0Service,
    OpenAIService,
    SendGridService,
    TwilioService,
    TwitterService,
)
from .legacy import IntegrationFactory as LegacyIntegrationFactory
from .slack import SlackService
from .elevenlabs_voice import ElevenLabsVoiceAgent


@dataclass
class IntegrationContainer:
    """Holds instantiated provider clients for outreach orchestration."""

    voice: ElevenLabsVoiceAgent = field(default_factory=ElevenLabsVoiceAgent)
    apollo: ApolloService = field(default_factory=ApolloService)
    slack: SlackService = field(default_factory=SlackService)


class IntegrationFactory(LegacyIntegrationFactory):
    """Backwards-compatible factory + new provider clients."""

    _container: Optional[IntegrationContainer] = None

    @classmethod
    def get_container(cls) -> IntegrationContainer:
        if cls._container is None:
            cls._container = IntegrationContainer()
        return cls._container

    @classmethod
    def get_voice_agent(cls) -> ElevenLabsVoiceAgent:
        return cls.get_container().voice

    @classmethod
    def get_apollo_service(cls) -> ApolloService:
        return cls.get_container().apollo

    @classmethod
    def get_slack_service(cls) -> SlackService:
        return cls.get_container().slack

    # Compatibility alias for older celery task code.
    @staticmethod
    def get_email_service() -> SendGridService:
        return SendGridService()


__all__ = [
    "AnthropicService",
    "ApolloService",
    "BufferService",
    "ECH0Service",
    "ElevenLabsVoiceAgent",
    "IntegrationContainer",
    "IntegrationFactory",
    "OpenAIService",
    "SendGridService",
    "SlackService",
    "TwilioService",
    "TwitterService",
]

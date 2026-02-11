"""
Tests for AnthropicService Integration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
import sys
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies that might be missing in the environment
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.status"] = MagicMock()
sys.modules["anthropic"] = MagicMock() # Mock anthropic to ensure we test the service logic with library present or absent

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder import integrations

class TestAnthropicService:
    """Test AnthropicService functionality."""

    def setup_method(self):
        # Reload module to ensure we use current mocks/classes
        importlib.reload(integrations)
        self.AnthropicService = integrations.AnthropicService
        self.IntegrationFactory = integrations.IntegrationFactory

    def test_initialization(self):
        """Test that AnthropicService initializes correctly."""
        service = self.AnthropicService()
        assert hasattr(service, "generate_content")

    def test_factory_method(self):
        """Test that IntegrationFactory returns an AnthropicService instance."""
        service = self.IntegrationFactory.get_anthropic_service()
        assert isinstance(service, self.AnthropicService)

    def test_generate_content_mock(self):
        """Test generate_content with mocked client."""
        service = self.AnthropicService()
        # Mock the client
        service.client = MagicMock()
        service.client.messages.create.return_value.content = [MagicMock(text="Mocked response")]

        response = service.generate_content("Test prompt")
        assert response == "Mocked response"

    def test_generate_content_fallback(self):
        """Test generate_content fallback behavior."""
        # If client raises error
        service = self.AnthropicService()
        service.client = MagicMock()
        service.client.messages.create.side_effect = Exception("Authentication error: api_key invalid")

        response = service.generate_content("Test prompt")
        assert "[Claude Simulation]" in response

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

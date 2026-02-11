import sys
import asyncio
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["anthropic"] = MagicMock()

# Mock the internal module that causes issues
mock_integrations = MagicMock()
sys.modules["src.blank_business_builder.integrations"] = mock_integrations

import pytest

from src.blank_business_builder.features.ai_content_generator import (
    AIContentGenerator,
    ContentRequest,
    ContentType,
    AIModel
)

def test_generate_with_claude_placeholder():
    """Test that _generate_with_claude returns the placeholder string."""
    generator = AIContentGenerator()

    request = ContentRequest(
        content_type=ContentType.BLOG_POST,
        topic="Code Health",
        tone="Professional",
        length="Short",
        keywords=["refactoring"],
        target_audience="Developers",
        ai_model=AIModel.CLAUDE_OPUS
    )

    result = asyncio.run(generator._generate_with_claude("Test prompt", request))

    assert "[Claude-Generated Content]" in result
    assert "Code Health" in result

def test_generate_with_gemini_placeholder():
    """Test that _generate_with_gemini returns the placeholder string."""
    generator = AIContentGenerator()

    request = ContentRequest(
        content_type=ContentType.BLOG_POST,
        topic="Gemini Test",
        tone="Professional",
        length="Short",
        keywords=[],
        target_audience="Developers",
        ai_model=AIModel.GEMINI_PRO
    )

    result = asyncio.run(generator._generate_with_gemini("Test prompt", request))

    assert "[Gemini-Generated Content]" in result
    assert "Gemini Test" in result

def test_generate_with_openai_fallback():
    """Test that _generate_with_openai falls back to placeholder on error."""
    generator = AIContentGenerator()

    request = ContentRequest(
        content_type=ContentType.BLOG_POST,
        topic="OpenAI Fail",
        tone="Professional",
        length="Short",
        keywords=[],
        target_audience="Developers",
        ai_model=AIModel.GPT4
    )

    result = asyncio.run(generator._generate_with_openai("Test prompt", request))

    assert "[OpenAI-Generated Content]" in result
    assert "OpenAI Fail" in result

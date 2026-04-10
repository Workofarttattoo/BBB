"""
Tests for AI Content Generator placeholder/fallback behaviour.

These tests validate that each model's generator returns a sensible
placeholder when the real API is unavailable.
"""

import sys
import asyncio
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# We need lightweight mocks for optional heavy deps that the module
# tries to import at the top level.  Instead of polluting sys.modules
# permanently (which breaks other tests that import the real package),
# we save/restore them properly.
# ---------------------------------------------------------------------------
_MOCKED_MODULES = {}


def setup_module(module):
    """Temporarily mock heavy optional deps before import."""
    for mod_name in ("anthropic",):
        if mod_name not in sys.modules:
            _MOCKED_MODULES[mod_name] = None
            sys.modules[mod_name] = MagicMock()
        else:
            _MOCKED_MODULES[mod_name] = sys.modules[mod_name]


def teardown_module(module):
    """Restore original modules."""
    for mod_name, original in _MOCKED_MODULES.items():
        if original is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = original


from src.blank_business_builder.features.ai_content_generator import (
    AIContentGenerator,
    ContentRequest,
    ContentType,
    AIModel,
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
        ai_model=AIModel.CLAUDE_OPUS,
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
        ai_model=AIModel.GEMINI_PRO,
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
        ai_model=AIModel.GPT4,
    )

    result = asyncio.run(generator._generate_with_openai("Test prompt", request))

    assert "[OpenAI-Generated Content]" in result
    assert "OpenAI Fail" in result

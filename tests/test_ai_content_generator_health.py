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

import types
mock_sqla = MagicMock()
sys.modules['sqlalchemy'] = mock_sqla
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.types'] = MagicMock()

mock_sqla_dialects = MagicMock()
mock_sqla_postgresql = MagicMock()
sys.modules['sqlalchemy.dialects'] = mock_sqla_dialects
sys.modules['sqlalchemy.dialects.postgresql'] = mock_sqla_postgresql

# completely mock the database module to bypass SQLAlchemy StopIteration
sys.modules['src.blank_business_builder.database'] = MagicMock()
sys.modules['src.blank_business_builder.level6_agent'] = MagicMock()
sys.modules['src.blank_business_builder.features.marketing_automation'] = MagicMock()



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


if __name__ == '__main__':
    test_generate_with_claude_placeholder()
    test_generate_with_gemini_placeholder()
    test_generate_with_openai_fallback()
    print('All health tests passed.')

import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


# Mock missing dependencies
mock_openai = MagicMock()
mock_openai.OpenAI = MagicMock()
sys.modules['openai'] = mock_openai

mock_requests = MagicMock()
sys.modules['requests'] = mock_requests

mock_fastapi = MagicMock()
mock_fastapi.HTTPException = Exception
mock_fastapi.status = MagicMock()
sys.modules['fastapi'] = mock_fastapi

class MockSQLAlchemy(MagicMock):
    pass
mock_sqla = MockSQLAlchemy()
sys.modules['sqlalchemy'] = mock_sqla
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.types'] = MagicMock()

import types
mock_sqla_dialects = MagicMock()
mock_sqla_postgresql = MagicMock()
sys.modules['sqlalchemy.dialects'] = mock_sqla_dialects
sys.modules['sqlalchemy.dialects.postgresql'] = mock_sqla_postgresql

# completely mock the database module to bypass SQLAlchemy StopIteration
sys.modules['src.blank_business_builder.database'] = MagicMock()
sys.modules['src.blank_business_builder.level6_agent'] = MagicMock()
sys.modules['src.blank_business_builder.features.marketing_automation'] = MagicMock()

# Now import the module under test
# We no longer need to mock ech0_service module because we fixed the import in source
from src.blank_business_builder.features.ai_content_generator import AIContentGenerator, ContentRequest, ContentType, AIModel

def test_generate_content_gpt4():
    """Verify that AIContentGenerator works for GPT4 with mocked dependencies."""

    async def run_test():
        # Setup mock ECH0Service instance
        # Since ECH0Service is imported in ai_content_generator, we patch it there
        with patch('src.blank_business_builder.features.ai_content_generator.ECH0Service') as MockECH0:
            mock_ech0_instance = MockECH0.return_value
            # Make ECH0 fail so fallback to OpenAI is triggered
            mock_ech0_instance.generate_content = AsyncMock(side_effect=Exception("ECH0 Failed"))

            # Instantiate
            generator = AIContentGenerator()

            # Verify AIModel does NOT have LLAMA_3 (confirming removal)
            assert not hasattr(AIModel, 'LLAMA_3'), "AIModel should NOT have LLAMA_3"

            # Verify basic functionality for GPT4
            request = ContentRequest(
                content_type=ContentType.BLOG_POST,
                topic="Testing GPT4",
                tone="professional",
                length="short",
                keywords=["test"],
                target_audience="developers",
                ai_model=AIModel.GPT4
            )

            # Mock internal methods to isolate generate_content logic
            generator._generate_with_openai = AsyncMock(return_value="[GPT4 Content]")
            generator._generate_quantum_variations = AsyncMock(return_value=["var1"])
            generator._optimize_for_seo = AsyncMock(side_effect=lambda c, k: c)
            generator._generate_meta_description = AsyncMock(return_value="meta")
            generator._calculate_seo_score = AsyncMock(return_value=80.0)
            generator._generate_image_suggestions = AsyncMock(return_value=[])
            generator._extract_title = AsyncMock(return_value="Title")

            # Call generate_content
            result = await generator.generate_content(request)

            # Verify content is from OpenAI
            assert "[GPT4 Content]" in result.body
            assert result.ai_model_used == AIModel.GPT4

    asyncio.run(run_test())

if __name__ == "__main__":
    test_generate_content_gpt4()

def test_generate_placeholder_content():
    """Verify that _generate_placeholder_content returns the correctly formatted string."""
    generator = AIContentGenerator()

    request = ContentRequest(
        content_type=ContentType.BLOG_POST,
        topic="Testing Placeholders",
        tone="professional",
        length="short",
        keywords=[],
        target_audience="developers",
        ai_model=AIModel.GPT4
    )

    model_name = "TEST_MODEL"
    result = generator._generate_placeholder_content(model_name, request)

    assert "[TEST_MODEL-Generated Content]" in result
    assert "Testing Placeholders" in result
    assert result == f"[{model_name}-Generated Content]\n\nHigh-quality content about {request.topic}"

if __name__ == "__main__":
    test_generate_content_gpt4()
    test_generate_placeholder_content()
    print("All tests passed.")

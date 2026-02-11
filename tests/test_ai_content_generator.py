import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

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

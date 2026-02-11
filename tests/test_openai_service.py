"""
Tests for OpenAIService Integration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import pytest
import sys
import json
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies for initial import
sys.modules["openai"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.status"] = MagicMock()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder import integrations

class TestOpenAIService:
    """Test OpenAIService functionality."""

    def setup_method(self):
        # Mock dependencies
        self.mock_openai = MagicMock()
        sys.modules["openai"] = self.mock_openai
        sys.modules["requests"] = MagicMock()

        # Mock FastAPI
        class MockHTTPException(Exception):
            def __init__(self, status_code, detail):
                self.status_code = status_code
                self.detail = detail

        mock_fastapi = MagicMock()
        mock_fastapi.HTTPException = MockHTTPException
        mock_fastapi.status = MagicMock()
        mock_fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
        sys.modules["fastapi"] = mock_fastapi
        sys.modules["fastapi.status"] = mock_fastapi.status

        # Reload module to ensure it uses our mocks
        importlib.reload(integrations)
        self.OpenAIService = integrations.OpenAIService
        self.IntegrationFactory = integrations.IntegrationFactory
        self.MockHTTPException = MockHTTPException

        # Setup OpenAI mock details
        self.mock_openai.ChatCompletion = MagicMock()

    def test_initialization(self):
        """Test that OpenAIService initializes correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-4-test'}):
            service = self.OpenAIService()
            assert service.api_key == 'test-key'
            assert service.model == 'gpt-4-test'
            assert self.mock_openai.api_key == 'test-key'

    def test_generate_business_plan_success(self):
        """Test generating a business plan successfully."""
        service = self.OpenAIService()

        # Mock successful response
        expected_plan = {
            "executive_summary": "Summary",
            "market_analysis": "Analysis",
            "marketing_strategy": "Strategy",
            "financial_projections": "Projections",
            "operations_plan": "Plan"
        }

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(expected_plan)

        self.mock_openai.ChatCompletion.create.return_value = mock_response

        plan = service.generate_business_plan(
            "Test Biz", "Tech", "A test business"
        )

        assert plan == expected_plan
        self.mock_openai.ChatCompletion.create.assert_called_once()

        # Verify call arguments contain correct prompts
        call_args = self.mock_openai.ChatCompletion.create.call_args
        assert call_args.kwargs['model'] == service.model
        assert "Test Biz" in call_args.kwargs['messages'][1]['content']

    def test_generate_business_plan_json_error(self):
        """Test generating a business plan with invalid JSON response."""
        service = self.OpenAIService()

        # Mock invalid JSON response
        raw_content = "Not a JSON object"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = raw_content

        self.mock_openai.ChatCompletion.create.return_value = mock_response

        plan = service.generate_business_plan(
            "Test Biz", "Tech", "A test business"
        )

        assert plan == {"raw_content": raw_content}

    def test_generate_business_plan_api_error(self):
        """Test API error handling."""
        service = self.OpenAIService()

        # Mock API error
        self.mock_openai.ChatCompletion.create.side_effect = Exception("API Error")

        with pytest.raises(self.MockHTTPException) as excinfo:
            service.generate_business_plan("Test Biz", "Tech", "Desc")

        assert excinfo.value.status_code == 500
        assert "API Error" in excinfo.value.detail

    def test_generate_marketing_copy(self):
        """Test generating marketing copy."""
        service = self.OpenAIService()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Buy now!"

        self.mock_openai.ChatCompletion.create.return_value = mock_response

        copy = service.generate_marketing_copy(
            "Test Biz", "Twitter", "Sales", "Everyone"
        )

        assert copy == "Buy now!"
        self.mock_openai.ChatCompletion.create.assert_called_once()

    def test_generate_email_campaign(self):
        """Test generating email campaign."""
        service = self.OpenAIService()

        expected_email = {
            "subject": "Hello",
            "body": "World",
            "cta": "Click"
        }

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(expected_email)

        self.mock_openai.ChatCompletion.create.return_value = mock_response

        email = service.generate_email_campaign(
            "Test Biz", "Sales", "Everyone", ["Point 1"]
        )

        assert email == expected_email

    def test_analyze_competitor(self):
        """Test competitor analysis."""
        service = self.OpenAIService()

        expected_analysis = {
            "strengths": ["Strong"],
            "weaknesses": ["Weak"]
        }

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(expected_analysis)

        self.mock_openai.ChatCompletion.create.return_value = mock_response

        analysis = service.analyze_competitor("Competitor X", "Tech")

        assert analysis == expected_analysis

    def test_factory_method(self):
        """Test IntegrationFactory creates OpenAIService."""
        service = self.IntegrationFactory.get_openai_service()
        assert isinstance(service, self.OpenAIService)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

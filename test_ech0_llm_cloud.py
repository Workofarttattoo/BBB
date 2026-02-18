import unittest
from unittest.mock import MagicMock, patch
import json
import urllib.request
from ech0_llm_engine import ECH0LLMEngine

class TestECH0LLMEngineCloud(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_huggingface_space_call(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"data": ["Hello from HF"]}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Initialize engine
        engine = ECH0LLMEngine(provider="huggingface", endpoint="https://test.hf.space/api/predict")

        # Call generate
        response = engine.generate_response("Hi")

        # Verify
        self.assertEqual(response, "Hello from HF")

        # Check request payload
        args, kwargs = mock_urlopen.call_args
        request_obj = args[0]
        self.assertEqual(request_obj.full_url, "https://test.hf.space/api/predict")
        self.assertEqual(request_obj.get_method(), "POST")

        payload = json.loads(request_obj.data.decode('utf-8'))
        self.assertIn("data", payload)
        self.assertIsInstance(payload["data"], list)

    @patch('urllib.request.urlopen')
    def test_together_ai_call(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "output": {
                "choices": [{"text": "Hello from Together"}]
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Initialize engine
        engine = ECH0LLMEngine(provider="together", endpoint="https://api.together.xyz/inference", api_key="test_key")

        # Call generate
        response = engine.generate_response("Hi")

        # Verify
        self.assertEqual(response, "Hello from Together")

        # Check headers
        args, kwargs = mock_urlopen.call_args
        request_obj = args[0]
        self.assertEqual(request_obj.get_header("Authorization"), "Bearer test_key")

    @patch('urllib.request.urlopen')
    def test_fallback_on_error(self, mock_urlopen):
        # Setup mock error
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")

        # Initialize engine
        engine = ECH0LLMEngine(provider="huggingface")

        # Call generate
        response = engine.generate_response("Hi")

        # Verify fallback
        self.assertIn("Automated Response", response)

if __name__ == '__main__':
    unittest.main()

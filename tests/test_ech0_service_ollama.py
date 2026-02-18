import unittest
import asyncio
import json
from unittest.mock import MagicMock, patch
from src.blank_business_builder.ech0_service import ECH0Service
import urllib.request

class TestECH0ServiceOllama(unittest.TestCase):

    def setUp(self):
        self.service = ECH0Service()

    @patch('urllib.request.urlopen')
    def test_call_ollama_success(self, mock_urlopen):
        # Mock the response object
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"response": "Hello from Echo"}'
        # Configure the mock to return this response
        mock_urlopen.return_value = mock_response

        # Run the async method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # We need to mock the run_in_executor call because it runs in a thread
        # causing issues with MagicMock in some environments, but let's try standard approach first.
        # Actually, since we mock urlopen, run_in_executor will call the mock.

        result = loop.run_until_complete(self.service.chat("Hello"))
        loop.close()

        self.assertEqual(result, "Hello from Echo")

        # Verify the request
        # mock_urlopen is called with a Request object
        self.assertTrue(mock_urlopen.called)
        args, _ = mock_urlopen.call_args
        request = args[0]

        self.assertIsInstance(request, urllib.request.Request)
        self.assertEqual(request.full_url, "http://localhost:11434/api/generate")
        self.assertEqual(request.get_method(), "POST")

        payload = json.loads(request.data.decode('utf-8'))
        self.assertEqual(payload['model'], 'echo')
        self.assertEqual(payload['prompt'], 'Hello')

    @patch('urllib.request.urlopen')
    def test_call_ollama_failure(self, mock_urlopen):
        # Simulate an error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.service.chat("Hello"))
        loop.close()

        # Should return error message
        self.assertIn("unable to connect", result)

if __name__ == '__main__':
    unittest.main()

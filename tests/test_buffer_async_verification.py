
import asyncio
import unittest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock dependencies before import
mock_requests = MagicMock()
mock_httpx = MagicMock()
mock_fastapi = MagicMock()
mock_fastapi.status = MagicMock()
mock_fastapi.HTTPException = Exception # Simple substitute for testing

sys.modules["requests"] = mock_requests
sys.modules["httpx"] = mock_httpx
sys.modules["fastapi"] = mock_fastapi
sys.modules["fastapi.status"] = mock_fastapi.status

# Now import the module
from blank_business_builder import integrations

class TestBufferServiceAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Ensure access token is set for non-simulation path
        os.environ["BUFFER_ACCESS_TOKEN"] = "test_token"
        self.service = integrations.BufferService()

        # Reset mocks
        mock_requests.reset_mock()
        mock_httpx.reset_mock()

        # Setup mock_httpx.AsyncClient
        self.mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value.__aenter__.return_value = self.mock_client

    async def test_get_profiles_async_httpx(self):
        """Test get_profiles uses httpx when available."""
        with patch("blank_business_builder.integrations.httpx", mock_httpx):
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": "p1"}]
            self.mock_client.get.return_value = mock_response

            profiles = await self.service.get_profiles()

            self.assertEqual(profiles, [{"id": "p1"}])
            self.mock_client.get.assert_called_once()
            mock_requests.get.assert_not_called()

    async def test_get_profiles_async_fallback(self):
        """Test get_profiles falls back to requests when httpx is missing."""
        with patch("blank_business_builder.integrations.httpx", None):
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": "p2"}]
            mock_requests.get.return_value = mock_response

            profiles = await self.service.get_profiles()

            self.assertEqual(profiles, [{"id": "p2"}])
            mock_requests.get.assert_called_once()
            self.mock_client.get.assert_not_called()

    async def test_create_post_direct_async_httpx(self):
        """Test create_post_direct uses httpx."""
        with patch("blank_business_builder.integrations.httpx", mock_httpx):
            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True}
            self.mock_client.post.return_value = mock_response

            result = await self.service.create_post_direct("p1", "test text")

            self.assertEqual(result, {"success": True})
            self.mock_client.post.assert_called_once()

    async def test_buffer_handler_is_async(self):
        """Test that _buffer_handler is async and works."""
        with patch("blank_business_builder.integrations.httpx", mock_httpx):
            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True}
            self.mock_client.post.return_value = mock_response

            await integrations._buffer_handler({"profile_id": "p1", "text": "hello"})

            self.mock_client.post.assert_called_once()

if __name__ == "__main__":
    unittest.main()

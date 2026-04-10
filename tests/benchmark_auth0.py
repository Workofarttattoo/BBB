import time
import os
import sys
import unittest.mock as mock
import asyncio
from jose import jwt as jose_jwt

# Add the src directory to the path so we can import blank_business_builder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.auth import Auth0Service

# Mock data
MOCK_DOMAIN = "test.auth0.com"
MOCK_AUDIENCE = "test-audience"
MOCK_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "test-kid",
            "use": "sig",
            "n": "test-n",
            "e": "AQAB"
        }
    ]
}
MOCK_PAYLOAD = {"sub": "user123"}
MOCK_TOKEN = "test.token.here"

def mock_get(*args, **kwargs):
    class MockResponse:
        def json(self):
            # Simulate network latency
            time.sleep(0.05)
            return MOCK_JWKS
        def raise_for_status(self):
            pass
    return MockResponse()

class MockAsyncResponse:
    def json(self):
        return MOCK_JWKS
    def raise_for_status(self):
        pass

async def mock_async_get(*args, **kwargs):
    # Simulate network latency
    await asyncio.sleep(0.05)
    return MockAsyncResponse()

def benchmark_baseline():
    service = Auth0Service()
    service.domain = MOCK_DOMAIN
    service.audience = MOCK_AUDIENCE
    service.enabled = True

    # Clear cache before benchmarking
    service.__class__._jwks_cache = None

    # Check if verify_auth0_token is async
    is_async = asyncio.iscoroutinefunction(service.verify_auth0_token)

    if not is_async:
        with mock.patch("requests.get", side_effect=mock_get):
            with mock.patch("jose.jwt.get_unverified_header", return_value={"kid": "test-kid"}):
                with mock.patch("jose.jwt.decode", return_value=MOCK_PAYLOAD):

                    start_time = time.time()
                    iterations = 100

                    for _ in range(iterations):
                        service.verify_auth0_token(MOCK_TOKEN)

                    end_time = time.time()

                    duration = end_time - start_time
                    print(f"Benchmark: {iterations} iterations took {duration:.4f} seconds")
                    print(f"Average time per call: {duration / iterations:.4f} seconds")
                    return duration
    else:
        # Create a mock for httpx.AsyncClient
        class MockClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def get(self, *args, **kwargs):
                return await mock_async_get(*args, **kwargs)

        async def run_async_benchmark():
            with mock.patch("httpx.AsyncClient", return_value=MockClient()):
                with mock.patch("jose.jwt.get_unverified_header", return_value={"kid": "test-kid"}):
                    with mock.patch("jose.jwt.decode", return_value=MOCK_PAYLOAD):

                        start_time = time.time()
                        iterations = 100

                        for _ in range(iterations):
                            await service.verify_auth0_token(MOCK_TOKEN)

                        end_time = time.time()

                        duration = end_time - start_time
                        print(f"Benchmark: {iterations} iterations took {duration:.6f} seconds")
                        print(f"Average time per call: {duration / iterations:.6f} seconds")
                        return duration

        return asyncio.run(run_async_benchmark())

if __name__ == "__main__":
    benchmark_baseline()

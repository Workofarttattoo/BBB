import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException, status
from blank_business_builder.cache import cache, rate_limit

@pytest.fixture
def mock_redis_client():
    with patch("blank_business_builder.cache.redis_client", new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.url.path = "/test-path"
    req.client.host = "127.0.0.1"
    # Ensure it passes the isinstance(request, Request) check in src/blank_business_builder/cache.py
    req.__class__ = Request
    return req

@pytest.mark.asyncio
async def test_cache_miss(mock_redis_client, mock_request):
    mock_redis_client.get.return_value = None

    @cache(expire=60)
    async def dummy_func(request: Request, param1: str):
        return {"result": param1}

    result = await dummy_func(request=mock_request, param1="value1")

    assert result == {"result": "value1"}
    mock_redis_client.get.assert_called_once()
    mock_redis_client.setex.assert_called_once()

    # Check setex arguments
    args, _ = mock_redis_client.setex.call_args
    assert args[1] == 60 # expire time
    assert json.loads(args[2]) == {"result": "value1"} # serialized value

@pytest.mark.asyncio
async def test_cache_hit(mock_redis_client, mock_request):
    cached_data = {"cached": "data"}
    mock_redis_client.get.return_value = json.dumps(cached_data)

    @cache(expire=60)
    async def dummy_func(request: Request):
        return {"result": "new_data"}

    result = await dummy_func(request=mock_request)

    assert result == cached_data
    mock_redis_client.get.assert_called_once()
    mock_redis_client.setex.assert_not_called()

@pytest.mark.asyncio
async def test_rate_limit_allowed(mock_redis_client, mock_request):
    mock_pipeline = MagicMock() # pipeline is synchronous object until executed
    # When redis_client.pipeline() is called, return mock_pipeline
    mock_redis_client.pipeline.return_value = mock_pipeline
    # Mock chain methods to return self
    mock_pipeline.incr.return_value = mock_pipeline
    mock_pipeline.ttl.return_value = mock_pipeline
    mock_pipeline.execute = AsyncMock(return_value=[1, -1]) # current_count=1, ttl=-1

    @rate_limit(limit=5, window=60)
    async def dummy_func(request: Request):
        return {"status": "ok"}

    result = await dummy_func(request=mock_request)

    assert result == {"status": "ok"}
    mock_redis_client.pipeline.assert_called_once()
    mock_pipeline.incr.assert_called_once()
    mock_pipeline.ttl.assert_called_once()
    mock_pipeline.execute.assert_called_once()
    mock_redis_client.expire.assert_called_once() # Called because ttl was -1

@pytest.mark.asyncio
async def test_rate_limit_exceeded(mock_redis_client, mock_request):
    mock_pipeline = MagicMock()
    mock_redis_client.pipeline.return_value = mock_pipeline
    mock_pipeline.incr.return_value = mock_pipeline
    mock_pipeline.ttl.return_value = mock_pipeline
    mock_pipeline.execute = AsyncMock(return_value=[6, 50]) # current_count=6 (> limit 5), ttl=50

    @rate_limit(limit=5, window=60)
    async def dummy_func(request: Request):
        return {"status": "ok"}

    with pytest.raises(HTTPException) as excinfo:
        await dummy_func(request=mock_request)

    assert excinfo.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    mock_redis_client.pipeline.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_no_request_object(mock_redis_client):
    @rate_limit(limit=5, window=60)
    async def dummy_func():
        return {"status": "ok"}

    result = await dummy_func()

    assert result == {"status": "ok"}
    # Redis shouldn't be called if there's no request object
    mock_redis_client.pipeline.assert_not_called()

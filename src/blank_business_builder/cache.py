import functools
import json
import logging
from typing import Callable, Any, Optional

import redis.asyncio as redis
from fastapi import Request, HTTPException, status

from blank_business_builder.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def cache(expire: int = 3600, key_prefix: str = ""):
    """
    Asynchronous cache decorator for FastAPI endpoints.
    Caches the JSON serialized response.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key based on function name
            cache_key_parts = [key_prefix or func.__name__]

            # Try to extract Request to use path as part of key
            request = kwargs.get("request") or next((arg for arg in args if isinstance(arg, Request)), None)

            if request:
                cache_key_parts.append(request.url.path)

            # Sort kwargs for deterministic keys (excluding non-serializable like Request)
            clean_kwargs = {k: v for k, v in kwargs.items() if k != "request" and not isinstance(v, Request)}
            if clean_kwargs:
                cache_key_parts.append(str(sorted(clean_kwargs.items())))

            cache_key = ":".join(cache_key_parts)

            try:
                cached_value = await redis_client.get(cache_key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception as e:
                logger.warning(f"Cache get error for key {cache_key}: {e}")

            # If not cached, execute the function
            result = await func(*args, **kwargs)

            try:
                # Serialize and store, using FastAPI's jsonable_encoder to handle Pydantic models
                from fastapi.encoders import jsonable_encoder
                serialized_result = json.dumps(jsonable_encoder(result))
                await redis_client.setex(cache_key, expire, serialized_result)
            except Exception as e:
                logger.warning(f"Cache set error for key {cache_key}: {e}")

            return result

        return wrapper
    return decorator


def rate_limit(limit: int, window: int = 60):
    """
    Rate limiting decorator for FastAPI endpoints using Redis.
    limit: Number of allowed requests.
    window: Time window in seconds.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the Request object to get client IP
            # Check if one of the kwargs contains Request (FastAPI does this by name sometimes)
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for v in kwargs.values():
                    # Handle both exact matches and mock objects in tests
                    if isinstance(v, Request) or (hasattr(v, 'client') and hasattr(v, 'url')):
                        request = v
                        break

            if not request:
                for arg in args:
                    # In tests we pass the MagicMock which has type MagicMock, not Request.
                    if isinstance(arg, Request) or (hasattr(arg, 'client') and hasattr(arg, 'url')):
                        request = arg
                        break

            if not request:
                # If no request object found, skip rate limiting or log warning
                logger.warning(f"Rate limiting skipped for {func.__name__}: No Request object found")
                return await func(*args, **kwargs)

            # Get client IP
            client_ip = request.client.host if request.client else "unknown_ip"

            # Key for rate limiting
            rate_key = f"rate_limit:{func.__name__}:{client_ip}"

            try:
                # Atomically increment and set expiry
                # For redis.asyncio, pipeline() is an async context manager or object,
                # but depending on mock setup it might be different.
                # Handling it generically so it works with the actual driver and tests.
                pipe = redis_client.pipeline()
                if hasattr(pipe, '__await__'):
                    pipe = await pipe
                pipe.incr(rate_key)
                pipe.ttl(rate_key)
                current_count, ttl = await pipe.execute()

                if current_count == 1 or ttl == -1:
                    # Set expiry on first request or if TTL was not set
                    await redis_client.expire(rate_key, window)

                if current_count > limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Rate limiting error for {rate_key}: {e}")
                # Failsafe: allow request if Redis fails

            return await func(*args, **kwargs)

        return wrapper
    return decorator

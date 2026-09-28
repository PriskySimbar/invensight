"""
Rate limiting middleware using Redis.
"""

import os
import time
from typing import Optional
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from redis_client import cache_service

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.getenv("RATE_LIMIT_MAX_REQUESTS", "10") + "/minute"],
)

# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Maximum {os.getenv('RATE_LIMIT_MAX_REQUESTS', '10')} requests per minute.",
            "retry_after": 60
        }
    )

# Rate limit checker
async def check_rate_limit(identifier: str, limit: int = 10, window: int = 60) -> bool:
    """
    Check if request is within rate limit using Redis.
    
    Args:
        identifier: Unique identifier (IP address or user ID)
        limit: Maximum requests allowed
        window: Time window in seconds
    
    Returns:
        True if request is allowed, False otherwise
    """
    if not cache_service.enabled:
        return True  # Allow if Redis is not available
    
    try:
        key = f"rate_limit:{identifier}"
        current = await cache_service.get(key)
        
        if current is None:
            # First request in window
            await cache_service.set(key, {"count": 1, "window_start": time.time()}, window)
            return True
        
        # Check if window has expired
        if time.time() - current["window_start"] > window:
            # Reset for new window
            await cache_service.set(key, {"count": 1, "window_start": time.time()}, window)
            return True
        
        # Check if limit exceeded
        if current["count"] >= limit:
            return False
        
        # Increment counter
        current["count"] += 1
        await cache_service.set(key, current, window)
        return True
        
    except Exception as e:
        print(f"Rate limit check error: {e}")
        return True  # Allow request on error

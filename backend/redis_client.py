"""
Redis client for caching and rate limiting.
"""

import os
import json
from typing import Optional, Any
import redis
from dotenv import load_dotenv

load_dotenv()

def get_redis_client() -> redis.Redis:
    """
    Get Redis client connection.
    
    Update REDIS_URL in .env with your actual Redis Cloud host.
    Format: redis://default:your-token@your-host:6379
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # For now, disable Redis for local development
    # Uncomment when Redis is available
    return None
    
    try:
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        # Test connection
        client.ping()
        print("Redis connection successful")
        return client
    except Exception as e:
        print(f"Redis connection failed: {str(e)}")
        print("Falling back to in-memory cache")
        return None

class CacheService:
    """Cache service using Redis."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.enabled = self.redis_client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

# Global cache service instance
cache_service = CacheService()

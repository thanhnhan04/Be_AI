import redis.asyncio as redis
from config import settings


class RedisCache:
    """Redis connection manager"""
    
    client: redis.Redis = None


redis_cache = RedisCache()


async def connect_to_redis():
    """Connect to Redis cache"""
    try:
        redis_cache.client = await redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await redis_cache.client.ping()
        print(f"✓ Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        print(f"✗ Could not connect to Redis: {e}")
        # Redis is optional, don't raise error
        redis_cache.client = None


async def close_redis_connection():
    """Close Redis connection"""
    if redis_cache.client:
        await redis_cache.client.close()
        print("✓ Closed Redis connection")


def get_redis():
    """Get Redis client instance"""
    return redis_cache.client

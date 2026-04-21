import json
import redis.asyncio as aioredis
from app.config import settings

_client = None

async def get_redis():
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def set_cache(key: str, value: dict, ttl_seconds: int = 86400):
    """Store dict as JSON. Default TTL 24h."""
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl_seconds)


async def get_cache(key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def delete_cache(key: str):
    r = await get_redis()
    await r.delete(key)
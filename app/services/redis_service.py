import redis.asyncio as aioredis
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

#single shared async redis client instance for the application
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL_SECONDS = 30 #Cache exprires after 30 seconds to ensure we don't serve stale data for too long

def _cache_key(category: str, judge: str, metric: str) -> str:
    return f"leaderboard:{category}:{judge}:{metric}"

async def get_cached_leaderboard(category, judge, metric) -> list | None:
    try:
        cached = await redis_client.get(_cache_key(category, judge, metric))
        if cached:
            print("> Cache hit - serving leaderboard from redis")
            return json.loads(cached)
        print("Cache miss - querying InfluxDB for latest leaderboard")
        return None
    except Exception as e:
        print(f"Error accessing Redis cache: {e}")
        return None
    
async def set_cached_leaderboard(results, category, judge, metric):
    try:
        await redis_client.setex(   #stores value with an expiry
            _cache_key(category, judge, metric),
            CACHE_TTL_SECONDS,
            json.dumps(results)
        )
        print("> Updated leaderboard cache in redis")
    except Exception as e:
        print(f"Error setting Redis cache: {e}")

async def invalidate_cache(category, judge):
    try:
        pattern = f"leaderboard:{category}:{judge}:*"
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        print(f"error, not invalidated")
    
async def publish_benchmark(data: dict):
    try:
        await redis_client.publish("benchmarks", json.dumps(data))
        print("> Published benchmark update to Redis channel")
    except Exception as e:
        print(f"Error publishing to Redis channel: {e}")

async def get_pubsub():
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("benchmarks")
        print("> Subscribed to Redis channel for benchmark updates")
        return pubsub
    except Exception as e:
        print(f"Error subscribing to Redis channel: {e}")
        return None
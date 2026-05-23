import redis.asyncio as aioredis
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

#single shared async redis client instance for the application
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

LEADERBOARD_CACHE_KEY = "leaderboard:latest"
CACHE_TTL_SECONDS = 30 #Cache exprires after 30 seconds to ensure we don't serve stale data for too long

async def get_cached_leaderboard() -> list | None:
    try:
        cached = await redis_client.get(LEADERBOARD_CACHE_KEY)
        if cached:
            print("> Cache hit - serving leaderboard from redis")
            return json.loads(cached)
        print("Cache miss - querying InfluxDB for latest leaderboard")
        return None
    except Exception as e:
        print(f"Error accessing Redis cache: {e}")
        return None
    
async def set_cached_leaderboard(leaderboard: list):
    try:
        await redis_client.setex(   #stores value with an expiry
            LEADERBOARD_CACHE_KEY,
            CACHE_TTL_SECONDS,
            json.dumps(leaderboard)
        )
        print("> Updated leaderboard cache in redis")
    except Exception as e:
        print(f"Error setting Redis cache: {e}")

async def invalidate_cache():
    try:
        await redis_client.delete(LEADERBOARD_CACHE_KEY)
        print("> Invalidated leaderboard cache in redis")
    except Exception as e:
        print(f"Error invalidating Redis cache: {e}")
    
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
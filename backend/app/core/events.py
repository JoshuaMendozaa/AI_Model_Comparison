import redis.asyncio as redis
import json
from typing import Dict, Any
from datetime import datetime
from app.config import settings

class EventPublisher:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = await redis.from_url(settings.REDIS_URL)

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    async def publish_event(self, channel: str, event_type: str, data: Dict[str, Any]):
        if not self.redis_client:
            await self.connect()

        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        await self.redis_client.publish(channel, json.dumps(message))

    async def publish_benchmark_update(self, model_id: int, bench_data: Dict[str, Any]):
        await self.publish_event("benchmarks", "benchmark_update", {
            "model_id": model_id,
            **bench_data
        })

    async def publish_battle_result(self, battle_data: Dict[str, Any]):
        await self.publish_event("battles", "battle_result", battle_data)

    async def publish_model_added(self, model_data: Dict[str, Any]):
        await self.publish_event("models", "model_added", model_data)


event_publisher = EventPublisher()
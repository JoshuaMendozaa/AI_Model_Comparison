# backend/app/services/benchmark_service.py
from typing import Any, Dict

class BenchmarkService:
    def __init__(self, influx_url: str | None = None, org: str | None = None, bucket: str | None = None, token: str | None = None):
        self.influx_url = influx_url
        self.org = org
        self.bucket = bucket
        self.token = token

    async def submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: wire InfluxDB write here. For now just echo back.
        return {"status": "accepted", "echo": payload}

    async def list(self, model_id: str | None = None) -> list[Dict[str, Any]]:
        # TODO: query Postgres/Influx. For now return empty.
        return []

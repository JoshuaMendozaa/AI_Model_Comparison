from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.influx import write_benchmark, query_benchmarks, query_latest_scores
from app.services.websocket_manager import manager
from app.services.redis_service import publish_benchmark, set_cached_leaderboard, invalidate_cache, get_cached_leaderboard

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

# Valid metrics models can submit
VALID_METRICS = {"accuracy", "latency_ms", "tokens_per_second", "memory_mb"}

# This file defines the API endpoints for submitting and retrieving benchmark data for AI models.

#write to InfluxDB when a new benchmark score is submitted, and then broadcast the update to all connected WebSocket clients so they can see real-time changes in the leaderboard. The get_leaderboard endpoint retrieves the latest leaderboard data, and the get_benchmarks endpoint allows clients to query historical benchmark data for a specific model and metric over a specified time range. The code also includes validation to ensure that only valid metrics are accepted and that benchmark values are positive.
class BenchmarkSubmit(BaseModel):
    model_name: str
    metric: str
    value: float

@router.post("/", response_model=dict)  #why dict? because we are returning a custom response instead of a single model, and we want to include additional fields like status and message
async def submit_benchmark(benchmark: BenchmarkSubmit):
    if benchmark.metric not in VALID_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Must be one of: {VALID_METRICS}"
        )
    if benchmark.value < 0:
        raise HTTPException(status_code=400, detail="Value must be positive")

    write_benchmark(
        model_name=benchmark.model_name,
        metric=benchmark.metric,
        value=benchmark.value
    )


    await invalidate_cache()  #invalidate the cached leaderboard in Redis whenever a new benchmark is submitted, so that the get_leaderboard endpoint will know to fetch fresh data from InfluxDB the next time it's called


    leaderboard = query_latest_scores()
    await set_cached_leaderboard(leaderboard)  #update the cached leaderboard in Redis whenever a new benchmark is submitted, so that the get_leaderboard endpoint can return the latest data without having to query InfluxDB every time

    # Debug — confirm broadcast is firing
    print(f"Broadcasting to {len(manager.active_connections)} clients")

    #Broadcast update to all connected WebSocket clients - this is done in the write_benchmark function after writing to InfluxDB, so that clients get real-time updates whenever a new benchmark score is submitted.
    broadcast_data = {
        "type": "benchmark_update",
        "model_name": benchmark.model_name,
        "metric": benchmark.metric,
        "value": benchmark.value,
        "leaderboard": query_latest_scores()  #include the latest leaderboard data in the broadcast so clients can update their displays immediately
    }

    await publish_benchmark(broadcast_data)

    print("> Published benchmark update to WebSocket clients")
    await manager.broadcast(broadcast_data)

    return {
        "status": "recorded",
        "model_name": benchmark.model_name,
        "metric": benchmark.metric,
        "value": benchmark.value
    }

@router.get("/leaderboard/latest")
async def get_leaderboard():
    #try cache first
    cached = await get_cached_leaderboard()
    if cached:
        return {"leaderboard": cached, "source": "cache"}
    
    #cache miss, query InfluxDB
    results = query_latest_scores()
    await set_cached_leaderboard(results)  #update cache with fresh data from InfluxDB
    return {"leaderboard": results, "source": "influxdb"}

@router.get("/{model_name}/{metric}")
async def get_benchmarks(model_name: str, metric: str, hours: int = 1):
    if metric not in VALID_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Must be one of: {VALID_METRICS}"
        )
    results = query_benchmarks(model_name, metric, hours)
    return {"model_name": model_name, "metric": metric, "data": results}
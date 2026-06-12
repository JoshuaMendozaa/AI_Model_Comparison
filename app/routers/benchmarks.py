from fastapi import APIRouter, HTTPException
from app.services.influx import query_benchmarks, query_latest_scores
from app.services.redis_service import set_cached_leaderboard, get_cached_leaderboard

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

# Valid metrics models can submit
VALID_METRICS = {"accuracy", "latency_ms", "tokens_per_second", "memory_mb"}

# This file defines the API endpoints for submitting and retrieving benchmark data for AI models.

@router.get("/leaderboard/latest")
async def get_leaderboard(category: str, judge: str, metric: str = "accuracy"):
    #try cache first
    cached = await get_cached_leaderboard(category, judge, metric)
    if cached:
        return {"leaderboard": cached, "source": "cache"}
    
    #cache miss, query InfluxDB
    results = query_latest_scores(category, judge, metric)
    await set_cached_leaderboard(results, category, judge, metric)  #update cache with fresh data from InfluxDB
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
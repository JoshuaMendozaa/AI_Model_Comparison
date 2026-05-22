from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.influx import write_benchmark, query_benchmarks, query_latest_scores
from app.services.websocket_manager import manager

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

# Valid metrics models can submit
VALID_METRICS = {"accuracy", "latency_ms", "tokens_per_second", "memory_mb"}

# This file defines the API endpoints for submitting and retrieving benchmark data for AI models.
class BenchmarkSubmit(BaseModel):
    model_name: str
    metric: str
    value: float

class BenchmarkResponse(BaseModel):
    model_name: str
    metric: str
    value: float
    time: str

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

    #Broadcast update to all connected WebSocket clients - this is done in the write_benchmark function after writing to InfluxDB, so that clients get real-time updates whenever a new benchmark score is submitted.
    await manager.broadcast({
        "type": "benchmark_update",
        "model_name": benchmark.model_name,
        "metric": benchmark.metric,
        "value": benchmark.value,
        "leaderboard": query_latest_scores()  #include the latest leaderboard data in the broadcast so clients can update their displays immediately
    })

    return {
        "status": "recorded",
        "model_name": benchmark.model_name,
        "metric": benchmark.metric,
        "value": benchmark.value
    }

@router.get("/{model_name}/{metric}")
async def get_benchmarks(model_name: str, metric: str, hours: int = 1):
    if metric not in VALID_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Must be one of: {VALID_METRICS}"
        )
    results = query_benchmarks(model_name, metric, hours)
    return {"model_name": model_name, "metric": metric, "data": results}

@router.get("/leaderboard/latest")
async def get_leaderboard():
    results = query_latest_scores()
    return {"leaderboard": results}
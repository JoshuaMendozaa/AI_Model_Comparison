from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import random
from pathlib import Path
from app.services.providers.ollama_provider import run_model
from app.services.judge import judge_response
from app.services.influx import write_benchmark
from app.services.websocket_manager import manager
from app.services.redis_service import invalidate_cache, set_cached_leaderboard
from app.services.influx import query_latest_scores

router = APIRouter(prefix="/battle", tags=["battle"])

VALID_CATEGORIES = ["reasoning", "coding", "knowledge", "creative"]

#Load prompts from start up
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "prompts.json"
with open(PROMPT_PATH) as f:
    PROMPT_LIBRARY = json.load(f)   #what does json.load do? it reads the json file and converts it into a python dictionary or list, depending on the structure of the json data. In this case, it likely creates a dictionary where each key is a category and the value is a list of prompts for that category.

class BattleRequest(BaseModel):
    category: str
    models: Optional[list[str]] = None
    prompt: Optional[str] = None    #if prompt is provided, use it. Otherwise, select random prompt from category
    judge: str

class BattleResponse(BaseModel):
    battle_id: str
    category: str
    prompt: str
    results: list[dict]   #list of model results with scores and metrics
    winner: str

@router.get("/models/available")
async def get_available_models():
    # Implementation for fetching available models
    import ollama
    import os
    try:
        client = ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"))
        models = client.list()  #fetch the list of available models from ollama
        return {
            "models": [m["name"] for m in models["models"]],   #return the names of the models in a list
            "judge": os.getenv("JUDGE_MODEL", "deepseek-r1")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")
    
@router.post("/start")
async def start_battle(request: BattleRequest):
    if request.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {VALID_CATEGORIES}")
    
    if not request.models or len(request.models) < 2:   #we need at least 2 models to have a battle, otherwise it's not really a battle. If the client doesn't provide a list of models, or if they provide a list with less than 2 models, we raise a 400 Bad Request error with a message indicating that at least 2 models must be provided for a battle.
        raise HTTPException(status_code=400, detail="At least 2 models must be provided for a battle.")
    
    if request.judge in request.models:
        raise HTTPException(status_code=400, detail="Judge cannot be in models due to bias")
    
    prompt = request.prompt or random.choice(PROMPT_LIBRARY[request.category])   #if the client doesn't provide a prompt, we select a random prompt from the PROMPT_LIBRARY based on the requested category. This ensures that we always have a valid prompt to use for the battle, even if the client doesn't specify one.

    print(f"Starting battle with prompt: {prompt} for models: {request.models}")

    await manager.broadcast({
        "type": "battle_start",
        "category": request.category,
        "models": request.models,
        "prompt": prompt,
        "judge": request.judge,
    })

    # Run models and judge asynchronously
    print("> Running models...")
    model_tasks = [run_model(model, prompt) for model in request.models]    #create list of asynchronous tasks to run each model with the given prompt.
    battle_results = await asyncio.gather(*model_tasks) #run_model is an asynchronous function that takes a model name and a prompt, runs the model with the prompt, and returns the result. By using asyncio.gather, we can run all the models concurrently and wait for all of them to finish before proceeding to the judging step.
    #battle_results will be a list of results corresponding to each model, in the same order as the request.models list. Each result should contain the model's response to the prompt, and possibly other metadata like latency or token usage.

    print("> Judging results...")
    results = []
    for result in battle_results:
        if result.error:
            print(f"Error running model: {result.error}")
            continue
        else:
            print(f"Model response: {result.model_name}...")
            scores = judge_response(prompt, result.response, request.judge)

        if not result.error:
            write_benchmark(result.model_name, "accuracy", scores["overall"], category=request.category, judge=request.judge)  #write the overall accuracy to InfluxDB for benchmarking purposes, so we can track how each model performs over time and see trends in their performance.
            write_benchmark(result.model_name, "latency_ms", result.latency_ms, category=request.category, judge=request.judge)  #also write latency as a benchmark metric, since it's an important aspect of model performance that we want to track and compare across models.
            write_benchmark(result.model_name, "tokens_per_second", result.tokens_per_second, category=request.category, judge=request.judge)  #also write tokens per second as a benchmark metric, since it's another important aspect of model performance that we want to track and compare across models.)
            
        results.append({
            "model": result.model_name,
            "response": result.response,
            "latency_ms": result.latency_ms,
            "tokens_per_second": result.tokens_per_second,
            "scores": scores,
            "error": result.error
        })

    # Determine winner based on overall score
    valid_results = [r for r in results if not r["error"]]
    winner = max(valid_results, key=lambda r: r["scores"]["overall"])["model"] if valid_results else "No valid responses"

    #update leaderboard cache in Redis
    await invalidate_cache(request.category, request.judge)
    leaderboard = query_latest_scores(request.category, request.judge)
    await set_cached_leaderboard(leaderboard, request.category, request.judge, "accuracy")

    #broadcast results to WebSocket clients
    await manager.broadcast({
        "type": "battle_results",
        "category": request.category,
        "prompt": prompt,
        "results": results,
        "winner": winner,
        "leaderboard": leaderboard
    })
       
    print(f"Battle complete! Winner: {winner}")

    import uuid
    return {
        "battle_id": str(uuid.uuid4()),  #generate a unique ID for this battle, which can be used for tracking and referencing the battle in the future if needed.
        "category": request.category,
        "prompt": prompt,
        "results": results,
        "winner": winner
    }

@router.get("/prompts/{category}")
async def get_prompts(category: str):
    "preview available prompts for a category"
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Must be one of {VALID_CATEGORIES}"
        )
    return {
        "category": category,
        "prompts": PROMPT_LIBRARY[category]
    }

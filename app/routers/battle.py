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

VALID_CATEGORIES = ["reasoning", "coding", "math", "creative"]

#Load prompts from start up
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "prompts.json"
with open(PROMPT_PATH) as f:
    PROMPT_LIBRARY = json.load(f)   #what does json.load do? it reads the json file and converts it into a python dictionary or list, depending on the structure of the json data. In this case, it likely creates a dictionary where each key is a category and the value is a list of prompts for that category.

class BattleRequest(BaseModel):
    category: str
    models: Optional[list[str]] = None
    prompt: Optional[str] = None    #if prompt is provided, use it. Otherwise, select random prompt from category

class BattleResponse(BaseModel):
    hattle_id: str
    category: str
    prompt: str
    results: list[dict]   #list of model results with scores and metrics
    winner: str

@router.get("/models/available")
async def get_available_models():
    # Implementation for fetching available models
    import ollama
    try:
        models = ollama.list()  #fetch the list of available models from ollama
        return {
            "models": [m["name"] for m in models["models"]],   #return the names of the models in a list
            "judge": "deepseek"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")
    
@router.post("/start")
async def start_battle(request: BattleRequest):
    if request.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {VALID_CATEGORIES}")
    
    if len(request.models) < 2:
        raise HTTPException(status_code=400, detail="At least 2 models must be provided for a battle.")
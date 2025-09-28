from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api import SYNCHRONOUS
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.events import event_publisher
from app.models.database import User, AIModel, Benchmark, Battle
from app.models.schemas import (
    BenchmarkCreate, BenchmarkResponse,
    BattleCreate, BattleResponse
)
from app.services.benchmark_service import BenchmarkService
from app.services.battle_engine import BattleEngine
from app.config import settings

router = APIRouter()

@router.post("/submit", response_model=BenchmarkResponse)
async def submit_benchmark(
    benchmark_data: BenchmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model exists and user owns it
    result = await db.execute(
        select(AIModel).where(AIModel.id == benchmark_data.model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if model.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to submit benchmarks for this model"
        )
    
    # Save to PostgreSQL
    db_benchmark = Benchmark(**benchmark_data.dict())
    db.add(db_benchmark)
    await db.commit()
    await db.refresh(db_benchmark)
    
    # Save to InfluxDB for time-series data
    benchmark_service = BenchmarkService()
    await benchmark_service.save_to_influxdb(db_benchmark, model.name)
    
    # Publish event
    await event_publisher.publish_benchmark_update(
        model_id=model.id,
        benchmark_data={
            "benchmark_id": db_benchmark.id,
            "test_name": db_benchmark.test_name,
            "accuracy": db_benchmark.accuracy,
            "speed_ms": db_benchmark.speed_ms,
            "model_name": model.name
        }
    )
    
    return db_benchmark

@router.get("/model/{model_id}", response_model=List[BenchmarkResponse])
async def get_model_benchmarks(
    model_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Benchmark)
        .where(Benchmark.model_id == model_id)
        .order_by(desc(Benchmark.created_at))
        .limit(limit)
    )
    return result.scalars().all()

@router.post("/battle", response_model=BattleResponse)
async def create_battle(
    battle_data: BattleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get both models
    model1_result = await db.execute(
        select(AIModel).where(AIModel.id == battle_data.model1_id)
    )
    model1 = model1_result.scalar_one_or_none()
    
    model2_result = await db.execute(
        select(AIModel).where(AIModel.id == battle_data.model2_id)
    )
    model2 = model2_result.scalar_one_or_none()
    
    if not model1 or not model2:
        raise HTTPException(status_code=404, detail="One or both models not found")
    
    # Get latest benchmarks for both models
    bench1_result = await db.execute(
        select(Benchmark)
        .where(Benchmark.model_id == model1.id)
        .order_by(desc(Benchmark.created_at))
        .limit(1)
    )
    bench1 = bench1_result.scalar_one_or_none()
    
    bench2_result = await db.execute(
        select(Benchmark)
        .where(Benchmark.model_id == model2.id)
        .order_by(desc(Benchmark.created_at))
        .limit(1)
    )
    bench2 = bench2_result.scalar_one_or_none()
    
    if not bench1 or not bench2:
        raise HTTPException(
            status_code=400,
            detail="Both models need at least one benchmark to battle"
        )
    
    # Run battle
    battle_engine = BattleEngine()
    battle_results = battle_engine.run_battle(
        model1, bench1, model2, bench2, battle_data.battle_type
    )
    
    # Save battle
    db_battle = Battle(
        model1_id=model1.id,
        model2_id=model2.id,
        winner_id=battle_results["winner_id"],
        battle_type=battle_data.battle_type,
        battle_config=battle_data.battle_config,
        results=battle_results
    )
    db.add(db_battle)
    await db.commit()
    await db.refresh(db_battle)
    
    # Publish event
    await event_publisher.publish_battle_result({
        "battle_id": db_battle.id,
        "model1": {"id": model1.id, "name": model1.name},
        "model2": {"id": model2.id, "name": model2.name},
        "winner_id": battle_results["winner_id"],
        "battle_type": battle_data.battle_type,
        "scores": battle_results["scores"]
    })
    
    return db_battle

@router.get("/battles/recent", response_model=List[BattleResponse])
async def get_recent_battles(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Battle)
        .order_by(desc(Battle.created_at))
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/leaderboard")
async def get_leaderboard(
    battle_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # Complex query to get win rates
    query = """
    WITH battle_stats AS (
        SELECT 
            m.id,
            m.name,
            m.version,
            COUNT(DISTINCT b.id) as total_battles,
            COUNT(DISTINCT CASE WHEN b.winner_id = m.id THEN b.id END) as wins
        FROM ai_models m
        LEFT JOIN battles b ON (m.id = b.model1_id OR m.id = b.model2_id)
        WHERE m.is_active = true
        GROUP BY m.id, m.name, m.version
    )
    SELECT 
        id,
        name,
        version,
        total_battles,
        wins,
        CASE 
            WHEN total_battles > 0 THEN ROUND(wins::numeric / total_battles * 100, 2)
            ELSE 0
        END as win_rate
    FROM battle_stats
    WHERE total_battles > 0
    ORDER BY win_rate DESC, total_battles DESC
    LIMIT :limit
    """
    
    result = await db.execute(text(query), {"limit": limit})
    leaderboard = []
    for row in result:
        leaderboard.append({
            "model_id": row[0],
            "name": row[1],
            "version": row[2],
            "total_battles": row[3],
            "wins": row[4],
            "win_rate": float(row[5])
        })
    
    return leaderboard
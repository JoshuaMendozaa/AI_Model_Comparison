from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from app.services.influx import query_latest_scores
from app.services.redis_service import get_cached_leaderboard, get_pubsub
import json
import asyncio

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/leaderboard")
async def leaderboard_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        # Send current leaderboard on connect — try cache first
        try:
            leaderboard = await get_cached_leaderboard() or query_latest_scores()
            await websocket.send_text(json.dumps({
                "type": "init",
                "leaderboard": leaderboard
            }))
        except Exception as e:
            print(f"⚠️ Could not fetch initial leaderboard: {e}")
            await websocket.send_text(json.dumps({
                "type": "init",
                "leaderboard": []
            }))

        # Keep connection alive, listen for pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
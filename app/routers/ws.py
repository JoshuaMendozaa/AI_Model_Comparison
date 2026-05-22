from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from app.services.influx import query_latest_scores

router = APIRouter(tags=["WebSocket"]) #This file defines a WebSocket endpoint for real-time leaderboard updates. Clients can connect to this endpoint to receive live updates whenever new benchmark scores are submitted. The endpoint listens for WebSocket connections at /ws/leaderboard and uses the ConnectionManager to manage active connections and broadcast messages to all connected clients. Whenever a new benchmark score is recorded, the latest leaderboard data is queried from InfluxDB and broadcasted to all clients, allowing them to see real-time changes in the leaderboard as new scores come in.

@router.websocket("/ws/leaderboard")
async def leaderboard_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        #send current leaderboard immediately upon connection
        current_scores = query_latest_scores()
        await websocket.send_text(
            __import__('json').dumps({
                "type": "init",
                "leaderboard": current_scores
            })
        )

        # Keep connection open to listen for incoming messages (if needed in the future)
        while True:
            data = await websocket.receive_text()
            #Client can send "ping" to check connection health, or we can implement other interactions in the future
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

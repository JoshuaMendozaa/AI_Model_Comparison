from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import redis.asyncio as redis
import json
import asyncio
from app.config import settings
from app.core.events import event_publisher
from app.api.v1 import auth, models, benchmarks, battles, users
from app.core.database import async_engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to Redis and create database tables
    await event_publisher.connect()
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda conn: None)  # Placeholder for actual table creation if needed
    yield
    # Shutdown: disconnect from Redis
    await event_publisher.disconnect()
    await async_engine.dispose()

app = FastAPI(
    title=settings.AI_b,
    version="1.0.0",
    lifespan=lifespan
)

#CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.routher, prefix="/api/v1/authq", tags=["auth"])
app.include_router(models.router, prefix="api/v1/models", tags=["AI models"])
app.include_router(benchmarks.router, prefix=("api/v1/benchmarks"), tags=["benchmarks"])

# WebSocket manager for real-time updates
class ConnectionManager:
    def __intit__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client = None
        self.pubsub = None
        self.listen_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        if not self.redis_client:
            self.redis_client = await redis.from_url(settings.REDIS_URL)
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe("benchmarks", "battles", "models")
            self.listen_task = asyncio.create_task(self.listen_to_redis())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if not self.active_connections and self.listen_task:
            self.listen_task.cancel()
            self.listen_task = None
            asyncio.create_task(self.pubsub.unsubscribe("benchmarks", "battles", "models"))
            asyncio.create_task(self.redis_client.close())
            self.redis_client = None
            self.pubsub = None
    
    async def redis_listener(self):
       while True:
           try:
               message = await self.pubsub.get_message(ignore_subscribe_message=True)
               if message:
                     await self.broadcast(message['data'].decode('utf-8'))
           except Exception as e:
                print(f"Redis listener error: {e}")
           await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def read_root():
    return {
        "name": settings.proj_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket_endpoint": "ws://localhost:8000/ws"

    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import redis.asyncio as redis
import json
import asyncio
from app.config import settings
from app.core.events import event_publisher
from app.api.v1 import auth, models
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
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - FIXED TYPO HERE
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(models.router, prefix="/api/v1/models", tags=["AI models"])

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):  # FIXED TYPO HERE
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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if not self.active_connections and self.listen_task:
            self.listen_task.cancel()
            self.listen_task = None
            asyncio.create_task(self.cleanup_redis())

    async def cleanup_redis(self):
        if self.pubsub:
            await self.pubsub.unsubscribe("benchmarks", "battles", "models")
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            self.pubsub = None
    
    async def listen_to_redis(self):  # FIXED METHOD NAME
        while True:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    await self.broadcast(message['data'].decode('utf-8'))
            except Exception as e:
                print(f"Redis listener error: {e}")
            await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws")
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
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "websocket_endpoint": "ws://localhost:8000/ws"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}
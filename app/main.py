import asyncio
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import models
from app.routers import benchmarks
from app.routers import ws
from app.routers import battle
from app.services.influx import client, write_api, query_api
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(  #This initializes a FastAPI app instance with metadata such as title, description, and version. This information is used in the automatically generated API documentation (Swagger UI) and helps users understand the purpose and version of the API.
    title="AI Model Battle",
    description="Real-time AI benchmark battle system",
    version="1.2.0"
)

#allows the frontend to call this api from a differenct origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    #any origin allowed(for dev atm)
    allow_credentials=True,
    allow_methods=["*"],    #allows GET, POST, etc
    allow_headers=["*"]     #allows Content-Type: app/json 
)

@app.on_event("startup")    #This decorator registers the startup function to be called when the FastAPI app starts up. The startup function is responsible for establishing a connection to the database and creating the necessary tables if they don't already exist. It includes a retry mechanism to handle potential connection issues gracefully, ensuring that the application can start successfully even if the database is temporarily unavailable.
async def startup():
    retries = 5
    for i in range(retries):
        try:
            async with engine.begin() as conn:  #This creates an asynchronous connection to the database using the engine defined in the database module.
                await conn.run_sync(Base.metadata.create_all)  #This creates all tables defined via SQLAlchemy if they don't exist yet. This ensure that the database schema is set up correctly before the application starts handling requests.
            print("Database connected and tables created successfully.")
            break
        except Exception as e:
            print(f"Database connection failed, retrying in 5 seconds... ({i+1}/{retries})")
            await asyncio.sleep(2)
    # Creates all tables defined via SQLAlchemy if they don't exist yet. This ensure that the database schema is set up correctly before the application starts handling requests.

app.include_router(models.router)   # this line includes the router defined in the models module, which contains the API endpoints related to managing AI models.
app.include_router(benchmarks.router)   # this lines includes the router defined in the benchmarks module, which contains the API endpoints related to managing benchmarks and benchmark results.
app.include_router(ws.router)   # this line includes the router defined in the ws.module, which contains the API endpoints related to managing websocket connections and broadcasting messages to clients.
app.include_router(battle.router)

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "AI Battle API is running"}
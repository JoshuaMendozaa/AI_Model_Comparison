import asyncio
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import models
from app.routers import benchmarks
from app.services.influx import client, write_api, query_api

app = FastAPI(
    title="AI Model Battle",
    description="Real-time AI benchmark battle system",
    version="1.0.0"
)

@app.on_event("startup")    #This event is triggered when the application starts up.
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

app.include_router(models.router)
app.include_router(benchmarks.router)

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "AI Battle API is running"}
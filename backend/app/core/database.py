import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Read the variables by NAME
SYNC_DATABASE_URL  = os.getenv("SYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

# Derive async URL from sync if not provided
if not ASYNC_DATABASE_URL and SYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("+psycopg2", "+asyncpg")

if not SYNC_DATABASE_URL:
    raise RuntimeError("Missing DB URL: set SYNC_DATABASE_URL or DATABASE_URL")

# For Alembic / any sync ops
sync_engine = create_engine(SYNC_DATABASE_URL, future=True)

# For app runtime (FastAPI deps)
async_engine = create_async_engine(ASYNC_DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

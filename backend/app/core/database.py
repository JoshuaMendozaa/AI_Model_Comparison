import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use settings from config
SYNC_DATABASE_URL = settings.SYNC_DATABASE_URL or settings.DATABASE_URL
ASYNC_DATABASE_URL = settings.ASYNC_DATABASE_URL

# Derive async URL from sync if not provided
if not ASYNC_DATABASE_URL and SYNC_DATABASE_URL:
    if "+psycopg2" in SYNC_DATABASE_URL:
        ASYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("+psycopg2", "+asyncpg")
    elif "postgresql://" in SYNC_DATABASE_URL:
        ASYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        ASYNC_DATABASE_URL = SYNC_DATABASE_URL

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
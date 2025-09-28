from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

#Async engine for FASTAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
)

AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

#Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL or settings.DATABASE_URL.replace("asyncpg", ""),
    echo=settings.DEBUG,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


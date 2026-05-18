# database.py used to set up the database connection and session management for the 
# application using SQLAlchemy with async support. It defines the database URL, 
# creates an asynchronous engine, and provides a session factory for managing 
# database sessions in FastAPI endpoints. The Base class is defined for use in 
# model definitions, and a dependency function is provided to yield a database 
# session for each request.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Database configuration using environment variables for security and flexibility
DATABASE_URL = (
    f"postgresql+asyncpg://"    # Construct the database URL using the asyncpg driver for PostgreSQL, with credentials and database name from environment variables
    f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@postgres:5432/{os.getenv('POSTGRES_DB')}"
)

# The engine is the actual connection to Postgres
engine = create_async_engine(DATABASE_URL, echo=True)   # Create an asynchronous engine for connecting to the PostgreSQL database, with echo enabled for logging SQL statements

# SessionLocal is a factory that creates database sessions
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Base class that all our table models will inherit from
class Base(DeclarativeBase):
    pass

# Dependency — FastAPI will call this to get a DB session per request
async def get_db():
    async with SessionLocal() as session:
        yield session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os 


DATABASE_URL = (    #Construct the database URL using environment variables for the PostgreSQL connection param.
    f"postgresql+asyncpg://"    
    f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@postgres:5432/{os.getenv('POSTGRES_DB')}"
)

# The engine is the actual connection to Postgres
engine = create_async_engine(DATABASE_URL, echo=True)   # Create an asynchronous engine for connecting to the PostgreSQL database, with echo enabled for logging SQL statements

#1 create the shopping cart FACTORY (blueprint for creating sessions)
# sessions are the actual shopping carts that we use to interact with the database.
# they are created from the factory, and we can have multiple sessions (shopping carts) active at the same time, 
# each handling a different request or transaction.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False) 


class Base(DeclarativeBase):
    pass

# Dependency — FastAPI will call this to get a DB session per request
#  use the factory to create an individual shopping cart(session) for each request.
# why would we need a request? Because we want to ensure that each request gets its own database session, 
# which is important for handling concurrent requests and ensuring that database operations are properly isolated. 
# By using a dependency, FastAPI can automatically manage the lifecycle of the database session, creating a new session 
# for each request and closing it when the request is finished. This helps prevent issues like connection leaks and ensures 
# that database resources are used efficiently.
async def get_db():
    async with SessionLocal() as session:
        yield session
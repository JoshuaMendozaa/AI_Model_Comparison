from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    # Project info
    APP_NAME: str = "AI Model Battle"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = Field(default="postgresql+psycopg2://battleuser:battlepass@postgres/ai_battle_db")
    SYNC_DATABASE_URL: Optional[str] = None
    ASYNC_DATABASE_URL: Optional[str] = None  # Add this field to accept the env var
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # InfluxDB
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str = "your-token-here"
    INFLUXDB_ORG: str = "ai-battle"
    INFLUXDB_BUCKET: str = "benchmarks"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # This allows extra fields and ignores them
    }

settings = Settings()
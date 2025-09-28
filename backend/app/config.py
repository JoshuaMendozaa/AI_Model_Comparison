# config.py - application configuration settings\
#hold app settings like database URL, secret keys, etc.
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    #Project info
    #metadata for the project like name, version, etc.
    proj_name: str = "AI_Model_B"
    api_v1_str: str = "/api/v1"
    DEBUG: bool = False

    # Database settings
    # url for connecting to the database
    DATABASE_URL: Optional[str]
    SYNC_DATABASE_URL: Optional[str] = None

    #REDIS
    # url for connecting to the Redis server
    REDIS_URL: Optional[str] = 'redis://localhost:6379/0'

    # InfluxDB
    # url and credentials for connecting to InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str 
    INFLUXDB_ORG: str = "ai_b"
    INFLUXDB_BUCKET: str = "benchmarks"

    #Security
    # settings for JWT authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  #

    class Config: #pydantic settings config class for loading env variables
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() #instance of settings to be imported and used throughout the app
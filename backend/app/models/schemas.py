from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime 
from enum import Enum

class ModelType(str, Enum):
    LLM = 'llm'
    VISION = 'vision'
    AUDIO = 'audio'
    MULTIMODAL = 'multimodal'

class BattleType(str, Enum):
    ACCURACY = 'accuracy'
    SPEED = 'speed'
    EFFICIENCY = 'efficiency'
    COMPREHENSIVE = 'comprehensive'

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

#AI Model Schemas
class AIModelCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    model_type: ModelType
    parameters_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AIModelResponse(BaseModel):
    id: int
    name: str
    version: str
    description: Optional[str]
    model_type: str
    parameters_count: Optional[int]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any]

    class Config:
        orm_mode = True

#Benchmark Schemas
class BenchmarkCreate(BaseModel):
    model_id: int
    test_name: str
    accuracy: Optional[float] = Field(None, ge=0.0, le=100)
    speed_ms: Optional[float] = Field(None, ge=0.0)
    memory_mb: Optional[float] = Field(None, ge=0.0)
    throughput: Optional[float] = Field(None, ge=0.0)
    latency_p50: Optional[float] = Field(None, ge=0.0)
    latency_p95: Optional[float] = Field(None, ge=0.0)
    latency_p99: Optional[float] = Field(None, ge=0.0)
    test_dataset: Optional[str] = None
    test_size: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = {}

class BenchmarkResponse(BaseModel):
    id: int
    model_id: int
    test_name: str
    accuracy: Optional[float]
    speed_ms: Optional[float]
    memory_mb: Optional[float]
    throughput: Optional[float]
    latency_p50: Optional[float]
    latency_p95: Optional[float]
    latency_p99: Optional[float]
    test_dataset: Optional[str]
    test_size: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True

#Battle Schemas
class BattleCreate(BaseModel):
    model1_id: int
    model2_id: int
    battle_type: BattleType
    battle_config: Optional[Dict[str, Any]] = {}

class BattleResponse(BaseModel):
    id: int
    model1_id: int
    model2_id: int
    winner_model_id: Optional[int]
    battle_type: BattleType
    battle_config: Dict[str, Any]
    results: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True

#WebSocket Schemas
class WSMessage(BaseModel):
    type: str #benchmark_update, battle_update, notification
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

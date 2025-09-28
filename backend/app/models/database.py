from sqlalchemy import column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = column(Integer, primary_key=True, index=True)
    email = column(String, unique=True, index=True, nullable=False)
    hashed_password = column(String, nullable=False)
    is_active = column(Boolean, default=True)
    is_superuser = column(Boolean, default=False)
    created_at = column(DateTime(timezone=True), server_default=func.now())
    updated_at = column(DateTime(timezone=True), onupdate=func.now())
    
    benchmarks = relationship("ai_model", back_populates="owner")

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = column(Integer, primary_key=True, index=True)
    name = column(String, nullable=False)
    version = column(String, nullable=False)
    description = column(Text)
    model_type = column(String)
    parameters_count = column(String)  # Store model parameters as JSON
    owner_id = column(Integer, ForeignKey("users.id"))
    created_at = column(DateTime(timezone=True), server_default=func.now())
    updated_at = column(DateTime(timezone=True), onupdate=func.now())
    metadata = column(JSON, default={})  # Additional model metadata
    
    owner = relationship("User", back_populates="models")
    benchmarks = relationship("Benchmark", back_populates="model")


class Benchmark(Base):
    __tablename__ = "benchmarks"
    
    id = column(Integer, primary_key=True, index=True)
    model_id = column(Integer, ForeignKey("ai_models.id"))
    test_name = column(String, nullable=False)
    accuracy = column(float)
    speed_ms = column(float)
    memory_mb = column(float)
    throughput = column(float)
    latency_p50 = column(float)
    latency_p95 = column(float)
    latency_p99 = column(float)
    test_dataset = column(String)
    test_size = column(Integer)
    metadata = column(JSON, default={})  # Additional benchmark metadata
    created_at = column(DateTime(timezone=True), server_default=func.now())

    model = relationship("AIModel", back_populates="benchmarks")

class Battle(Base):
    __tablename__ = "battles"

    id = column(Integer, primary_key=True, index=True)
    model1_id = column(Integer, ForeignKey("ai_models.id"))
    model2_id = column(Integer, ForeignKey("ai_models.id"))
    winner_model_id = column(Integer, ForeignKey("ai_models.id"), nullable=True)
    battle_type = column(String)
    battle_config = column(JSON, default={})  # Configuration details for the battle
    results = column(JSON, default={})  # Store battle results as JSON
    created_at = column(DateTime(timezone=True), server_default=func.now())

    model1 = relationship("AIModel", foreign_keys=[model1_id])
    model2 = relationship("AIModel", foreign_keys=[model2_id])
    winner_model = relationship("AIModel", foreign_keys=[winner_model_id])
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.db_base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Fixed relationship name
    models = relationship("AIModel", back_populates="owner")

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    description = Column(Text)
    model_type = Column(String)
    parameters_count = Column(String)  # Store as string for flexibility
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    model_metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)  # Added missing field
    
    owner = relationship("User", back_populates="models")
    benchmarks = relationship("Benchmark", back_populates="model")

class Benchmark(Base):
    __tablename__ = "benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"))
    test_name = Column(String, nullable=False)
    accuracy = Column(Float)
    speed_ms = Column(Float)
    memory_mb = Column(Float)
    throughput = Column(Float)
    latency_p50 = Column(Float)
    latency_p95 = Column(Float)
    latency_p99 = Column(Float)
    test_dataset = Column(String)
    test_size = Column(Integer)
    model_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("AIModel", back_populates="benchmarks")

class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, index=True)
    model1_id = Column(Integer, ForeignKey("ai_models.id"))
    model2_id = Column(Integer, ForeignKey("ai_models.id"))
    winner_model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=True)
    battle_type = Column(String)
    battle_config = Column(JSON, default={})
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model1 = relationship("AIModel", foreign_keys=[model1_id])
    model2 = relationship("AIModel", foreign_keys=[model2_id])
    winner_model = relationship("AIModel", foreign_keys=[winner_model_id])
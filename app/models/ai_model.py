from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class AIModel(Base):
    __tablename__ = "ai_models"  # Define the name of the database table for AI models

    id = Column(Integer, primary_key=True, index=True)  # Unique identifier for each model, set as primary key and indexed for faster queries
    name = Column(String(255), nullable=False)  # Name of the AI model, required field with a maximum length of 255 characters
    version = Column(String(50), nullable=False)  # Version of the AI model, required field with a maximum length of 50 characters
    creator = Column(String(255), nullable=False)  # Creator of the AI model, required field with a maximum length of 255 characters
    description = Column(Text, nullable=True)  # Optional description of the AI model, stored as text for longer entries
    registered_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp for when the model was registered, automatically set to the current time when a new record is created
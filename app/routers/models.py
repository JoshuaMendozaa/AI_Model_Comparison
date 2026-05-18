from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.ai_model import AIModel

router = APIRouter(prefix="/models", tags=["models"])

# --- Pydantic schemas for request and response validation ---
# These schemas define the structure of the data for creating and retrieving AI models.

class ModelCreate(BaseModel):   #Post request body schema for creating a new AI model
    name: str
    version: str
    creator: str
    description: Optional[str] = None

class ModelResponse(BaseModel): #Get response schema for returning AI model details, including the registered_at timestamp
    id: int
    name: str
    version: str
    creator: str
    description: Optional[str] = None
    registered_at: datetime

    class Config:
        from_attributes = True  # lets Pydantic read SQLAlchemy objects


# --- Routes --- #
@router.post("/", response_model=ModelResponse) #Endpoint to register a new AI model, expects a ModelCreate Object in the request body and returns a ModelResponse Object
async def register_model(model: ModelCreate, db: AsyncSession = Depends(get_db)):
    new_model = AIModel(**model.model_dump())   #
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    return new_model

@router.get("/", response_model=list[ModelResponse])    #Endpoint to list all registered AI models, returns a list of ModelResponse Objects
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel))
    return result.scalars().all()

@router.get("/{model_id}", response_model=ModelResponse)    #Endpoint to get details of a specific AI model by its ID, returns a ModelResponse Object if found, otherwise raises a 404 error
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model
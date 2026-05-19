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
@router.post("/", response_model=ModelResponse) #Endpoint to register a new AI model, response_model specifies that the response will be serialized using the ModelResponse schema
async def register_model(model: ModelCreate, db: AsyncSession = Depends(get_db)): #db parameter is an asynchronous database session provided by the get_db dependency
    new_model = AIModel(**model.model_dump())   #**model.model_dump()converts the incoming ModelCreate Pydantic object into a dictionary and unpacks it as keyword arguments to create a new AIModel instance
    db.add(new_model)   #adds the new model instance to the database session
    await db.commit()   #commits the transaction to save the new model to the databsase
    await db.refresh(new_model) #refreshes the new_model instance to get the updated data from the database, including the generated ID and timestamp
    return new_model    #returns the newly created model, which will be serialized to JSON using the ModelResponse schema defined earlier

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

#this file defines the api endpoints for managing ai models, including registring 
#new models, listing all models, and retrieving details of a specific model.
# It uses SQLAlchemy for database interactions and Pydantic for data validation and serialization.
# register_model endpoint allows clients to submit new ai model, which is then stored in 
#postgres database, while list_models and get_model endpoints allow clients to retrieve model information.

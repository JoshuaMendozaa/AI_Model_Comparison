from fastapi import APIRouter, FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.events import event_publisher 
from app.models.database import User, AIModel
from app.models.schemas import AIModelCreate, AIModelResponse, AIModelUpdate

router = APIRouter()

@router.post("/", response_model=AIModelResponse)
async def create_model(
    model_data: AIModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create new model
    db_model = AIModel(
        **model_data.dict(),
        owner_id=current_user.id
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    
    # Publish event
    await event_publisher.publish_model_added({
        "id": db_model.id,
        "name": db_model.name,
        "version": db_model.version,
        "owner": current_user.username
    })
    
    return db_model

@router.get("/", response_model=List[AIModelResponse])
async def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    model_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(AIModel)
    
    # Apply filters
    filters = []
    if model_type:
        filters.append(AIModel.model_type == model_type)
    if is_active is not None:
        filters.append(AIModel.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    model_update: AIModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(AIModel).where(
            and_(AIModel.id == model_id, AIModel.owner_id == current_user.id)
        )
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=404,
            detail="Model not found or you don't have permission"
        )
    
    # Update model
    for field, value in model_update.dict(exclude_unset=True).items():
        setattr(model, field, value)
    
    await db.commit()
    await db.refresh(model)
    return model

@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(AIModel).where(
            and_(AIModel.id == model_id, AIModel.owner_id == current_user.id)
        )
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=404,
            detail="Model not found or you don't have permission"
        )
    
    # Soft delete
    model.is_active = False
    await db.commit()
    return {"message": "Model deleted successfully"}

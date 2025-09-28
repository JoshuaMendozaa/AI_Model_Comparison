from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from app.models.database import User
from app.models.schemas import UserCreate, UserResponse, Token
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    # Basic password validation
    if len(user_create.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    if len(user_create.password) > 128:
        raise HTTPException(status_code=400, detail="Password is too long (maximum 128 characters)")
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_create.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Authenticate user - using email as username
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
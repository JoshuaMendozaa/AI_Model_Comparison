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

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email)) | (User.username == user_data.username)
    if result.scalarr_one_or_more():
        raise HTTPException(status_code=400, detail="Email or username already registered")
    
    # Create new user
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login?", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):

    # Authenticate user
    result = await db.exectute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
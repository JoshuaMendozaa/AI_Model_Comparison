from datetime import datetime, timedelta
from typing import Optional 
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status  
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
from app.config import settings
from app.core.database import get_db
from app.models.database import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def _prepare_password(password: str) -> str:
    """
    Prepare password for bcrypt hashing.
    Bcrypt has a 72-byte limit, so we hash long passwords with SHA256 first.
    """
    # Convert to bytes to check actual byte length
    password_bytes = password.encode('utf-8')
    
    # If password is longer than 72 bytes, pre-hash it with SHA256
    if len(password_bytes) > 72:
        # Use SHA256 to create a fixed-length hash, then encode as hex
        password_hash = hashlib.sha256(password_bytes).hexdigest()
        return password_hash
    
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    prepared_password = _prepare_password(plain_password)
    return pwd_context.verify(prepared_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing"""
    prepared_password = _prepare_password(password)
    return pwd_context.hash(prepared_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
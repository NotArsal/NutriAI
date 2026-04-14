"""
app/api/deps.py — FastAPI dependencies for DI.
"""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import get_settings
from app.core.database import async_session_maker
from app.core.security import oauth2_scheme, verify_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenData

settings = get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting DB sessions into routers/services."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    token_data = TokenData(email=email)
    user = await UserRepository.get_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db), token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False))
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(db, token)
    except HTTPException:
        return None

"""
app/routers/auth.py — Authentication endpoints (multi-user).

Endpoints:
  POST /auth/register  → Create a new account
  POST /auth/login     → OAuth2 form login → JWT access token
  GET  /auth/me        → Fetch current user's profile
  PUT  /auth/me        → Update current user's profile (name, password, email)
  DELETE /auth/me      → Deactivate (soft-delete) the current user's account
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import Token, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """Register a new user account."""
    existing = await UserRepository.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
    user = await UserRepository.create(db, obj_in=user_in)
    return user


# ── Login ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """OAuth2 password login — returns a Bearer JWT access token."""
    user = await UserRepository.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}


# ── Get current user ───────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return the currently authenticated user's profile."""
    return current_user


# ── Update current user ────────────────────────────────────────────────────────

@router.put("/me", response_model=UserOut)
async def update_current_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update the current user's profile (full_name, email, password)."""
    # If email is being changed, ensure it's not taken
    if user_in.email and user_in.email != current_user.email:
        existing = await UserRepository.get_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already in use by another account.",
            )
    updated = await UserRepository.update(db, user=current_user, obj_in=user_in)
    return updated


# ── Deactivate account ─────────────────────────────────────────────────────────

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Soft-delete: mark the current user's account as inactive."""
    from app.schemas.user import UserUpdate
    await UserRepository.update(db, user=current_user, obj_in=UserUpdate())
    # Set is_active = False directly
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

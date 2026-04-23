"""
app/schemas/user.py — Pydantic models for Users, Auth Tokens, and Prediction History.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr


# ── Registration / Creation ─────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


# ── Update ─────────────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


# ── Public output ───────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Tokens ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# ── Prediction history (per-user reports) ───────────────────────────────────────

class PredictionLogOut(BaseModel):
    id: int
    diet_recommendation: str
    risk_score: float
    meal_category: str
    patient_inputs: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class UserReportsOut(BaseModel):
    user_id: int
    total: int
    predictions: List[PredictionLogOut]

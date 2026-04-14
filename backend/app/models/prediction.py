"""
app/models/prediction.py — SQLAlchemy Prediction log model mapping.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class PredictionLog(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    
    # Store the input subset directly for tracking
    patient_inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Store key output results
    diet_recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    meal_category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Metadata
    hashed_input: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

"""
app/repositories/prediction_repo.py — Database interactions for Prediction model.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionLog


class PredictionRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: Optional[int],
        patient_inputs: dict,
        diet_recommendation: str,
        risk_score: float,
        meal_category: str,
        hashed_input: str,
    ) -> PredictionLog:
        db_obj = PredictionLog(
            user_id=user_id,
            patient_inputs=patient_inputs,
            diet_recommendation=diet_recommendation,
            risk_score=risk_score,
            meal_category=meal_category,
            hashed_input=hashed_input,
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_hash(session: AsyncSession, hashed_input: str) -> PredictionLog | None:
        """Check if identical prediction was logged."""
        stmt = select(PredictionLog).where(
            PredictionLog.hashed_input == hashed_input
        ).order_by(PredictionLog.id.desc())
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_user(
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[PredictionLog]:
        """Return paginated predictions for a specific user, newest first."""
        stmt = (
            select(PredictionLog)
            .where(PredictionLog.user_id == user_id)
            .order_by(PredictionLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(session: AsyncSession, user_id: int) -> int:
        """Return total prediction count for a user."""
        from sqlalchemy import func
        stmt = select(func.count(PredictionLog.id)).where(PredictionLog.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one() or 0

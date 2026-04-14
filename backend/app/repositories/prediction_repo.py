"""
app/repositories/prediction_repo.py — Database interactions for Prediction model.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionLog


class PredictionRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int | None,
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
        # Check if identical prediction was logged
        stmt = select(PredictionLog).where(PredictionLog.hashed_input == hashed_input).order_by(PredictionLog.id.desc())
        result = await session.execute(stmt)
        return result.scalars().first()

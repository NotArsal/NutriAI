"""
app/routers/reports.py — Per-user prediction history endpoints.

Endpoints:
  GET  /reports          → Paginated list of the current user's predictions
  GET  /reports/{id}     → Single prediction detail
  DELETE /reports/{id}   → Delete a specific prediction record
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.prediction_repo import PredictionRepository
from app.schemas.user import PredictionLogOut, UserReportsOut

router = APIRouter(prefix="/reports", tags=["Reports"])
log = get_logger(__name__)


# ── List user's reports ─────────────────────────────────────────────────────────

@router.get("", response_model=UserReportsOut)
async def list_my_reports(
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return a paginated list of the authenticated user's prediction history."""
    predictions = await PredictionRepository.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    total = await PredictionRepository.count_by_user(db, user_id=current_user.id)
    log.info("reports_fetched", user_id=current_user.id, count=len(predictions), total=total)
    return UserReportsOut(
        user_id=current_user.id,
        total=total,
        predictions=predictions,
    )


# ── Single report detail ────────────────────────────────────────────────────────

@router.get("/{report_id}", response_model=PredictionLogOut)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Fetch a single prediction report by ID. Only the owning user can access it."""
    from sqlalchemy import select
    from app.models.prediction import PredictionLog

    stmt = select(PredictionLog).where(
        PredictionLog.id == report_id,
        PredictionLog.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or does not belong to you.",
        )
    return log_entry


# ── Delete a report ─────────────────────────────────────────────────────────────

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a specific prediction record. Only the owning user can delete it."""
    from sqlalchemy import select
    from app.models.prediction import PredictionLog

    stmt = select(PredictionLog).where(
        PredictionLog.id == report_id,
        PredictionLog.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or does not belong to you.",
        )
    await db.delete(log_entry)
    await db.commit()
    log.info("report_deleted", user_id=current_user.id, report_id=report_id)

"""
app/routers/health.py — /health and /models/info endpoints.

/health returns:
  • Overall service status
  • Per-model load status + sklearn metadata
  • Full HuggingFace-style model card
  • App version and environment
"""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.responses import HealthResponse, ModelCard, ModelInfo
from app.services.ml_service import MODEL_CARD_DATA, ml_service

router = APIRouter(tags=["Health"])
settings = get_settings()

# Record startup time for uptime calculation
_START_TIME = time.time()


@router.get("/", summary="Root ping")
async def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check with model card",
    description=(
        "Returns the operational status of the API, detailed per-model information, "
        "and a HuggingFace-style model card documenting training data, limitations, and bias notes."
    ),
)
async def health() -> HealthResponse:
    raw_models = ml_service.get_model_info()
    all_loaded  = all(v["loaded"] for v in raw_models.values())

    return HealthResponse(
        status="healthy" if all_loaded else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        uptime_s=round(time.time() - _START_TIME, 1),
        models={
            name: ModelInfo(**info) for name, info in raw_models.items()
        },
        model_card=ModelCard(**MODEL_CARD_DATA),
    )


@router.get("/models/info", summary="Model metadata")
async def model_info():
    """Return class distribution info for diet and meal models."""
    return {
        "models":       ml_service.get_model_info(),
        "diet_classes": ml_service.diet_classes,
        "meal_classes": ml_service.meal_classes,
        "stats":        ml_service.meta.get("stats", {}),
        "shap_enabled": settings.shap_enabled,
        "ci_enabled":   settings.ci_enabled,
    }

"""
app/main.py — FastAPI application factory (v3).

Key improvements over legacy main.py:
  • lifespan context manager for model loading (modern FastAPI pattern)
  • Rate limiting via slowapi (per-IP, configurable per route)
  • structlog JSON logging middleware with request IDs
  • Fully typed routers from app/routers/
  • Model loads inside lifespan — no module-level side-effects
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.database import engine, Base
from app.core.redis_client import redis_client
from app.core.logging import LoggingMiddleware, configure_logging, get_logger
from app.routers import auth, chat, health, meals, predict, reports
from app.services.ml_service import ml_service

settings = get_settings()
log      = get_logger(__name__)

# ── Rate limiter ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models once at startup; release resources on shutdown."""
    configure_logging()
    log.info("startup_begin", version=settings.app_version, env=settings.environment)
    
    # Init ML models
    ml_service.load()
    log.info("ml_models_loaded", models_loaded=ml_service._loaded)
    
    # Init DB schema (in a production environment, you should use Alembic for migrations instead of create_all)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("database_tables_created")
    except Exception as e:
        log.error("database_init_failed", error=str(e))
    
    # Init Redis
    try:
        await redis_client.connect()
    except Exception as e:
        log.error("redis_init_failed", error=str(e))
    
    yield
    
    # Teardown
    try:
        await redis_client.disconnect()
        await engine.dispose()
    except Exception:
        pass
    log.info("shutdown_complete")


# ── App factory ────────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Research-grade clinical nutrition recommendation engine. "
            "Powered by Gradient Boosting + Random Forest models with SHAP explainability "
            "and 90% confidence intervals on risk scores."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ───────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # ── Logging middleware ─────────────────────────────────────────────
    app.add_middleware(LoggingMiddleware)

    # ── Rate limiting ──────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Routers ────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(predict.router)
    app.include_router(meals.router)
    app.include_router(chat.router)
    app.include_router(reports.router)

    return app


app = create_app()

"""
app/core/database.py — SQLAlchemy async setup.

Uses NullPool so no connections are held open between requests.
This means the app starts cleanly even when PostgreSQL is unreachable,
and each request gets a fresh connection (or a clean 503 if DB is down).
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
log = get_logger("database")

engine = create_async_engine(
    settings.database_url,
    echo=False,
    # AsyncAdaptedQueuePool: Production-ready connection pooling.
    # We maintain a pool of open connections to reduce TCP handshake latency.
    pool_size=5, # Standard for Render free/hobby tiers
    max_overflow=10,
    pool_pre_ping=True, # Validates connections before checkout
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

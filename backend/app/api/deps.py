"""
app/api/deps.py — FastAPI dependencies for DI.

DB error handling strategy
──────────────────────────
• get_db()           — Yields a session. If Postgres is unreachable the
                       ConnectionRefusedError is converted to HTTP 503 so
                       callers get a clean JSON error, not a 500 crash.
• get_current_user() — Wraps the DB lookup; propagates 401 on bad token,
                       503 on DB failure, never 500.
• get_current_user_optional() — Returns None when token absent; None when
                       DB is unreachable (prediction endpoint stays up).
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import async_session_maker
from app.core.security import oauth2_scheme, verify_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenData

settings = get_settings()

# ── Connection-error sentinel ──────────────────────────────────────────────────
# asyncpg raises ConnectionRefusedError (OSError subclass). We also catch
# generic Exception so any driver-level crash is handled the same way.
_DB_CONN_ERRORS = (OSError, ConnectionRefusedError, asyncio.TimeoutError)


def _is_db_conn_error(exc: BaseException) -> bool:
    """Return True if exc looks like a driver-level connection failure."""
    if isinstance(exc, _DB_CONN_ERRORS):
        return True
    # SQLAlchemy wraps driver errors in its own exception hierarchy
    name = type(exc).__name__
    return any(k in name for k in ("OperationalError", "InterfaceError", "CannotConnect", "ConnectionDoesNotExist"))


_DB_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Database is temporarily unavailable. Predictions still work — auth and history require a database.",
)


# ── Session dependency ─────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inject an async DB session. Converts connection errors to HTTP 503."""
    try:
        async with async_session_maker() as session:
            try:
                yield session
                # Attempt commit; if the DB went away mid-request, swallow it.
                try:
                    await session.commit()
                except Exception:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
            except HTTPException:
                # Re-raise HTTP exceptions unchanged (e.g. 401, 404 from routers)
                try:
                    await session.rollback()
                except Exception:
                    pass
                raise
            except Exception as exc:
                try:
                    await session.rollback()
                except Exception:
                    pass
                if _is_db_conn_error(exc):
                    raise _DB_UNAVAILABLE from exc
                raise
            finally:
                try:
                    await session.close()
                except Exception:
                    pass
    except HTTPException:
        raise
    except Exception as exc:
        # Session-maker itself failed (e.g. pool exhausted, driver crash)
        if _is_db_conn_error(exc):
            raise _DB_UNAVAILABLE from exc
        raise


# ── Auth dependencies ──────────────────────────────────────────────────────────

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
    try:
        user = await UserRepository.get_by_email(db, email=token_data.email)
    except HTTPException:
        raise  # 503 already formatted by get_db
    except Exception as exc:
        if _is_db_conn_error(exc):
            raise _DB_UNAVAILABLE from exc
        raise credentials_exception from exc

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
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)),
) -> User | None:
    """Return the user if authenticated, or None if token absent / DB down."""
    if not token:
        return None
    try:
        return await get_current_user(db, token)
    except HTTPException as exc:
        # 503 (DB down) or 401 (bad token) — prediction still works, just unauth
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return None  # silently degrade: predictions skip DB persistence
        return None

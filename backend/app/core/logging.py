"""
app/core/logging.py — structlog JSON logger with request ID injection.

In development: colourful, pretty-printed output.
In production  : JSON lines for log aggregators (Datadog, CloudWatch, etc.)

Usage:
    from app.core.logging import get_logger, configure_logging
    log = get_logger(__name__)
    log.info("prediction_complete", diet="Low_Carb", risk_score=62.4, request_id=rid)
"""
from __future__ import annotations

import logging
import sys
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


def configure_logging() -> None:
    """Call once at app startup inside the lifespan context."""
    settings = get_settings()
    is_dev = settings.environment == "development"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_dev:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging so uvicorn logs route through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    return structlog.get_logger(name)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Inject request_id into structlog context, log request/response timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        log = get_logger("http")
        t0 = time.perf_counter()
        log.info("request_started")

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        log.info(
            "request_completed",
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )

        # Surface request_id in response header for correlation
        response.headers["X-Request-ID"] = request_id
        return response

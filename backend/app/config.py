"""
app/config.py — Centralised settings via pydantic-settings.
All values can be overridden through environment variables.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ────────────────────────────────────────────────────────────
    app_name: str = "NutriPlanner API"
    app_version: str = "3.0.0"
    environment: str = "development"  # development | staging | production
    log_level: str = "INFO"

    # ── CORS ───────────────────────────────────────────────────────────
    allowed_origins_raw: str = ""  # comma-separated; env var: ALLOWED_ORIGINS_RAW

    @property
    def allowed_origins(self) -> List[str]:
        raw = os.environ.get("ALLOWED_ORIGINS", self.allowed_origins_raw)
        parsed = [o.strip() for o in raw.split(",") if o.strip()]
        if not parsed:
            parsed = [
                "http://localhost:5173",
                "http://localhost:4173",
                "http://localhost:3000",
            ]
        return parsed

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nutriplanner"
    
    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    
    # ── Security ───────────────────────────────────────────────────────
    secret_key: str = "very-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # ── Models ─────────────────────────────────────────────────────────
    model_dir: Path = Path(__file__).parent.parent.parent / "ml"

    # ── Rate limiting ──────────────────────────────────────────────────
    rate_limit_predict: str = "60/minute"
    rate_limit_chat: str = "30/minute"
    rate_limit_default: str = "120/minute"

    # ── SHAP ───────────────────────────────────────────────────────────
    shap_enabled: bool = True
    shap_top_n: int = 5

    # ── Confidence intervals ───────────────────────────────────────────
    ci_enabled: bool = True
    ci_n_bootstrap: int = 50  # number of tree sub-samples for CI


@lru_cache
def get_settings() -> Settings:
    return Settings()

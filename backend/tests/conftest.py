"""
tests/conftest.py — Re-architected for async tests with Redis/DB mocks.
"""
from __future__ import annotations

from typing import AsyncGenerator
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.deps import get_db, get_current_user_optional
from app.core.redis_client import redis_client

@pytest.fixture
def client():
    """Synchronous test client."""
    with TestClient(app) as ac:
        yield ac

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Global mock for redis_client to prevent real connection attempts."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = None
    mock.connect.return_value = None
    mock.disconnect.return_value = None
    monkeypatch.setattr("app.routers.predict.redis_client", mock)
    return mock

@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy AsyncSession."""
    session = AsyncMock()
    return session

@pytest.fixture(autouse=True)
def override_db(mock_db_session):
    """Directly override dependency to use the mock session."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def sample_patient() -> dict:
    return {
        "age": 45, "gender": "Male", "weight_kg": 75.0, "height_cm": 170,
        "disease_type": "Diabetes", "severity": "Moderate", "activity_level": "Moderate",
        "daily_caloric": 2200, "cholesterol": 210.0, "blood_pressure": 135, "glucose": 150.0
    }

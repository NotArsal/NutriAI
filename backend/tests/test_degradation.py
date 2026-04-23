import pytest
from httpx import AsyncClient, ASGITransport
import mock

from app.main import app
from app.core.redis_client import redis_client

@pytest.mark.asyncio
async def test_graceful_degradation_db_down():
    """
    Test that if the database raises an OSError (e.g. connection refused),
    the global error handler catches it and returns a 503 instead of crashing.
    """
    # Mock get_db dependency or engine to raise OSError
    # Since auth requires DB, let's hit an auth endpoint
    
    with mock.patch("app.routers.auth.authenticate_user", side_effect=OSError("Connection refused")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/auth/login", 
                data={"username": "test@example.com", "password": "password"}
            )
            assert response.status_code == 503
            assert "Database is temporarily unavailable" in response.json()["detail"]

@pytest.mark.asyncio
async def test_prediction_works_without_redis():
    """
    Test that the prediction engine still functions if Redis is unreachable.
    """
    # Mock redis get/set to raise ConnectionError or just mock them to do nothing
    with mock.patch.object(redis_client, 'get', return_value=None):
        with mock.patch.object(redis_client, 'set', side_effect=Exception("Redis down")):
            # It should silently fail the cache set and return the prediction
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/predict/diet",
                    json={
                        "age": 45,
                        "gender": "Male",
                        "weight_kg": 75,
                        "height_cm": 170,
                        "disease_type": "Diabetes",
                        "severity": "Moderate",
                        "activity_level": "Moderate",
                        "daily_caloric": 2200,
                        "cholesterol": 210,
                        "blood_pressure": 135,
                        "glucose": 150
                    }
                )
                assert response.status_code == 200
                assert "recommendation" in response.json()

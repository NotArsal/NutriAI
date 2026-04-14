"""
tests/test_predict_architecture.py — Verifies caching, hashing, and DB logging in Predict endpoint.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.schemas.responses import PredictResponse

@pytest.mark.asyncio
async def test_predict_flow_hashing_and_caching(client: AsyncClient, mock_redis, sample_patient):
    """Verify that same input hashes correctly and hits cache on second call."""
    # First call: Cache Miss
    mock_redis.get.return_value = None # Cache miss
    
    response1 = await client.post("/predict", json=sample_patient)
    assert response1.status_code == 200
    
    # Verify redis 'set' was called with some JSON
    assert mock_redis.set.called
    cache_key = mock_redis.set.call_args[0][0]
    assert cache_key.startswith("predict:")
    
    # Second call: Cache Hit
    # Feed the previous result back as cached
    mock_redis.get.return_value = response1.text 
    
    response2 = await client.post("/predict", json=sample_patient)
    assert response2.status_code == 200
    assert mock_redis.get.called
    # Since it's a hit, it shouldn't re-calculate or re-save (mock_redis.set call count should remain 1)
    assert mock_redis.set.call_count == 1

@pytest.mark.asyncio
async def test_predict_logs_to_db(client: AsyncClient, mock_db_session, sample_patient, monkeypatch):
    """Verify that every prediction attempt is logged to the PostgreSQL database."""
    from app.repositories.prediction_repo import PredictionRepository
    
    mock_create = AsyncMock()
    monkeypatch.setattr("app.repositories.prediction_repo.PredictionRepository.create", mock_create)
    
    response = await client.post("/predict", json=sample_patient)
    assert response.status_code == 200
    
    # Verify repository 'create' was called
    assert mock_create.called
    call_args = mock_create.call_args[1]
    assert call_args["diet_recommendation"] is not None
    assert call_args["risk_score"] >= 0
    assert call_args["meal_category"] is not None
    assert "hashed_input" in call_args

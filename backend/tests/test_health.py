"""
tests/test_health.py — Tests for /health and /models/info endpoints.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_ping(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_structure(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()

    # Status must be present
    assert data["status"] in {"healthy", "degraded", "unhealthy"}

    # Model dict must have all three models
    assert "diet" in data["models"]
    assert "risk" in data["models"]
    assert "meal" in data["models"]

    # Model card must be present and valid
    card = data["model_card"]
    assert "training_samples" in card
    assert "known_limitations" in card
    assert isinstance(card["known_limitations"], list)
    assert "intended_use" in card
    assert "bias_notes" in card
    assert "out_of_scope" in card


def test_health_response_header(client: TestClient):
    """Logging middleware should inject X-Request-ID into every response."""
    resp = client.get("/health")
    assert "x-request-id" in resp.headers


def test_models_info(client: TestClient):
    resp = client.get("/models/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "diet_classes" in data
    assert "meal_classes" in data
    assert len(data["diet_classes"]) >= 2

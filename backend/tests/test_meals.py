"""
tests/test_meals.py — Tests for /meals endpoint.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


class TestMeals:
    def test_status_200(self, client: TestClient, sample_patient: dict):
        resp = client.post("/meals", json=sample_patient)
        assert resp.status_code == 200

    def test_response_fields(self, client: TestClient, sample_patient: dict):
        data = client.post("/meals", json=sample_patient).json()
        assert "category" in data
        assert "cuisine" in data
        assert "meals" in data
        assert isinstance(data["meals"], list)

    def test_meals_nonempty(self, client: TestClient, sample_patient: dict):
        data = client.post("/meals", json=sample_patient).json()
        assert len(data["meals"]) > 0

    def test_meal_has_nutrition_fields(self, client: TestClient, sample_patient: dict):
        data  = client.post("/meals", json=sample_patient).json()
        meal  = data["meals"][0]
        for field in ("name", "kcal", "protein", "carbs", "fat", "time"):
            assert field in meal, f"Missing field '{field}' in meal: {meal}"

    def test_cuisine_matches(self, client: TestClient, sample_patient: dict):
        data = client.post("/meals", json=sample_patient).json()
        assert data["cuisine"] == sample_patient["cuisine"]

    def test_category_valid(self, client: TestClient, sample_patient: dict):
        data = client.post("/meals", json=sample_patient).json()
        assert data["category"] in {"Balanced-Macro", "High-Protein", "Heart-Healthy"}

    def test_peanut_allergen_filtered(self, client: TestClient, sample_patient: dict):
        patient = {**sample_patient, "allergies": "Peanuts"}
        data    = client.post("/meals", json=patient).json()
        for meal in data["meals"]:
            name_lower = meal["name"].lower()
            assert "peanut" not in name_lower and "groundnut" not in name_lower

    def test_invalid_payload_rejected(self, client: TestClient):
        resp = client.post("/meals", json={"invalid": "payload"})
        assert resp.status_code == 422

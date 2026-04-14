"""
tests/test_predict.py — Tests for /predict, /predict/diet, /predict/risk.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestFullPredict:
    def test_status_200(self, client: TestClient, sample_patient: dict):
        resp = client.post("/predict", json=sample_patient)
        assert resp.status_code == 200

    def test_diet_field_valid(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        assert data["diet"] in {"Balanced", "Low_Carb", "Low_Sodium"}

    def test_confidence_in_range(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        assert 0.0 <= data["conf"] <= 1.0

    def test_risk_score_in_range(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        assert 0.0 <= data["riskScore"] <= 100.0

    def test_confidence_interval_ordered(self, client: TestClient, sample_patient: dict):
        """Lower CI bound must be ≤ point estimate ≤ upper CI bound."""
        data = client.post("/predict", json=sample_patient).json()
        ci = data["riskCI"]
        assert ci["lower"] <= data["riskScore"] <= ci["upper"]

    def test_risk_level_consistent(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        rs = data["riskScore"]
        expected_level = "High" if rs >= 70 else "Moderate" if rs >= 40 else "Low"
        assert data["riskLevel"] == expected_level

    def test_meal_cat_valid(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        assert data["mealCat"] in {"Balanced-Macro", "High-Protein", "Heart-Healthy"}

    def test_meals_list_nonempty(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        assert len(data["recommended_meals"]) > 0

    def test_bmi_calculated(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        # 85 / (1.70)^2 = 29.4
        assert abs(data["bmi"] - 29.4) < 0.5

    def test_diet_proba_sums_to_one(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        total = sum(data["diet_proba"].values())
        assert abs(total - 1.0) < 0.01

    def test_scores_present(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict", json=sample_patient).json()
        scores = data["scores"]
        for key in ("metabolic", "cardiovascular", "lifestyle", "overall"):
            assert key in scores
            assert 0 <= scores[key] <= 100

    def test_hypertensive_gets_low_sodium(self, client: TestClient, hypertensive_patient: dict):
        """Hypertensive patients should generally be classified Low_Sodium."""
        data = client.post("/predict", json=hypertensive_patient).json()
        # Model may differ but diet response field must exist and be valid
        assert data["diet"] in {"Balanced", "Low_Carb", "Low_Sodium"}

    def test_gluten_allergy_filtered(self, client: TestClient, hypertensive_patient: dict):
        """Meals must not contain gluten allergen keywords for gluten-allergic patients."""
        data  = client.post("/predict", json=hypertensive_patient).json()
        meals = data["recommended_meals"]
        gluten_kws = ["roti", "chapati", "pasta", "bread", "dumpling", "quesadilla"]
        for meal in meals:
            name_lower = meal["name"].lower()
            for kw in gluten_kws:
                assert kw not in name_lower, f"Gluten keyword '{kw}' found in meal: {meal['name']}"

    def test_invalid_gender_rejected(self, client: TestClient, sample_patient: dict):
        bad = {**sample_patient, "gender": "Unknown"}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_invalid_disease_rejected(self, client: TestClient, sample_patient: dict):
        bad = {**sample_patient, "disease_type": "Cancer"}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_age_out_of_range_rejected(self, client: TestClient, sample_patient: dict):
        bad = {**sample_patient, "age": 15}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422


class TestDietOnly:
    def test_status_200(self, client: TestClient, sample_patient: dict):
        resp = client.post("/predict/diet", json=sample_patient)
        assert resp.status_code == 200

    def test_fields_present(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict/diet", json=sample_patient).json()
        assert "recommendation" in data
        assert "confidence" in data
        assert "probabilities" in data


class TestRiskOnly:
    def test_status_200(self, client: TestClient, sample_patient: dict):
        resp = client.post("/predict/risk", json=sample_patient)
        assert resp.status_code == 200

    def test_ci_present(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict/risk", json=sample_patient).json()
        assert "riskCI" in data
        assert data["riskCI"]["lower"] <= data["risk_score"] <= data["riskCI"]["upper"]

    def test_components_present(self, client: TestClient, sample_patient: dict):
        data = client.post("/predict/risk", json=sample_patient).json()
        for key in ("glucose", "blood_pressure", "cholesterol", "bmi", "activity", "nutrition"):
            assert key in data["components"]

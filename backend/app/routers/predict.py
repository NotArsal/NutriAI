"""
app/routers/predict.py — Prediction endpoints.

Endpoints:
  POST /predict          → Full composite prediction (diet + risk + meals + SHAP + CI)
  POST /predict/diet     → Diet classification only
  POST /predict/risk     → Risk scoring only (with CI)
"""
from __future__ import annotations

import hashlib
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, get_db
from app.core.logging import get_logger
from app.core.meals_db import compute_risk_breakdown, get_meals
from app.core.redis_client import redis_client
from app.models.user import User
from app.repositories.prediction_repo import PredictionRepository
from app.schemas.patient import PatientInput
from app.schemas.responses import (
    ConfidenceInterval,
    DietResponse,
    HealthScores,
    PredictResponse,
    RiskResponse,
    SHAPExplanation,
    SHAPFeature,
    TrendCurve,
    Point,
)
from app.services.ml_service import ml_service

router = APIRouter(prefix="/predict", tags=["Predictions"])
log = get_logger(__name__)


def _build_insights(patient: PatientInput, bmi: float) -> list[str]:
    """Clinical insight rules — mirrors original main.py logic."""
    insights = []
    if patient.disease_type == "Diabetes":
        insights.append("Target fasting glucose < 100 mg/dL through carbohydrate restriction.")
        if patient.glucose > 140:
            insights.append("Post-meal glucose monitoring at 1–2 hrs is essential.")
    elif patient.disease_type == "Hypertension":
        insights.append("Reduce sodium intake below 1,500 mg/day using the DASH protocol.")
        if patient.blood_pressure > 140:
            insights.append("Current BP indicates stage 2 hypertension — consult your physician.")
    else:
        if bmi > 30:
            insights.append(f"BMI of {bmi} indicates obesity — a 300–500 kcal daily deficit is recommended.")
        insights.append("Maintain dietary diversity to meet all micronutrient requirements.")
    if patient.activity_level == "Sedentary":
        insights.append("150 min/week of moderate cardio significantly improves all biomarker trajectories.")
    if patient.cholesterol > 200:
        insights.append("Elevated cholesterol: reduce saturated fats, increase omega-3 rich foods.")
    return insights


def _build_health_scores(components: dict, patient: PatientInput) -> HealthScores:
    metabolic  = max(0, int(100 - components["glucose"] * 2.5 - components["bmi"] * 3))
    cardio     = max(0, int(100 - components["blood_pressure"] * 2.5 - components["cholesterol"] * 2))
    lifestyle  = min(100, int((patient.weekly_exercise / 10) * 60 + (
        40 if patient.activity_level == "Active" else 20 if patient.activity_level == "Moderate" else 0
    )))
    overall    = int((metabolic + cardio + lifestyle) / 3)
    return HealthScores(
        metabolic=metabolic,
        cardiovascular=cardio,
        lifestyle=lifestyle,
        overall=overall,
    )


def _parse_shap(shap_dict: dict | None) -> SHAPExplanation | None:
    """Convert raw SHAP dict from ml_service into typed SHAPExplanation."""
    if shap_dict is None:
        return None
    return SHAPExplanation(
        model_type=shap_dict["model_type"],
        base_value=shap_dict["base_value"],
        note=shap_dict["note"],
        top_features=[
            SHAPFeature(
                feature=f["feature"],
                raw_value=f["raw_value"],
                shap_value=f["shap_value"],
                direction=f["direction"],
            )
            for f in shap_dict["top_features"]
        ],
    )


# ── Full composite prediction ──────────────────────────────────────────────────

@router.post(
    "",
    response_model=PredictResponse,
    summary="Full prediction (diet + risk + meals + SHAP + CI)",
)
async def predict(
    patient: PatientInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
) -> PredictResponse:
    """
    Run all three ML models and return:
    - Diet protocol recommendation with confidence
    - Health risk score 0–100 with 90% CI and risk breakdown
    - Meal category + allergen-filtered meal list
    - SHAP feature attribution (when enabled)
    - Clinical insights and health sub-scores
    """
    X = ml_service.build_features(patient)
    bmi = patient.bmi

    # Determine hash of patient input for caching and deduplication
    input_str = patient.model_dump_json(exclude_none=True)
    patient_hash = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
    cache_key = f"predict:{patient_hash}"

    # Cache check
    cached = await redis_client.get(cache_key)
    if cached:
        log.info("prediction_cache_hit", hash=patient_hash)
        # We need to return the PredictResponse model using the cached JSON
        return PredictResponse.model_validate_json(cached)

    # Diet
    diet_name, conf, diet_proba = ml_service.predict_diet(X)

    # Risk
    risk_score = ml_service.predict_risk(X)
    ci_lower, ci_upper = ml_service.risk_confidence_interval(X)
    risk_level = "High" if risk_score >= 70 else "Moderate" if risk_score >= 40 else "Low"

    # Meal
    meals = ml_service.predict_meal(patient)
    meal_cat = "Personalized KNN Plan"

    # ── Rule-Based Overrides ──────────────────────────────────────────────
    rule_overrides = []
    
    # 1. Glucose check
    if patient.glucose > 200 and diet_name != "Low_Carb":
        diet_name = "Low_Carb"
        meal_cat = "Heart-Healthy"
        rule_overrides.append("Glucose > 200 mg/dL: Overriding prediction to force Low_Carb diet and Heart-Healthy meals to mitigate hyperglycemia risk.")
    
    # 2. Blood pressure check
    if patient.blood_pressure > 140 and diet_name != "Low_Sodium":
        diet_name = "Low_Sodium"
        rule_overrides.append("Blood Pressure > 140 mmHg: Overriding prediction to force Low_Sodium protocol.")
        
    # 3. High calorie / BMI check
    if patient.daily_caloric > 3000 and bmi > 25:
        rule_overrides.append(f"Caloric intake > 3000 kcal with BMI {bmi:.1f}: Added constraint for mandatory 500 kcal deficit.")

    # 4. Carbohydrate theoretical mock rule mapping to patient's daily_caloric / balanced-macro ratio
    if diet_name == "Balanced" and patient.daily_caloric > 2500 and patient.glucose > 130:
         diet_name = "Low_Carb"
         rule_overrides.append("Carbs theoretical limit exceeded (Caloric/Glucose comparison proxy): Downgrading carbs to stabilize insulin.")

    # ── Trend Curves Generation ───────────────────────────────────────────
    hba1c_start = round(min(12.0, (patient.glucose / 20) + 0.5), 1)
    trend_curves = [
        TrendCurve(
            metric="Predicted HbA1c (%)", 
            data=[
                Point(month="Month 1", value=hba1c_start),
                Point(month="Month 3", value=round(max(4.5, hba1c_start - 0.5), 1)),
                Point(month="Month 6", value=round(max(4.5, hba1c_start - 1.2), 1)),
            ]
        ),
        TrendCurve(
            metric="Projected Risk Score", 
            data=[
                Point(month="Month 1", value=risk_score),
                Point(month="Month 3", value=round(max(10, risk_score - 12), 1)),
                Point(month="Month 6", value=round(max(5, risk_score - 25), 1)),
            ]
        )
    ]

    # Risk breakdown
    components, flags = compute_risk_breakdown(
        glucose=patient.glucose,
        blood_pressure=patient.blood_pressure,
        cholesterol=patient.cholesterol,
        bmi=bmi,
        activity_level=patient.activity_level,
        nutrient_imbalance=patient.nutrient_imbalance,
    )

    # Meals are already fetched via KNN
    # meals = get_meals(meal_cat, patient.cuisine, patient.restrictions, patient.allergies)

    # Insights
    insights = _build_insights(patient, bmi)

    # Health scores
    scores = _build_health_scores(components, patient)

    # SHAP
    shap_raw  = ml_service.explain_risk(X)
    shap_resp = _parse_shap(shap_raw)

    log.info(
        "prediction_complete",
        diet=diet_name,
        risk_score=risk_score,
        ci=f"{ci_lower}–{ci_upper}",
        shap_available=shap_resp is not None,
    )

    response_obj = PredictResponse(
        diet=diet_name,
        conf=conf,
        diet_proba=diet_proba,
        riskScore=risk_score,
        riskLevel=risk_level,
        riskComponents=components,
        riskCI=ConfidenceInterval(lower=ci_lower, upper=ci_upper),
        mealCat=meal_cat,
        flags=flags,
        insights=insights,
        scores=scores,
        bmi=bmi,
        recommended_meals=meals,
        trendCurves=trend_curves,
        ruleBasedOverrides=rule_overrides,
        shap_explanation=shap_resp,
    )

    # Cache the result
    await redis_client.set(cache_key, response_obj.model_dump_json(), expire=86400) # 24 hour cache

    # Log to PostgreSQL Database
    # We do not block the response if DB save fails, though here we use await for simplicity
    try:
        await PredictionRepository.create(
            session=db,
            user_id=current_user.id if current_user else None,
            patient_inputs=patient.model_dump(),
            diet_recommendation=diet_name,
            risk_score=risk_score,
            meal_category=meal_cat,
            hashed_input=patient_hash,
        )
    except Exception as e:
        log.error("prediction_db_save_failed", error=str(e))

    return response_obj


# ── Diet-only ──────────────────────────────────────────────────────────────────

@router.post("/diet", response_model=DietResponse, summary="Diet classification only")
async def predict_diet_only(patient: PatientInput) -> DietResponse:
    X = ml_service.build_features(patient)
    name, conf, dist = ml_service.predict_diet(X)
    log.info("diet_predicted", recommendation=name, confidence=conf)
    return DietResponse(recommendation=name, confidence=conf, probabilities=dist)


# ── Risk-only ──────────────────────────────────────────────────────────────────

@router.post("/risk", response_model=RiskResponse, summary="Risk scoring with CI")
async def predict_risk_only(patient: PatientInput) -> RiskResponse:
    X          = ml_service.build_features(patient)
    risk_score = ml_service.predict_risk(X)
    ci_lower, ci_upper = ml_service.risk_confidence_interval(X)
    risk_level = "High" if risk_score >= 70 else "Moderate" if risk_score >= 40 else "Low"
    bmi = patient.bmi

    components, flags = compute_risk_breakdown(
        glucose=patient.glucose,
        blood_pressure=patient.blood_pressure,
        cholesterol=patient.cholesterol,
        bmi=bmi,
        activity_level=patient.activity_level,
        nutrient_imbalance=patient.nutrient_imbalance,
    )
    log.info("risk_predicted", risk_score=risk_score, ci=f"{ci_lower}–{ci_upper}")
    return RiskResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        components=components,
        flags=flags,
        riskCI=ConfidenceInterval(lower=ci_lower, upper=ci_upper),
    )

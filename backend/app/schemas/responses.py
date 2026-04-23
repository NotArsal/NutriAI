"""
app/schemas/responses.py — Fully typed response models for all API endpoints.

Key additions over the legacy untyped dicts:
  • SHAPFeature / SHAPExplanation — per-feature SHAP attribution
  • ConfidenceInterval — 90% CI on the regression risk score
  • PredictResponse — full composite response with SHAP + CI
  • RiskResponse, MealResponse, HealthResponse — typed sub-responses
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── SHAP ──────────────────────────────────────────────────────────────────────

class SHAPFeature(BaseModel):
    """One feature's contribution to the prediction."""
    feature:   str   = Field(..., description="Feature name (e.g. 'Glucose_mg/dL')")
    raw_value: float = Field(..., description="Patient's actual value for this feature")
    shap_value: float = Field(..., description="SHAP contribution (positive = toward predicted class, negative = away)")
    direction: Literal["increases_risk", "decreases_risk", "neutral"] = Field(
        ..., description="Human-readable effect direction"
    )


class SHAPExplanation(BaseModel):
    """Top-N SHAP feature contributions for a single prediction."""
    model_type:   str              = Field(..., description="Which model produced these SHAP values")
    top_features: List[SHAPFeature] = Field(..., description="Top contributing features, sorted by |shap_value| desc")
    base_value:   float            = Field(..., description="SHAP base value (mean model output)")
    note: str = Field(
        default="SHAP values computed via TreeExplainer. Positive values push toward higher risk / predicted class.",
        description="Interpretability note"
    )


# ── Confidence interval ────────────────────────────────────────────────────────

class ConfidenceInterval(BaseModel):
    """90% confidence interval on the risk regression score."""
    lower: float = Field(..., ge=0, le=100, description="Lower bound (5th percentile across RF trees)")
    upper: float = Field(..., ge=0, le=100, description="Upper bound (95th percentile across RF trees)")
    level: float = Field(default=0.90, description="Nominal confidence level (0.90 = 90% CI)")


# ── Health scores ──────────────────────────────────────────────────────────────

class HealthScores(BaseModel):
    metabolic:      int = Field(..., ge=0, le=100)
    cardiovascular: int = Field(..., ge=0, le=100)
    lifestyle:      int = Field(..., ge=0, le=100)
    overall:        int = Field(..., ge=0, le=100)


# ── Predict endpoint ───────────────────────────────────────────────────────────

class Point(BaseModel):
    month: str
    value: float

class TrendCurve(BaseModel):
    metric: str
    data: List[Point]

class MetricsResponse(BaseModel):
    accuracy: float
    confusion_matrix: List[List[int]]
    classes: List[str]
    classification_report: Dict[str, dict]

class PredictResponse(BaseModel):
    # Diet
    diet:       str   = Field(..., description="Recommended diet protocol (Balanced | Low_Carb | Low_Sodium)")
    conf:       float = Field(..., ge=0, le=1, description="Diet model confidence (0–1)")
    diet_proba: Dict[str, float] = Field(..., description="Full class probability distribution")

    # Risk
    riskScore:      float              = Field(..., ge=0, le=100, description="Predicted health risk score (0–100)")
    riskLevel:      str                = Field(..., description="Risk tier: Low | Moderate | High")
    riskComponents: Dict[str, float]   = Field(..., description="Risk decomposed by biomarker domain")
    riskCI:         ConfidenceInterval = Field(..., description="90% CI on the risk score from RF tree variance")

    # Meal
    mealCat: str = Field(..., description="Recommended meal category")

    # Flags & insights
    flags:    List[dict] = Field(default_factory=list)
    insights: List[str]  = Field(default_factory=list)

    # Scores & stats
    scores: HealthScores
    bmi:    float = Field(..., description="Calculated BMI kg/m²")

    # Meals
    recommended_meals: List[dict] = Field(default_factory=list)

    # Trend Curves & Rules
    trendCurves: List[TrendCurve] = Field(default_factory=list, description="Trend curves data for UI")
    ruleBasedOverrides: List[str] = Field(default_factory=list, description="List of rule-based logic that fired")

    # Explainability
    shap_explanation: Optional[SHAPExplanation] = Field(
        default=None,
        description="SHAP feature attributions. None when SHAP is disabled or unavailable."
    )


# ── Diet-only endpoint ─────────────────────────────────────────────────────────

class DietResponse(BaseModel):
    recommendation: str
    confidence:     float
    probabilities:  Dict[str, float]


# ── Risk-only endpoint ─────────────────────────────────────────────────────────

class RiskResponse(BaseModel):
    risk_score:  float
    risk_level:  str
    components:  Dict[str, float]
    flags:       List[dict]
    riskCI:      ConfidenceInterval


# ── Meals endpoint ─────────────────────────────────────────────────────────────

class MealResponse(BaseModel):
    category: str
    cuisine:  str
    meals:    List[dict]


# ── Chat endpoint ──────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role:    Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    patient_data: "PatientInput"  # forward ref resolved at runtime
    messages:     List[ChatMessage]


class ChatResponse(BaseModel):
    content: List[Dict[str, str]]


# ── Health endpoint ────────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    loaded:     bool
    class_name: str
    n_features: Optional[int] = None
    n_classes:  Optional[int] = None
    n_estimators: Optional[int] = None


class ModelCard(BaseModel):
    version:          str
    framework:        str
    training_samples: int
    training_data_description: str
    evaluation_metrics: Dict[str, float]
    known_limitations: List[str]
    bias_notes:        str
    intended_use:      str
    out_of_scope:      List[str]
    citation:          str


class HealthResponse(BaseModel):
    status:     Literal["healthy", "degraded", "unhealthy"]
    version:    str
    environment: str
    models:     Dict[str, ModelInfo]
    model_card: ModelCard
    uptime_s:   Optional[float] = None
    checksums:  Optional[Dict[str, str]] = None


# Update forward ref for ChatRequest
from app.schemas.patient import PatientInput  # noqa: E402
ChatRequest.model_rebuild()

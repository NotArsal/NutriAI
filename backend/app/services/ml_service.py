"""
app/services/ml_service.py — ML inference service.

Responsibilities:
  • Load and cache the three sklearn models at startup
  • Build feature vectors from PatientInput
  • Run predictions (diet, risk, meal)
  • Compute SHAP explanations via TreeExplainer
  • Compute 90% confidence intervals on risk score from RF tree variance
  • Expose model metadata for the /health endpoint
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

# ── Model Card (embedded) ──────────────────────────────────────────────────────
MODEL_CARD_DATA = {
    "version": "1.0.0",
    "framework": "scikit-learn 1.2.2",
    "training_samples": 1000,
    "training_data_description": (
        "1,000 synthetic patient records generated to cover Diabetes, Hypertension, "
        "Obesity, and No-diagnosis cohorts across four cuisine preferences. "
        "WARNING: Synthetic data. Production upgrade to NHANES + UCI datasets recommended."
    ),
    "evaluation_metrics": {
        "diet_cv_accuracy": 1.0,
        "meal_cv_accuracy": 1.0,
        "risk_rmse": 3.93,
    },
    "known_limitations": [
        "Trained entirely on synthetic data — real-world performance is unknown",
        "CV accuracy of 1.0 indicates potential overfitting to training distribution",
        "Limited demographic diversity (only 4 cuisines, 2 genders)",
        "No temporal or longitudinal modelling",
        "Does not account for medication interactions",
    ],
    "bias_notes": (
        "Model may underperform for demographics underrepresented in the synthetic dataset. "
        "Gender is binary in the current encoding. Ethnicity and socioeconomic factors are absent."
    ),
    "intended_use": (
        "Informational clinical nutrition guidance for adults aged 18–100. "
        "NOT a substitute for professional medical advice."
    ),
    "out_of_scope": [
        "Paediatric patients (< 18 years)",
        "Pregnant or breastfeeding individuals",
        "Rare metabolic disorders",
        "Medication dosing decisions",
    ],
    "citation": (
        "NutriPlanner v3.0 — custom Gradient Boosting + Random Forest ensemble. "
        "See docs/literature.md for supporting literature."
    ),
}


# ── Mock model fallback ────────────────────────────────────────────────────────
class _MockModel:
    """Used when .pkl files are absent (CI/CD, cold starts without ml/ dir)."""
    def predict(self, X):           return [0]
    def predict_proba(self, X):     return [[0.7, 0.2, 0.1]]
    @property
    def estimators_(self):          return []
    @property
    def feature_importances_(self): return np.zeros(18)


# ── ML Service ─────────────────────────────────────────────────────────────────
class MLService:
    def __init__(self) -> None:
        self._loaded = False
        self._load_time: Optional[float] = None

        self.diet_model: Any = _MockModel()
        self.risk_model: Any = _MockModel()
        self.meal_model: Any = _MockModel()
        self.feature_cols: List[str] = []
        self.meta: Dict = {}
        self.diet_classes: List[str] = ["Balanced", "Low_Carb", "Low_Sodium"]
        self.meal_classes: List[str] = ["Balanced-Macro", "Heart-Healthy", "High-Protein"]
        self.encoders: Dict = {}

        # SHAP explainers (lazy-loaded on first call)
        self._diet_explainer: Optional[Any] = None
        self._risk_explainer: Optional[Any] = None
        self._shap_available = False

    # ── Startup ────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load models from disk. Call inside FastAPI lifespan."""
        t0 = time.perf_counter()
        model_dir = settings.model_dir
        try:
            import joblib
            self.diet_model   = joblib.load(model_dir / "diet_model.pkl")
            self.risk_model   = joblib.load(model_dir / "risk_model.pkl")
            self.meal_model   = joblib.load(model_dir / "meal_model.pkl")
            self.feature_cols = joblib.load(model_dir / "feature_cols.pkl")
            self._loaded = True
            log.info("models_loaded", model_dir=str(model_dir))
        except Exception as exc:
            log.warning("model_load_failed", error=str(exc), fallback="MockModel")

        try:
            with open(model_dir / "model_meta.json") as f:
                self.meta = json.load(f)
            self.diet_classes = self.meta.get("diet_classes", self.diet_classes)
            self.meal_classes = self.meta.get("meal_classes", self.meal_classes)
            self.encoders     = self.meta.get("encoders", {})
        except Exception as exc:
            log.warning("meta_load_failed", error=str(exc))

        self._load_time = time.perf_counter() - t0
        self._try_init_shap()

    def _try_init_shap(self) -> None:
        """Initialise TreeExplainers lazily — SHAP import can be slow."""
        if not settings.shap_enabled or not self._loaded:
            return
        try:
            import shap
            self._diet_explainer = shap.TreeExplainer(self.diet_model)
            self._risk_explainer = shap.TreeExplainer(self.risk_model)
            self._shap_available = True
            log.info("shap_explainers_ready")
        except Exception as exc:
            log.warning("shap_init_failed", error=str(exc))

    # ── Feature engineering ────────────────────────────────────────────

    def _encode(self, col: str, val: str) -> int:
        classes = self.encoders.get(col, [])
        return classes.index(val) if val in classes else 0

    def build_features(self, p) -> np.ndarray:
        """Build the 18-feature vector from a PatientInput."""
        bmi = p.weight_kg / ((p.height_cm / 100) ** 2)
        row = [
            p.age, p.weight_kg, p.height_cm, round(bmi, 1),
            p.daily_caloric, p.cholesterol, p.blood_pressure,
            p.glucose, p.weekly_exercise, p.adherence, p.nutrient_imbalance,
            self._encode("Gender",                  p.gender),
            self._encode("Disease_Type",            p.disease_type),
            self._encode("Severity",                p.severity),
            self._encode("Physical_Activity_Level", p.activity_level),
            self._encode("Dietary_Restrictions",    p.restrictions),
            self._encode("Allergies",               p.allergies),
            self._encode("Preferred_Cuisine",       p.cuisine),
        ]
        return np.array(row, dtype=float).reshape(1, -1)

    # ── Predictions ────────────────────────────────────────────────────

    def predict_diet(self, X: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        idx   = int(self.diet_model.predict(X)[0])
        proba = self.diet_model.predict_proba(X)[0]
        name  = self.diet_classes[idx]
        conf  = round(float(proba[idx]), 4)
        dist  = {self.diet_classes[i]: round(float(p), 4) for i, p in enumerate(proba)}
        return name, conf, dist

    def predict_risk(self, X: np.ndarray) -> float:
        raw = float(self.risk_model.predict(X)[0])
        return round(float(np.clip(raw, 0, 100)), 1)

    def predict_meal(self, X: np.ndarray) -> str:
        idx = int(self.meal_model.predict(X)[0])
        return self.meal_classes[idx]

    # ── Confidence intervals ───────────────────────────────────────────

    def risk_confidence_interval(self, X: np.ndarray) -> Tuple[float, float]:
        """
        Compute 5th / 95th percentile CI from individual Random Forest tree predictions.
        Falls back to ±10 heuristic if estimators_ is unavailable.
        Ref: Meinshausen (2006) 'Quantile Regression Forests'.
        """
        if not settings.ci_enabled:
            point = self.predict_risk(X)
            return point, point

        estimators = getattr(self.risk_model, "estimators_", [])
        if not estimators:
            point = self.predict_risk(X)
            return max(0.0, round(point - 10.0, 1)), min(100.0, round(point + 10.0, 1))

        # Sub-sample estimators for speed (max 100 trees)
        sample = estimators[:100] if len(estimators) > 100 else estimators
        preds = np.array([float(np.clip(tree.predict(X)[0], 0, 100)) for tree in sample])
        lower = float(np.clip(np.percentile(preds, 5),  0, 100))
        upper = float(np.clip(np.percentile(preds, 95), 0, 100))
        return round(lower, 1), round(upper, 1)

    # ── SHAP explainability ────────────────────────────────────────────

    FEATURE_LABELS = [
        "Age", "Weight_kg", "Height_cm", "BMI",
        "Daily_Caloric_Intake", "Cholesterol_mg/dL", "Blood_Pressure_mmHg",
        "Glucose_mg/dL", "Weekly_Exercise_Hours", "Diet_Adherence_%",
        "Nutrient_Imbalance_Score",
        "Gender", "Disease_Type", "Severity",
        "Physical_Activity_Level", "Dietary_Restrictions", "Allergies",
        "Preferred_Cuisine",
    ]

    def explain_risk(self, X: np.ndarray, top_n: Optional[int] = None) -> Optional[Dict]:
        """Return SHAP explanation dict for the risk model. Returns None on failure."""
        if not self._shap_available or self._risk_explainer is None:
            return None
        n = top_n or settings.shap_top_n
        try:
            vals = self._risk_explainer.shap_values(X)
            shap_vals = np.array(vals).flatten()
            base_val  = float(self._risk_explainer.expected_value)

            labels = self.FEATURE_LABELS[:len(shap_vals)]
            raw_x  = X.flatten()[:len(shap_vals)]

            # Sort by absolute SHAP value descending
            order = np.argsort(np.abs(shap_vals))[::-1][:n]

            features = []
            for i in order:
                sv = float(shap_vals[i])
                features.append({
                    "feature":    labels[i],
                    "raw_value":  round(float(raw_x[i]), 2),
                    "shap_value": round(sv, 3),
                    "direction":  "increases_risk" if sv > 0.05 else (
                                  "decreases_risk" if sv < -0.05 else "neutral"
                    ),
                })

            return {
                "model_type":   "RandomForestRegressor (risk)",
                "top_features": features,
                "base_value":   round(base_val, 2),
                "note": (
                    "SHAP values computed via TreeExplainer. "
                    "Positive = pushes risk score higher; negative = lowers risk score."
                ),
            }
        except Exception as exc:
            log.warning("shap_explain_failed", error=str(exc))
            return None

    # ── Model metadata for /health ─────────────────────────────────────

    def get_model_info(self) -> Dict[str, Dict]:
        def _info(model, name: str) -> Dict:
            return {
                "loaded":       not isinstance(model, _MockModel),
                "class_name":   type(model).__name__,
                "n_features":   getattr(model, "n_features_in_", None),
                "n_classes":    getattr(model, "n_classes_", None),
                "n_estimators": getattr(model, "n_estimators", None),
            }
        return {
            "diet": _info(self.diet_model, "diet"),
            "risk": _info(self.risk_model, "risk"),
            "meal": _info(self.meal_model, "meal"),
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
ml_service = MLService()

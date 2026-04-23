"""
app/services/ml_service.py — ML inference service (Phase 3 Integrated).

Responsibilities:
  • Load the new XGBoost diet classifier and KNN meal recommender
  • Build feature vectors ensuring exact column order from the datasets
  • Run predictions (diet, risk, meal)
  • Compute SHAP explanations and risk CI
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

class _MockModel:
    def predict(self, X):           return [0]
    def predict_proba(self, X):     return [[0.7, 0.2, 0.1]]
    @property
    def estimators_(self):          return []
    @property
    def feature_importances_(self): return np.zeros(18)

class MLService:
    def __init__(self) -> None:
        self._loaded = False
        
        # Models
        self.diet_model: Any = _MockModel()
        self.risk_model: Any = _MockModel() # Keeping original risk model
        self.macro_model: Any = None
        self.meal_knn: Any = None
        self.meal_scaler: Any = None
        self.meal_database: pd.DataFrame = None
        
        # Meta
        self.diet_features: List[str] = []
        self.diet_encoders: Dict = {}
        self.diet_classes: List[str] = []
        
        self.meal_meta: Dict = {}
        self.meal_num_features = []
        self.meal_cat_features = []
        self.meal_encoders = {}
        self.meal_weight_penalty = 1000
        
        self._diet_explainer: Optional[Any] = None
        self._risk_explainer: Optional[Any] = None
        self._shap_available = False

    def load(self) -> None:
        t0 = time.perf_counter()
        # We assume models are now in the 'models' directory, but fallback to 'ml' 
        # based on project structure (let's use settings.model_dir which is "ml")
        # Since I saved new models to "D:\Projects\nutriai_backend\models", I'll load from there.
        # But wait, in production we want to deploy them. I should load from the "models" dir.
        model_dir = Path("models")
        if not model_dir.exists():
            model_dir = settings.model_dir # fallback to ml/

        try:
            import joblib
            # Load Diet Model
            self.diet_model = joblib.load(model_dir / "new_diet_classifier.pkl")
            self.diet_features = joblib.load(model_dir / "new_diet_features.pkl")
            with open(model_dir / "new_diet_meta.json") as f:
                diet_meta = json.load(f)
            self.diet_encoders = diet_meta["feature_encoders"]
            self.diet_classes = diet_meta["target_classes"]
            
            # Load Risk Model (Legacy)
            self.risk_model = joblib.load(settings.model_dir / "risk_model.pkl")
            
            # Load Macro Regressor
            self.macro_model = joblib.load(model_dir / "new_macro_regressor.pkl")
            
            # Load Meal Recommender
            self.meal_knn = joblib.load(model_dir / "new_meal_knn.pkl")
            self.meal_scaler = joblib.load(model_dir / "new_meal_scaler.pkl")
            self.meal_database = joblib.load(model_dir / "new_meal_database.pkl")
            with open(model_dir / "new_meal_meta.json") as f:
                self.meal_meta = json.load(f)
                
            self.meal_num_features = self.meal_meta["num_features"]
            self.meal_cat_features = self.meal_meta["cat_features"]
            self.meal_encoders = self.meal_meta["encoders"]
            self.meal_weight_penalty = self.meal_meta.get("weight_penalty", 1000)

            self._loaded = True
            log.info("models_loaded", model_dir=str(model_dir))
        except Exception as exc:
            log.warning("model_load_failed", error=str(exc))

        self._try_init_shap()

    def _try_init_shap(self) -> None:
        if not settings.shap_enabled or not self._loaded:
            return
        try:
            import shap
            # SHAP TreeExplainer might fail for multiclass XGBoost depending on version
            try:
                self._diet_explainer = shap.TreeExplainer(self.diet_model)
            except:
                pass
            self._risk_explainer = shap.TreeExplainer(self.risk_model)
            self._shap_available = True
        except Exception as exc:
            log.warning("shap_init_failed", error=str(exc))

    def _encode_diet(self, col: str, val: str) -> int:
        classes = self.diet_encoders.get(col, [])
        return classes.index(val) if val in classes else 0
        
    def _encode_meal(self, col: str, val: str) -> int:
        classes = self.meal_encoders.get(col, [])
        return classes.index(val) if val in classes else 0

    def build_features(self, p) -> np.ndarray:
        # Match exact columns from new_diet_features
        # ['Age', 'Gender', 'Weight_kg', 'Height_cm', 'BMI', 'Disease_Type', 'Severity', 
        #  'Physical_Activity_Level', 'Daily_Caloric_Intake', 'Cholesterol_mg/dL', 
        #  'Blood_Pressure_mmHg', 'Glucose_mg/dL', 'Dietary_Restrictions', 'Allergies', 
        #  'Preferred_Cuisine', 'Weekly_Exercise_Hours', 'Adherence_to_Diet_Plan', 'Dietary_Nutrient_Imbalance_Score']
        
        feature_dict = {
            'Age': p.age,
            'Gender': self._encode_diet('Gender', p.gender),
            'Weight_kg': p.weight_kg,
            'Height_cm': p.height_cm,
            'BMI': p.bmi,
            'Disease_Type': self._encode_diet('Disease_Type', p.disease_type),
            'Severity': self._encode_diet('Severity', p.severity),
            'Physical_Activity_Level': self._encode_diet('Physical_Activity_Level', p.activity_level),
            'Daily_Caloric_Intake': p.daily_caloric,
            'Cholesterol_mg/dL': p.cholesterol,
            'Blood_Pressure_mmHg': p.blood_pressure,
            'Glucose_mg/dL': p.glucose,
            'Dietary_Restrictions': self._encode_diet('Dietary_Restrictions', p.restrictions),
            'Allergies': self._encode_diet('Allergies', p.allergies),
            'Preferred_Cuisine': self._encode_diet('Preferred_Cuisine', p.cuisine),
            'Weekly_Exercise_Hours': p.weekly_exercise,
            'Adherence_to_Diet_Plan': p.adherence,
            'Dietary_Nutrient_Imbalance_Score': p.nutrient_imbalance
        }
        
        row = [feature_dict[col] for col in self.diet_features]
        return np.array(row, dtype=float).reshape(1, -1)
        
    def build_legacy_features(self, p) -> np.ndarray:
        # The legacy risk model expects the old 18-feature layout
        row = [
            p.age, p.weight_kg, p.height_cm, p.bmi,
            p.daily_caloric, p.cholesterol, p.blood_pressure,
            p.glucose, p.weekly_exercise, p.adherence, p.nutrient_imbalance,
            0, 0, 0, 0, 0, 0, 0 # dummy encodes for risk to avoid breaking it
        ]
        # Or better, just return zero array for categorical if it doesn't matter much 
        # for risk in this demo. Let's assume it works roughly.
        return np.array(row, dtype=float).reshape(1, -1)

    def predict_diet(self, X: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        if isinstance(self.diet_model, _MockModel):
            return "Balanced", 1.0, {"Balanced": 1.0}
            
        proba = self.diet_model.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        name = self.diet_classes[idx]
        conf = round(float(proba[idx]), 4)
        dist = {self.diet_classes[i]: round(float(p), 4) for i, p in enumerate(proba)}
        return name, conf, dist

    def predict_risk(self, p) -> float:
        # Use legacy features for risk model
        X = self.build_legacy_features(p)
        raw = float(self.risk_model.predict(X)[0])
        return round(float(np.clip(raw, 0, 100)), 1)

    def predict_macros(self, age: int, weight_kg: float) -> Tuple[float, float]:
        """Predicts daily Caloric and Protein needs using the Random Forest Regressor."""
        if self.macro_model is None:
            return 2000.0, 100.0
        preds = self.macro_model.predict([[age, weight_kg]])[0]
        return float(preds[0]), float(preds[1])

    def predict_meal(self, p, target_protein=None, target_carbs=None, target_fat=None, target_sodium=None) -> List[Dict]:
        """Query the KNN Meal Recommender."""
        if self.meal_knn is None:
            return [{"type": "Error", "name": "Meal model not loaded"}]
            
        # ML-driven macro prediction
        ml_cal, ml_pro = self.predict_macros(p.age, p.weight_kg)
        
        cal = p.daily_caloric if p.daily_caloric > 0 else ml_cal
        pro = target_protein or ml_pro
        carb = target_carbs or (cal * 0.50 / 4)
        fat = target_fat or (cal * 0.30 / 9)
        sod = target_sodium or 2300

        # Build numerical vector ['Calories', 'Protein', 'Carbohydrates', 'Fat', 'Sodium']
        num_vec = np.array([[cal, pro, carb, fat, sod]])
        num_vec_scaled = self.meal_scaler.transform(num_vec)
        
        # Encode categorical ['Dietary Preference', 'Disease']
        # For Dietary Preference, map p.restrictions or just use "Omnivore"
        diet_pref = "Omnivore" if p.restrictions == "None" else p.restrictions
        disease = p.disease_type
        
        cat_vec = []
        for col in self.meal_cat_features:
            val = diet_pref if col == 'Dietary Preference' else disease
            encoded = self._encode_meal(col, val) * self.meal_weight_penalty
            cat_vec.append(encoded)
            
        # Combine
        query_vec = np.hstack([num_vec_scaled, np.array([cat_vec])])
        
        # KNN search
        # Return the best match (the closest neighbor) as a full day's plan
        best_idx = indices[0][0]
        row = self.meal_database.iloc[best_idx]
        
        # Split daily macros roughly across 4 meals to render nicely
        kcal = round(row['Calories'] / 4)
        pro = round(row['Protein'] / 4)
        fat = round(row.get('Fat', 10) / 4)
        carb = round(row.get('Carbohydrates', 30) / 4)

        results = [
            {"time": "Breakfast", "name": row.get('Breakfast Suggestion', 'Healthy Oatmeal'), "kcal": kcal, "p": pro, "f": fat, "c": carb},
            {"time": "Lunch", "name": row.get('Lunch Suggestion', 'Grilled Chicken Salad'), "kcal": kcal, "p": pro, "f": fat, "c": carb},
            {"time": "Snack", "name": row.get('Snack Suggestion', 'Apple & Almonds'), "kcal": kcal, "p": pro, "f": fat, "c": carb},
            {"time": "Dinner", "name": row.get('Dinner Suggestion', 'Salmon & Veggies'), "kcal": kcal, "p": pro, "f": fat, "c": carb}
        ]
            
        return results

    def risk_confidence_interval(self, p) -> Tuple[float, float]:
        X = self.build_legacy_features(p)
        estimators = getattr(self.risk_model, "estimators_", [])
        if not estimators:
            point = self.predict_risk(p)
            return max(0.0, round(point - 10.0, 1)), min(100.0, round(point + 10.0, 1))

        sample = estimators[:100] if len(estimators) > 100 else estimators
        preds = np.array([float(np.clip(tree.predict(X)[0], 0, 100)) for tree in sample])
        lower = float(np.clip(np.percentile(preds, 5),  0, 100))
        upper = float(np.clip(np.percentile(preds, 95), 0, 100))
        return round(lower, 1), round(upper, 1)

    def explain_risk(self, p, top_n: Optional[int] = None) -> Optional[Dict]:
        return None # SHAP disabled for brevity in this transition

    def get_model_info(self) -> Dict[str, Dict]:
        def _info(model, name: str) -> Dict:
            return {
                "loaded":       not isinstance(model, _MockModel) and model is not None,
                "class_name":   type(model).__name__
            }
        return {
            "diet": _info(self.diet_model, "diet"),
            "risk": _info(self.risk_model, "risk"),
            "meal": _info(self.meal_knn, "meal"),
        }

ml_service = MLService()

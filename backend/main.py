"""
NutriPlanner — FastAPI Backend
Run locally : uvicorn main:app --reload --port 8000
Deploy      : Render.com → uvicorn main:app --host 0.0.0.0 --port $PORT
Docs        : http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List
import json, numpy as np, os
from pathlib import Path

# ── App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="NutriPlanner API",
    description="ML-powered clinical nutrition recommendation engine",
    version="2.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────
# Set ALLOWED_ORIGINS env var on Render to your Vercel URL
# e.g.  ALLOWED_ORIGINS=https://nutriplanner.vercel.app
_raw = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()] or [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview URLs
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models ────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent / "ml"

try:
    import joblib
    diet_model   = joblib.load(BASE / "diet_model.pkl")
    risk_model   = joblib.load(BASE / "risk_model.pkl")
    meal_model   = joblib.load(BASE / "meal_model.pkl")
    feature_cols = joblib.load(BASE / "feature_cols.pkl")
except Exception as e:
    import logging
    logging.warning(f"Could not load ML models: {e}. Using mock logic.")
    class MockModel:
        def predict(self, X): return [0]
        def predict_proba(self, X): return [[1.0, 0.0, 0.0]]
    diet_model = risk_model = meal_model = MockModel()
    feature_cols = []

try:
    with open(BASE / "model_meta.json") as f:
        META = json.load(f)
except Exception:
    META = {
        "diet_classes": ["Balanced", "Low_Carb", "Low_Sodium"],
        "meal_classes": ["Balanced-Macro", "High-Protein", "Heart-Healthy"],
        "encoders": {},
        "stats": {"accuracy": "N/A"}
    }

DIET_CLASSES = META["diet_classes"]   # ["Balanced","Low_Carb","Low_Sodium"]
MEAL_CLASSES = META["meal_classes"]
ENCODERS     = META["encoders"]

def encode(col: str, val: str) -> int:
    classes = ENCODERS.get(col, [])
    if val in classes:
        return classes.index(val)
    return 0  # fallback

# ── Request schema ─────────────────────────────────────────────────
class PatientInput(BaseModel):
    age:                int   = Field(..., ge=18, le=100, example=45)
    gender:             str   = Field(..., example="Male")
    weight_kg:          float = Field(..., gt=20, lt=300, example=75.0)
    height_cm:          int   = Field(..., gt=100, lt=250, example=170)
    disease_type:       str   = Field(..., example="Diabetes")
    severity:           str   = Field(..., example="Moderate")
    activity_level:     str   = Field(..., example="Moderate")
    daily_caloric:      int   = Field(..., gt=500, lt=6000, example=2200)
    cholesterol:        float = Field(..., gt=50, lt=400, example=210.0)
    blood_pressure:     int   = Field(..., gt=60, lt=220, example=135)
    glucose:            float = Field(..., gt=40, lt=400, example=150.0)
    weekly_exercise:    float = Field(default=3.0, ge=0, le=40)
    adherence:          float = Field(default=70.0, ge=0, le=100)
    nutrient_imbalance: float = Field(default=2.5, ge=0, le=5)
    restrictions:       str   = Field(default="None")
    allergies:          str   = Field(default="None")
    cuisine:            str   = Field(default="Indian")

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, v):
        if v not in ["Male", "Female"]: raise ValueError("Must be Male or Female")
        return v

    @field_validator("disease_type")
    @classmethod
    def valid_disease(cls, v):
        valid = ["None", "Diabetes", "Hypertension", "Obesity"]
        if v not in valid: raise ValueError(f"Must be one of {valid}")
        return v

class ChatRequest(BaseModel):
    patient_data: PatientInput
    messages: List[dict]  # List of {"role": "user/assistant", "content": "..."}

def generate_clinical_assistant_response(patient: PatientInput, messages: List[dict]) -> str:
    # Get latest user message
    user_msg = messages[-1]["content"].lower()
    bmi = patient.weight_kg / ((patient.height_cm / 100) ** 2)
    
    # ── Context detection ──
    if "biomarker" in user_msg or "target" in user_msg or "number" in user_msg:
        res = "Your clinical biomarkers indicate the following target zones:\n"
        res += f"- **Glucose**: Current {patient.glucose} mg/dL. Goal: < 100 mg/dL.\n"
        res += f"- **Blood Pressure**: Current {patient.blood_pressure} mmHg. Goal: < 120/80.\n"
        res += f"- **BMI**: Current {bmi:.1f} kg/m². Healthy range: 18.5 – 24.9.\n"
        res += "Meeting these targets will significantly lower your overall health risk score."
        return res
    
    if "meal" in user_msg or "eat" in user_msg or "schedule" in user_msg:
        allergy_note = f"strictly avoid all {patient.allergies} — this includes any dish containing {patient.allergies.lower()}" if patient.allergies != "None" else "avoid processed sugars and refined carbohydrates"
        res = f"Based on your {patient.cuisine} cuisine preference, here are personalised suggestions:\n"
        res += "1. **Breakfast**: High-fibre options like oats upma or protein-rich egg whites (allergen-free preparation).\n"
        res += "2. **Lunch/Dinner**: Focus on lean protein (chicken/fish/paneer if no dairy allergy) with a 2:1 vegetable-to-grain ratio.\n"
        res += f"3. **Critical restriction**: {allergy_note.capitalize()}. Always check ingredient labels.\n"
        res += "Always consult your physician or dietitian for clinical decisions."
        return res

    if "risk" in user_msg:
        res = "Your risk assessment considers your biomarkers, activity, and nutrition.\n"
        res += f"Your current BMI ({bmi:.1f}) and glucose ({patient.glucose}) are the primary drivers of your profile.\n"
        res += "To reduce risk: focus on 150 min/week of moderate activity and strictly adhere to the recommended protocol."
        return res

    # ── Default clinical summary (for startSession) ──
    res = f"NutriAI analysis complete. Based on your {patient.disease_type} history and current markers (Glucose: {patient.glucose}, BP: {patient.blood_pressure}), I recommend the **Balanced Protocol**.\n\n"
    res += "**Immediate Actions:**\n"
    res += f"1. Maintain caloric intake at {patient.daily_caloric} kcal with a focus on low-glycemic foods.\n"
    res += "2. Increase weekly exercise from your current 3 hrs/week to stabilize metabolic rates.\n\n"
    res += "Always consult your physician or dietitian for clinical decisions."
    return res

# ── Feature builder ────────────────────────────────────────────────
def build_features(p: PatientInput) -> np.ndarray:
    bmi = p.weight_kg / ((p.height_cm / 100) ** 2)
    row = [
        p.age, p.weight_kg, p.height_cm, round(bmi, 1),
        p.daily_caloric, p.cholesterol, p.blood_pressure,
        p.glucose, p.weekly_exercise, p.adherence, p.nutrient_imbalance,
        encode("Gender",                  p.gender),
        encode("Disease_Type",            p.disease_type),
        encode("Severity",                p.severity),
        encode("Physical_Activity_Level", p.activity_level),
        encode("Dietary_Restrictions",    p.restrictions),
        encode("Allergies",               p.allergies),
        encode("Preferred_Cuisine",       p.cuisine),
    ]
    return np.array(row).reshape(1, -1)

# ── Risk breakdown helper ──────────────────────────────────────────
def compute_risk_breakdown(p: PatientInput):
    bmi = p.weight_kg / ((p.height_cm / 100) ** 2)
    components = {
        "glucose":       round(float(np.clip((p.glucose - 70) / 130, 0, 1) * 25), 1),
        "blood_pressure": round(float(np.clip((p.blood_pressure - 90) / 90, 0, 1) * 25), 1),
        "cholesterol":   round(float(np.clip((p.cholesterol - 150) / 100, 0, 1) * 20), 1),
        "bmi":           round(float(np.clip((bmi - 18.5) / 30, 0, 1) * 15), 1),
        "activity":      round({"Sedentary": 10.0, "Moderate": 4.0, "Active": 0.0}.get(p.activity_level, 4.0), 1),
        "nutrition":     round((p.nutrient_imbalance / 5.0) * 5, 1),
    }
    flags = []
    if p.glucose > 180:   flags.append({"label": "Critical glucose",    "level": "critical"})
    elif p.glucose > 126: flags.append({"label": "Elevated glucose",    "level": "warning"})
    if p.blood_pressure > 160: flags.append({"label": "Hypertensive crisis", "level": "critical"})
    elif p.blood_pressure > 140: flags.append({"label": "High blood pressure", "level": "warning"})
    if p.cholesterol > 240: flags.append({"label": "High cholesterol",  "level": "warning"})
    if bmi > 35:            flags.append({"label": "Obesity class II",   "level": "critical"})
    elif bmi > 30:          flags.append({"label": "Obesity class I",    "level": "warning"})
    if p.activity_level == "Sedentary": flags.append({"label": "Sedentary lifestyle", "level": "info"})
    return components, flags

# ── Meal database ──────────────────────────────────────────────────
MEALS_DB = {
    ("High-Protein", "Indian"):   [
        {"name": "Paneer tikka bowl",         "kcal": 420, "protein": 32, "carbs": 18, "fat": 24, "time": "Lunch"},
        {"name": "Egg bhurji with roti",      "kcal": 380, "protein": 28, "carbs": 22, "fat": 18, "time": "Breakfast"},
        {"name": "Dal tadka (low carb)",      "kcal": 310, "protein": 18, "carbs": 20, "fat": 14, "time": "Dinner"},
        {"name": "Chicken tikka masala",      "kcal": 490, "protein": 38, "carbs": 12, "fat": 28, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Indian"):  [
        {"name": "Vegetable khichdi",         "kcal": 340, "protein": 14, "carbs": 55, "fat": 8,  "time": "Lunch"},
        {"name": "Oats upma",                 "kcal": 290, "protein": 10, "carbs": 48, "fat": 6,  "time": "Breakfast"},
        {"name": "Palak soup with multigrain","kcal": 220, "protein": 9,  "carbs": 30, "fat": 5,  "time": "Snack"},
        {"name": "Rajma with brown rice",     "kcal": 420, "protein": 18, "carbs": 62, "fat": 7,  "time": "Dinner"},
    ],
    ("Balanced-Macro", "Indian"): [
        {"name": "Mixed dal with chapati",    "kcal": 390, "protein": 16, "carbs": 58, "fat": 9,  "time": "Lunch"},
        {"name": "Curd rice with pickle",     "kcal": 320, "protein": 10, "carbs": 52, "fat": 7,  "time": "Dinner"},
        {"name": "Poha with peanuts",         "kcal": 280, "protein": 8,  "carbs": 44, "fat": 8,  "time": "Breakfast"},
        {"name": "Vegetable biryani",         "kcal": 460, "protein": 12, "carbs": 70, "fat": 12, "time": "Dinner"},
    ],
    ("High-Protein", "Chinese"):  [
        {"name": "Steamed fish with ginger",  "kcal": 380, "protein": 35, "carbs": 10, "fat": 18, "time": "Dinner"},
        {"name": "Egg drop soup",             "kcal": 180, "protein": 12, "carbs": 8,  "fat": 9,  "time": "Lunch"},
        {"name": "Stir-fried tofu & veg",     "kcal": 290, "protein": 20, "carbs": 14, "fat": 16, "time": "Lunch"},
        {"name": "Steamed chicken dumplings", "kcal": 340, "protein": 26, "carbs": 22, "fat": 14, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Chinese"): [
        {"name": "Congee (rice porridge)",    "kcal": 240, "protein": 8,  "carbs": 42, "fat": 3,  "time": "Breakfast"},
        {"name": "Steamed broccoli & oyster", "kcal": 180, "protein": 6,  "carbs": 22, "fat": 5,  "time": "Side"},
        {"name": "Hot & sour soup (low-Na)",  "kcal": 160, "protein": 8,  "carbs": 18, "fat": 4,  "time": "Starter"},
        {"name": "Steamed salmon fried rice", "kcal": 420, "protein": 28, "carbs": 48, "fat": 10, "time": "Dinner"},
    ],
    ("Balanced-Macro", "Chinese"):[
        {"name": "Wonton noodle soup",        "kcal": 360, "protein": 18, "carbs": 48, "fat": 9,  "time": "Lunch"},
        {"name": "Mapo tofu (light)",         "kcal": 320, "protein": 16, "carbs": 18, "fat": 18, "time": "Dinner"},
        {"name": "Steamed bun (bao)",         "kcal": 200, "protein": 8,  "carbs": 32, "fat": 4,  "time": "Snack"},
        {"name": "Cucumber sesame salad",     "kcal": 120, "protein": 3,  "carbs": 10, "fat": 7,  "time": "Side"},
    ],
    ("High-Protein", "Italian"):  [
        {"name": "Grilled chicken paillard",  "kcal": 390, "protein": 42, "carbs": 6,  "fat": 20, "time": "Dinner"},
        {"name": "Frittata (egg & veg)",      "kcal": 340, "protein": 26, "carbs": 8,  "fat": 22, "time": "Breakfast"},
        {"name": "Tuna carpaccio",            "kcal": 280, "protein": 30, "carbs": 4,  "fat": 14, "time": "Lunch"},
        {"name": "Bistecca (lean sirloin)",   "kcal": 460, "protein": 48, "carbs": 0,  "fat": 26, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Italian"): [
        {"name": "Minestrone soup",           "kcal": 220, "protein": 9,  "carbs": 38, "fat": 4,  "time": "Lunch"},
        {"name": "Caprese salad",             "kcal": 180, "protein": 10, "carbs": 8,  "fat": 12, "time": "Starter"},
        {"name": "Grilled sea bass",          "kcal": 380, "protein": 32, "carbs": 10, "fat": 20, "time": "Dinner"},
        {"name": "Ribollita (bread soup)",    "kcal": 300, "protein": 12, "carbs": 44, "fat": 6,  "time": "Dinner"},
    ],
    ("Balanced-Macro", "Italian"):[
        {"name": "Pasta primavera (wholewheat)","kcal": 420, "protein": 16, "carbs": 68, "fat": 9, "time": "Dinner"},
        {"name": "Bruschetta with tomato",    "kcal": 240, "protein": 7,  "carbs": 38, "fat": 6,  "time": "Snack"},
        {"name": "Risotto (mushroom)",        "kcal": 380, "protein": 12, "carbs": 62, "fat": 10, "time": "Dinner"},
        {"name": "Panzanella salad",          "kcal": 280, "protein": 8,  "carbs": 40, "fat": 10, "time": "Lunch"},
    ],
    ("High-Protein", "Mexican"):  [
        {"name": "Grilled chicken fajitas",   "kcal": 430, "protein": 38, "carbs": 20, "fat": 20, "time": "Dinner"},
        {"name": "Huevos rancheros (low carb)","kcal": 360, "protein": 24, "carbs": 16, "fat": 22,"time": "Breakfast"},
        {"name": "Carne asada tacos (2)",     "kcal": 480, "protein": 34, "carbs": 28, "fat": 24, "time": "Dinner"},
        {"name": "Black bean protein bowl",   "kcal": 400, "protein": 22, "carbs": 38, "fat": 14, "time": "Lunch"},
    ],
    ("Heart-Healthy", "Mexican"): [
        {"name": "Chicken tortilla soup",     "kcal": 280, "protein": 20, "carbs": 28, "fat": 8,  "time": "Lunch"},
        {"name": "Veggie burrito (low-Na)",   "kcal": 380, "protein": 14, "carbs": 58, "fat": 8,  "time": "Dinner"},
        {"name": "Guacamole & jicama sticks", "kcal": 190, "protein": 3,  "carbs": 14, "fat": 14, "time": "Snack"},
        {"name": "Baked tilapia tacos",       "kcal": 350, "protein": 28, "carbs": 32, "fat": 10, "time": "Dinner"},
    ],
    ("Balanced-Macro", "Mexican"):[
        {"name": "Burrito bowl (brown rice)",  "kcal": 460, "protein": 20, "carbs": 62, "fat": 12, "time": "Lunch"},
        {"name": "Quesadilla (wholewheat)",    "kcal": 380, "protein": 18, "carbs": 44, "fat": 14, "time": "Dinner"},
        {"name": "Mexican street corn salad",  "kcal": 220, "protein": 6,  "carbs": 32, "fat": 8,  "time": "Side"},
        {"name": "Pozole (light)",             "kcal": 310, "protein": 20, "carbs": 36, "fat": 6,  "time": "Dinner"},
    ],
}

ALLERGEN_KEYWORDS = {
    "Peanuts": ["peanut", "groundnut"],
    "Gluten":  ["roti","chapati","naan","bread","pasta","bun","tortilla","burrito",
                "quesadilla","wrap","dumpling","tostada","bruschetta","couscous","semolina"],
    "Dairy":   ["paneer","curd","yogurt","cheese","cream","butter","ghee","milk","lassi"],
    "None":    [],
}

def get_meals(meal_cat: str, cuisine: str, restrictions: str, allergies: str) -> list:
    key = (meal_cat, cuisine)
    meals = MEALS_DB.get(key, MEALS_DB.get((meal_cat, "Indian"), []))
    keywords = ALLERGEN_KEYWORDS.get(allergies, [allergies.lower()] if allergies and allergies != "None" else [])
    if not keywords:
        return meals
    filtered = [
        m for m in meals
        if not any(kw in m["name"].lower() for kw in keywords)
    ]
    # Only fall back to unfiltered list if zero meals remain — prefer safe empty over unsafe full
    return filtered if filtered else [
        {"name": f"Custom allergen-free meal (ask your dietitian for {allergies}-free options)",
         "kcal": 400, "protein": 20, "carbs": 40, "fat": 12, "time": "Any"}
    ]

# ── Routes ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "NutriAI API v1.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": True, "meta": META["stats"]}

@app.post("/predict")
def predict(patient: PatientInput):
    """
    Run all 3 ML models and return diet recommendation,
    health risk score, and meal category.
    """
    X = build_features(patient)

    # Diet prediction
    diet_idx  = int(diet_model.predict(X)[0])
    diet_prob = diet_model.predict_proba(X)[0]
    diet_name = DIET_CLASSES[diet_idx]
    confidence = round(float(diet_prob[diet_idx]), 4)

    # Risk score
    risk_score = round(float(risk_model.predict(X)[0]), 1)
    risk_score = float(np.clip(risk_score, 0, 100))

    # Risk level label
    if risk_score >= 70:   risk_level = "High"
    elif risk_score >= 40: risk_level = "Moderate"
    else:                  risk_level = "Low"

    # Meal category
    meal_idx  = int(meal_model.predict(X)[0])
    meal_cat  = MEAL_CLASSES[meal_idx]

    # Risk breakdown & flags
    components, flags = compute_risk_breakdown(patient)

    # Meals
    bmi = round(patient.weight_kg / (patient.height_cm / 100) ** 2, 1)
    meals = get_meals(meal_cat, patient.cuisine, patient.restrictions, patient.allergies)

    # Insights
    insights = []
    if patient.disease_type == "Diabetes":
        insights.append("Target fasting glucose < 100 mg/dL through carbohydrate restriction.")
        if patient.glucose > 140:
            insights.append("Post-meal glucose monitoring at 1–2 hrs is essential.")
    elif patient.disease_type == "Hypertension":
        insights.append("Reduce sodium intake below 1,500 mg/day using DASH protocol.")
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

    # Health scores (0-100) — simplified algorithm
    metabolic_score = max(0, int(100 - components["glucose"] * 2.5 - components["bmi"] * 3))
    cardio_score    = max(0, int(100 - components["blood_pressure"] * 2.5 - components["cholesterol"] * 2))
    lifestyle_score = min(100, int((patient.weekly_exercise / 10) * 60 + (40 if patient.activity_level == "Active" else 20 if patient.activity_level == "Moderate" else 0)))
    overall_score   = int((metabolic_score + cardio_score + lifestyle_score) / 3)

    return {
        "diet": diet_name,
        "conf": confidence,
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "riskComponents": components,
        "mealCat": meal_cat,
        "flags": flags,
        "insights": insights,
        "scores": {
            "metabolic": metabolic_score,
            "cardiovascular": cardio_score,
            "lifestyle": lifestyle_score,
            "overall": overall_score
        },
        "bmi": bmi,
        "recommended_meals": meals,
    }

@app.post("/predict/diet")
def predict_diet_only(patient: PatientInput):
    X = build_features(patient)
    diet_idx  = int(diet_model.predict(X)[0])
    diet_prob = diet_model.predict_proba(X)[0]
    return {
        "recommendation": DIET_CLASSES[diet_idx],
        "confidence": round(float(diet_prob[diet_idx]), 4),
        "probabilities": {DIET_CLASSES[i]: round(float(p), 4) for i, p in enumerate(diet_prob)},
    }

@app.post("/predict/risk")
def predict_risk_only(patient: PatientInput):
    X = build_features(patient)
    risk_score = float(np.clip(risk_model.predict(X)[0], 0, 100))
    components, flags = compute_risk_breakdown(patient)
    return {"risk_score": round(risk_score, 1), "components": components, "flags": flags}

@app.post("/meals")
def get_meal_recommendations(patient: PatientInput):
    X = build_features(patient)
    meal_idx = int(meal_model.predict(X)[0])
    meal_cat = MEAL_CLASSES[meal_idx]
    meals = get_meals(meal_cat, patient.cuisine, patient.restrictions, patient.allergies)
    return {"category": meal_cat, "cuisine": patient.cuisine, "meals": meals}

@app.post("/chat")
def chat(request: ChatRequest):
    """
    Handle AI consultation requests by generating clinical-grade responses
    based on patient data and history.
    """
    try:
        response = generate_clinical_assistant_response(request.patient_data, request.messages)
        return {"content": [{"text": response}]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/info")
def model_info():
    return {"models": META["stats"], "diet_classes": DIET_CLASSES, "meal_classes": MEAL_CLASSES}

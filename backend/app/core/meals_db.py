"""
app/core/meals_db.py — Meal database, allergen keyword map,
and helper functions extracted from main.py.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

# ── Meal database ──────────────────────────────────────────────────────────────
# Key: (meal_category, cuisine) → list of meal dicts
MEALS_DB: Dict[Tuple[str, str], List[dict]] = {
    ("High-Protein", "Indian"): [
        {"name": "Paneer tikka bowl",          "kcal": 420, "protein": 32, "carbs": 18, "fat": 24, "time": "Lunch"},
        {"name": "Egg bhurji with roti",       "kcal": 380, "protein": 28, "carbs": 22, "fat": 18, "time": "Breakfast"},
        {"name": "Dal tadka (low carb)",       "kcal": 310, "protein": 18, "carbs": 20, "fat": 14, "time": "Dinner"},
        {"name": "Chicken tikka masala",       "kcal": 490, "protein": 38, "carbs": 12, "fat": 28, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Indian"): [
        {"name": "Vegetable khichdi",          "kcal": 340, "protein": 14, "carbs": 55, "fat": 8,  "time": "Lunch"},
        {"name": "Oats upma",                  "kcal": 290, "protein": 10, "carbs": 48, "fat": 6,  "time": "Breakfast"},
        {"name": "Palak soup with multigrain", "kcal": 220, "protein": 9,  "carbs": 30, "fat": 5,  "time": "Snack"},
        {"name": "Rajma with brown rice",      "kcal": 420, "protein": 18, "carbs": 62, "fat": 7,  "time": "Dinner"},
    ],
    ("Balanced-Macro", "Indian"): [
        {"name": "Mixed dal with chapati",     "kcal": 390, "protein": 16, "carbs": 58, "fat": 9,  "time": "Lunch"},
        {"name": "Curd rice with pickle",      "kcal": 320, "protein": 10, "carbs": 52, "fat": 7,  "time": "Dinner"},
        {"name": "Poha with peanuts",          "kcal": 280, "protein": 8,  "carbs": 44, "fat": 8,  "time": "Breakfast"},
        {"name": "Vegetable biryani",          "kcal": 460, "protein": 12, "carbs": 70, "fat": 12, "time": "Dinner"},
    ],
    ("High-Protein", "Chinese"): [
        {"name": "Steamed fish with ginger",   "kcal": 380, "protein": 35, "carbs": 10, "fat": 18, "time": "Dinner"},
        {"name": "Egg drop soup",              "kcal": 180, "protein": 12, "carbs": 8,  "fat": 9,  "time": "Lunch"},
        {"name": "Stir-fried tofu & veg",     "kcal": 290, "protein": 20, "carbs": 14, "fat": 16, "time": "Lunch"},
        {"name": "Steamed chicken dumplings",  "kcal": 340, "protein": 26, "carbs": 22, "fat": 14, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Chinese"): [
        {"name": "Congee (rice porridge)",     "kcal": 240, "protein": 8,  "carbs": 42, "fat": 3,  "time": "Breakfast"},
        {"name": "Steamed broccoli & oyster",  "kcal": 180, "protein": 6,  "carbs": 22, "fat": 5,  "time": "Side"},
        {"name": "Hot & sour soup (low-Na)",   "kcal": 160, "protein": 8,  "carbs": 18, "fat": 4,  "time": "Starter"},
        {"name": "Steamed salmon fried rice",  "kcal": 420, "protein": 28, "carbs": 48, "fat": 10, "time": "Dinner"},
    ],
    ("Balanced-Macro", "Chinese"): [
        {"name": "Wonton noodle soup",         "kcal": 360, "protein": 18, "carbs": 48, "fat": 9,  "time": "Lunch"},
        {"name": "Mapo tofu (light)",          "kcal": 320, "protein": 16, "carbs": 18, "fat": 18, "time": "Dinner"},
        {"name": "Steamed bun (bao)",          "kcal": 200, "protein": 8,  "carbs": 32, "fat": 4,  "time": "Snack"},
        {"name": "Cucumber sesame salad",      "kcal": 120, "protein": 3,  "carbs": 10, "fat": 7,  "time": "Side"},
    ],
    ("High-Protein", "Italian"): [
        {"name": "Grilled chicken paillard",   "kcal": 390, "protein": 42, "carbs": 6,  "fat": 20, "time": "Dinner"},
        {"name": "Frittata (egg & veg)",       "kcal": 340, "protein": 26, "carbs": 8,  "fat": 22, "time": "Breakfast"},
        {"name": "Tuna carpaccio",             "kcal": 280, "protein": 30, "carbs": 4,  "fat": 14, "time": "Lunch"},
        {"name": "Bistecca (lean sirloin)",    "kcal": 460, "protein": 48, "carbs": 0,  "fat": 26, "time": "Dinner"},
    ],
    ("Heart-Healthy", "Italian"): [
        {"name": "Minestrone soup",            "kcal": 220, "protein": 9,  "carbs": 38, "fat": 4,  "time": "Lunch"},
        {"name": "Caprese salad",              "kcal": 180, "protein": 10, "carbs": 8,  "fat": 12, "time": "Starter"},
        {"name": "Grilled sea bass",           "kcal": 380, "protein": 32, "carbs": 10, "fat": 20, "time": "Dinner"},
        {"name": "Ribollita (bread soup)",     "kcal": 300, "protein": 12, "carbs": 44, "fat": 6,  "time": "Dinner"},
    ],
    ("Balanced-Macro", "Italian"): [
        {"name": "Pasta primavera (wholewheat)", "kcal": 420, "protein": 16, "carbs": 68, "fat": 9, "time": "Dinner"},
        {"name": "Bruschetta with tomato",     "kcal": 240, "protein": 7,  "carbs": 38, "fat": 6,  "time": "Snack"},
        {"name": "Risotto (mushroom)",         "kcal": 380, "protein": 12, "carbs": 62, "fat": 10, "time": "Dinner"},
        {"name": "Panzanella salad",           "kcal": 280, "protein": 8,  "carbs": 40, "fat": 10, "time": "Lunch"},
    ],
    ("High-Protein", "Mexican"): [
        {"name": "Grilled chicken fajitas",    "kcal": 430, "protein": 38, "carbs": 20, "fat": 20, "time": "Dinner"},
        {"name": "Huevos rancheros (low carb)", "kcal": 360, "protein": 24, "carbs": 16, "fat": 22, "time": "Breakfast"},
        {"name": "Carne asada tacos (2)",      "kcal": 480, "protein": 34, "carbs": 28, "fat": 24, "time": "Dinner"},
        {"name": "Black bean protein bowl",    "kcal": 400, "protein": 22, "carbs": 38, "fat": 14, "time": "Lunch"},
    ],
    ("Heart-Healthy", "Mexican"): [
        {"name": "Chicken tortilla soup",      "kcal": 280, "protein": 20, "carbs": 28, "fat": 8,  "time": "Lunch"},
        {"name": "Veggie burrito (low-Na)",    "kcal": 380, "protein": 14, "carbs": 58, "fat": 8,  "time": "Dinner"},
        {"name": "Guacamole & jicama sticks",  "kcal": 190, "protein": 3,  "carbs": 14, "fat": 14, "time": "Snack"},
        {"name": "Baked tilapia tacos",        "kcal": 350, "protein": 28, "carbs": 32, "fat": 10, "time": "Dinner"},
    ],
    ("Balanced-Macro", "Mexican"): [
        {"name": "Burrito bowl (brown rice)",  "kcal": 460, "protein": 20, "carbs": 62, "fat": 12, "time": "Lunch"},
        {"name": "Quesadilla (wholewheat)",    "kcal": 380, "protein": 18, "carbs": 44, "fat": 14, "time": "Dinner"},
        {"name": "Mexican street corn salad",  "kcal": 220, "protein": 6,  "carbs": 32, "fat": 8,  "time": "Side"},
        {"name": "Pozole (light)",             "kcal": 310, "protein": 20, "carbs": 36, "fat": 6,  "time": "Dinner"},
    ],
}

ALLERGEN_KEYWORDS: Dict[str, List[str]] = {
    "Peanuts": ["peanut", "groundnut"],
    "Gluten": [
        "roti", "chapati", "naan", "bread", "pasta", "bun", "tortilla",
        "burrito", "quesadilla", "wrap", "dumpling", "tostada", "bruschetta",
        "couscous", "semolina",
    ],
    "Dairy": ["paneer", "curd", "yogurt", "cheese", "cream", "butter", "ghee", "milk", "lassi"],
    "None": [],
}


def get_meals(meal_cat: str, cuisine: str, restrictions: str, allergies: str) -> List[dict]:
    """Return allergen-filtered meals for the given category and cuisine."""
    key = (meal_cat, cuisine)
    meals = MEALS_DB.get(key, MEALS_DB.get((meal_cat, "Indian"), []))

    keywords = ALLERGEN_KEYWORDS.get(
        allergies,
        [allergies.lower()] if allergies and allergies != "None" else [],
    )
    if not keywords:
        return meals

    filtered = [m for m in meals if not any(kw in m["name"].lower() for kw in keywords)]
    if filtered:
        return filtered

    # Safe fallback — always return something, never an empty list
    return [
        {
            "name": f"Custom allergen-free meal (ask your dietitian for {allergies}-free options)",
            "kcal": 400,
            "protein": 20,
            "carbs": 40,
            "fat": 12,
            "time": "Any",
        }
    ]


def compute_risk_breakdown(
    glucose: float,
    blood_pressure: int,
    cholesterol: float,
    bmi: float,
    activity_level: str,
    nutrient_imbalance: float,
) -> tuple[dict, list]:
    """
    Decompose total risk score into labelled components and flag list.
    Returns (components_dict, flags_list).
    """
    import numpy as np

    components = {
        "glucose":        round(float(np.clip((glucose - 70) / 130, 0, 1) * 25), 1),
        "blood_pressure": round(float(np.clip((blood_pressure - 90) / 90, 0, 1) * 25), 1),
        "cholesterol":    round(float(np.clip((cholesterol - 150) / 100, 0, 1) * 20), 1),
        "bmi":            round(float(np.clip((bmi - 18.5) / 30, 0, 1) * 15), 1),
        "activity":       round({"Sedentary": 10.0, "Moderate": 4.0, "Active": 0.0}.get(activity_level, 4.0), 1),
        "nutrition":      round((nutrient_imbalance / 5.0) * 5, 1),
    }

    flags = []
    if glucose > 180:          flags.append({"label": "Critical glucose",    "level": "critical"})
    elif glucose > 126:        flags.append({"label": "Elevated glucose",    "level": "warning"})
    if blood_pressure > 160:   flags.append({"label": "Hypertensive crisis", "level": "critical"})
    elif blood_pressure > 140: flags.append({"label": "High blood pressure", "level": "warning"})
    if cholesterol > 240:      flags.append({"label": "High cholesterol",    "level": "warning"})
    if bmi > 35:               flags.append({"label": "Obesity class II",    "level": "critical"})
    elif bmi > 30:             flags.append({"label": "Obesity class I",     "level": "warning"})
    if activity_level == "Sedentary":
        flags.append({"label": "Sedentary lifestyle", "level": "info"})

    return components, flags

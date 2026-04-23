"""
app/routers/meals.py — /meals endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.logging import get_logger
from app.core.meals_db import get_meals
from app.schemas.patient import PatientInput
from app.schemas.responses import MealResponse
from app.services.ml_service import ml_service

router = APIRouter(prefix="/meals", tags=["Meals"])
log = get_logger(__name__)


@router.post("", response_model=MealResponse, summary="Meal recommendations")
async def get_meal_recommendations(patient: PatientInput, request: Request) -> MealResponse:
    """
    Run the meal classifier model and return allergen-filtered meal suggestions
    for the patient's preferred cuisine.
    """
    X        = ml_service.build_features(patient)
    meal_cat = ml_service.predict_meal_category(X)
    meals    = get_meals(meal_cat, patient.cuisine, patient.restrictions, patient.allergies)

    log.info("meals_predicted", meal_cat=meal_cat, cuisine=patient.cuisine, n_meals=len(meals))

    return MealResponse(category=meal_cat, cuisine=patient.cuisine, meals=meals)


@router.get("/search", summary="Search food database")
async def search_foods(q: str = ""):
    """Search through the master clinical food database."""
    from app.core.meals_db import MEALS_DB
    
    results = []
    query = q.lower()
    
    # Flatten MEALS_DB for searching
    for (cat, cuisine), meals in MEALS_DB.items():
        for m in meals:
            if query in m["name"].lower():
                results.append({
                    "name": m["name"],
                    "kcal": m["kcal"],
                    "p": m["protein"],
                    "f": m["fat"],
                    "c": m["carbs"],
                    "cat": cat,
                    "cuisine": cuisine
                })
    
    return results[:50] # Limit to 50 results


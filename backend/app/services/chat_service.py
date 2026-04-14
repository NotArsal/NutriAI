"""
app/services/chat_service.py — Clinical AI consultation response generator.
Extracted from main.py; no functional changes, but now properly typed
and structured for future LLM / streaming upgrade in Phase 3.
"""
from __future__ import annotations

from typing import List

from app.schemas.patient import PatientInput


def generate_clinical_response(patient: PatientInput, messages: List[dict]) -> str:
    """
    Generate a contextual clinical response based on the last user message
    and patient biomarker data.

    Phase 3 upgrade: Replace with SSE-streamed LLM call (OpenAI / Gemini).
    """
    user_msg = messages[-1].get("content", "").lower() if messages else ""
    bmi      = patient.bmi

    # ── Biomarker targets ────────────────────────────────────────────────────
    if any(kw in user_msg for kw in ("biomarker", "target", "number", "lab")):
        lines = [
            "Your clinical biomarkers indicate the following target zones:",
            f"- **Glucose**: Current {patient.glucose} mg/dL → Target < 100 mg/dL (fasting).",
            f"- **Blood Pressure**: Current {patient.blood_pressure} mmHg → Target < 120/80 mmHg.",
            f"- **BMI**: Current {bmi} kg/m² → Healthy range: 18.5–24.9.",
            f"- **Cholesterol**: Current {patient.cholesterol} mg/dL → Target < 200 mg/dL.",
            "",
            "Reaching these targets will significantly reduce your composite health risk score.",
        ]
        return "\n".join(lines)

    # ── Meal / eating advice ─────────────────────────────────────────────────
    if any(kw in user_msg for kw in ("meal", "eat", "food", "diet", "schedule", "breakfast", "lunch", "dinner")):
        allergen_note = (
            f"strictly avoid all **{patient.allergies}** — always check ingredient labels"
            if patient.allergies != "None"
            else "minimise ultra-processed foods and refined carbohydrates"
        )
        return (
            f"Based on your **{patient.cuisine}** cuisine preference and **{patient.disease_type}** diagnosis:\n\n"
            "1. **Breakfast**: High-fibre options — oats upma, protein-rich eggs, or multigrain with avocado.\n"
            "2. **Lunch/Dinner**: Focus on lean protein (chicken / fish / legumes) with a 2:1 vegetable-to-grain ratio.\n"
            f"3. **Critical restriction**: {allergen_note.capitalize()}.\n\n"
            "⚕️ *Always consult your physician or registered dietitian before making significant dietary changes.*"
        )

    # ── Risk score ───────────────────────────────────────────────────────────
    if "risk" in user_msg:
        return (
            "Your risk score is driven by your biomarkers, activity level, and nutritional balance.\n\n"
            f"- **Primary drivers**: BMI ({bmi}) and glucose ({patient.glucose} mg/dL).\n"
            "- **To reduce risk**: Achieve 150 min/week of moderate aerobic exercise "
            "and adhere strictly to your recommended dietary protocol.\n"
            "- Each 5-point reduction in risk score correlates with improved 10-year cardiovascular outcomes "
            "(Framingham Heart Study model)."
        )

    # ── Exercise ─────────────────────────────────────────────────────────────
    if any(kw in user_msg for kw in ("exercise", "workout", "activity", "gym", "walk")):
        return (
            f"With your current activity level ({patient.activity_level}), here are evidence-based targets:\n\n"
            "- **Minimum**: 150 min/week moderate cardio (WHO guidelines).\n"
            "- **Ideal**: 300 min/week moderate OR 150 min/week vigorous activity.\n"
            "- **Resistance training**: 2×/week for glucose regulation (ADA 2023).\n"
            "- Start with 20-minute brisk walks if currently sedentary — gradual progression is key."
        )

    # ── Default — session summary ─────────────────────────────────────────────
    return (
        f"NutriAI analysis complete. Based on your **{patient.disease_type}** history "
        f"and current markers (Glucose: {patient.glucose} mg/dL, BP: {patient.blood_pressure} mmHg), "
        f"I recommend the **{'Low-Carb' if patient.disease_type == 'Diabetes' else 'Low-Sodium' if patient.disease_type == 'Hypertension' else 'Balanced'} Protocol**.\n\n"
        "**Immediate actions:**\n"
        f"1. Maintain caloric intake near {patient.daily_caloric} kcal/day with low-glycaemic foods.\n"
        "2. Aim for ≥ 150 min/week of moderate aerobic exercise.\n"
        "3. Monitor biomarkers monthly and update your plan accordingly.\n\n"
        "⚕️ *Always consult your physician or dietitian for clinical decisions.*"
    )

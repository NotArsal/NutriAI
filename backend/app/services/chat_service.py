"""
app/services/chat_service.py — Clinical AI consultation response generator.
Upgraded to Track 2: Context-Aware Assistant with Safety Guardrails, KNN-Bridge, and Redis Memory.
"""
from __future__ import annotations

import json
import hashlib
from typing import List, Dict

from app.schemas.patient import PatientInput
from app.services.ml_service import ml_service
from app.core.redis_client import redis_client
from app.core.logging import get_logger

log = get_logger(__name__)

async def _get_or_create_session_context(user_id: str | None, patient: PatientInput) -> dict:
    """Uses Redis to maintain short-term state, stored by user_id or patient hash."""
    base_key = user_id or hashlib.sha256(patient.model_dump_json().encode()).hexdigest()
    session_id = f"chat_session:{base_key}"
    cached = await redis_client.get(session_id)
    if cached:
        return json.loads(cached)
    return {"last_meals": [], "turn_count": 0, "history": []}

async def _save_session_context(user_id: str | None, patient: PatientInput, context: dict):
    base_key = user_id or hashlib.sha256(patient.model_dump_json().encode()).hexdigest()
    session_id = f"chat_session:{base_key}"
    # Sliding window: keep last 10 messages
    if len(context.get("history", [])) > 10:
        context["history"] = context["history"][-10:]
    await redis_client.set(session_id, json.dumps(context), expire=3600) # 1 hour expiry

def _check_safety_guardrails(user_msg: str) -> str | None:
    """Track 2: Safety Guardrails for emergency and out-of-scope queries."""
    emergency_keywords = ["chest pain", "heart attack", "stroke", "fainting", "severe pain", "bleeding", "emergency"]
    out_of_scope_keywords = ["surgery", "medication", "dose", "dosage", "pill", "prescription", "vaccine"]
    
    if any(kw in user_msg for kw in emergency_keywords):
        return "🚨 **MEDICAL EMERGENCY DETECTED**: Please call your local emergency services (e.g., 911) immediately or go to the nearest emergency room. I am an AI nutrition assistant and cannot handle acute medical emergencies."
        
    if any(kw in user_msg for kw in out_of_scope_keywords):
        return "⚕️ **OUT OF SCOPE**: My expertise is strictly limited to clinical nutrition and dietary planning. I cannot provide pharmacological, surgical, or medical dosage advice. Please consult your physician for these matters."
        
    return None

async def generate_clinical_response(
    patient: PatientInput, 
    messages: List[dict], 
    user_id: str | None = None,
    prediction: Optional[dict] = None
) -> str:
    """
    Context-aware clinical response using Simulated LLM logic, KNN bridging, and Redis memory.
    """
    user_msg = messages[-1].get("content", "").lower() if messages else ""
    bmi = patient.bmi
    
    # 0. Extraction from ML-Predicted Protocol (Track 2 Clinical Context Bridge)
    diet_protocol = prediction.get("diet") if prediction else "Standard Clinical"
    risk_level = prediction.get("riskLevel") if prediction else "Unknown"
    
    # 1. Safety Guardrails
    safety_response = _check_safety_guardrails(user_msg)
    if safety_response:
        return safety_response

    # 2. Stateful Memory via Redis
    context = await _get_or_create_session_context(user_id, patient)
    context["turn_count"] += 1
    
    # 3. Contextual Seeding (Simulated System Context)
    # Track 2: Conversation is now augmented with patient biomarkers
    
    # 4. KNN-Chat Bridge (Tool Calling)
    if any(kw in user_msg for kw in ["alternative", "another meal", "different food", "what else", "hungry"]):
        # Trigger narrowed KNN search
        log.info("chat_triggered_knn_bridge")
        # To get an alternative, we perturb the protein target
        meals = ml_service.predict_meal(patient, target_protein=(patient.weight_kg * 1.8))
        
        meal_names = [m["name"] for m in meals]
        context["last_meals"] = meal_names
        
        response = f"I have queried the KNN engine for clinical alternatives. Since you are managing **{patient.disease_type}**, I've prioritised low-glycemic options:\n\n"
        for m in meals:
            response += f"- **{m['time']}**: {m['name']} ({m['kcal']} kcal)\n"
        response += "\nDoes this new plan better suit your preference?"
        
        context["history"].append({"role": "user", "content": user_msg})
        context["history"].append({"role": "assistant", "content": response})
        await _save_session_context(user_id, patient, context)
        return response

    # 5. Stateful follow-up
    if "recipe" in user_msg or "how to make" in user_msg:
        if context["last_meals"]:
            meal = context["last_meals"][0]
            text = f"For **{meal}**, focus on using whole ingredients and completely avoiding added sugars. Ensure you portion control to maintain your {patient.daily_caloric} kcal target."
        else:
            text = "I don't have a specific meal in mind. Would you like me to recommend a daily plan?"
    
    elif any(kw in user_msg for kw in ("biomarker", "target", "number", "lab")):
        text = (
            f"Based on your profile, here are your target zones:\n"
            f"- **Glucose**: Current {patient.glucose} mg/dL → Target < 100 mg/dL.\n"
            f"- **Blood Pressure**: Current {patient.blood_pressure} mmHg → Target < 120/80 mmHg.\n"
            f"- **BMI**: Current {bmi} kg/m² → Healthy range: 18.5–24.9.\n"
        )
    else:
        text = (
            f"NutriAI Session Active (Turn {context['turn_count']}).\n"
            f"Our models have classified your case as **{risk_level} Risk** requiring a **{diet_protocol}** protocol. "
            f"Tracking your **{patient.disease_type}** history with a focus on your current glucose ({patient.glucose} mg/dL). "
            f"I recommend maintaining your {patient.daily_caloric} kcal target. "
            "Ask me for 'alternatives' if you need a new meal plan."
        )

    context["history"].append({"role": "user", "content": user_msg})
    context["history"].append({"role": "assistant", "content": text})
    await _save_session_context(user_id, patient, context)
    return text


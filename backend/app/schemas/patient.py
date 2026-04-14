"""
app/schemas/patient.py — PatientInput Pydantic v2 model.
Validates all incoming patient data with strict field constraints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PatientInput(BaseModel):
    age:                int   = Field(..., ge=18,  le=100,  examples=[45],    description="Patient age in years")
    gender:             str   = Field(...,                   examples=["Male"], description="Biological sex: Male | Female")
    weight_kg:          float = Field(..., gt=20,  lt=300,  examples=[75.0],  description="Body weight in kilograms")
    height_cm:          int   = Field(..., gt=100, lt=250,  examples=[170],   description="Height in centimetres")
    disease_type:       str   = Field(...,                   examples=["Diabetes"], description="Primary diagnosis")
    severity:           str   = Field(...,                   examples=["Moderate"], description="Disease severity")
    activity_level:     str   = Field(...,                   examples=["Moderate"], description="Physical activity level")
    daily_caloric:      int   = Field(..., gt=500, lt=6000, examples=[2200],  description="Daily caloric intake in kcal")
    cholesterol:        float = Field(..., gt=50,  lt=400,  examples=[210.0], description="Total cholesterol in mg/dL")
    blood_pressure:     int   = Field(..., gt=60,  lt=220,  examples=[135],   description="Systolic blood pressure in mmHg")
    glucose:            float = Field(..., gt=40,  lt=400,  examples=[150.0], description="Fasting glucose in mg/dL")
    weekly_exercise:    float = Field(default=3.0, ge=0, le=40,              description="Weekly exercise hours")
    adherence:          float = Field(default=70.0, ge=0, le=100,            description="Diet plan adherence percentage")
    nutrient_imbalance: float = Field(default=2.5, ge=0, le=5,              description="Nutrient imbalance score (0–5)")
    restrictions:       str   = Field(default="None",                        description="Dietary restrictions")
    allergies:          str   = Field(default="None",                        description="Known food allergies")
    cuisine:            str   = Field(default="Indian",                      description="Preferred cuisine style")

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, v: str) -> str:
        if v not in {"Male", "Female"}:
            raise ValueError("gender must be 'Male' or 'Female'")
        return v

    @field_validator("disease_type")
    @classmethod
    def valid_disease(cls, v: str) -> str:
        valid = {"None", "Diabetes", "Hypertension", "Obesity"}
        if v not in valid:
            raise ValueError(f"disease_type must be one of {sorted(valid)}")
        return v

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, v: str) -> str:
        valid = {"Mild", "Moderate", "Severe"}
        if v not in valid:
            raise ValueError(f"severity must be one of {sorted(valid)}")
        return v

    @field_validator("activity_level")
    @classmethod
    def valid_activity(cls, v: str) -> str:
        valid = {"Sedentary", "Moderate", "Active"}
        if v not in valid:
            raise ValueError(f"activity_level must be one of {sorted(valid)}")
        return v

    @property
    def bmi(self) -> float:
        return round(self.weight_kg / ((self.height_cm / 100) ** 2), 1)

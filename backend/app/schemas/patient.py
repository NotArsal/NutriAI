"""
app/schemas/patient.py — PatientInput Pydantic v2 model.
Validates all incoming patient data with strict field constraints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PatientInput(BaseModel):
    age:                int   = Field(..., ge=18,  le=120,  examples=[45],    description="Patient age (18-120 years)")
    gender:             str   = Field(...,                   examples=["Male"], description="Biological sex: Male | Female")
    weight_kg:          float = Field(..., gt=30,  lt=250,  examples=[75.0],  description="Body weight (30-250 kg)")
    height_cm:          int   = Field(..., gt=120, lt=230,  examples=[170],   description="Height (120-230 cm)")
    disease_type:       str   = Field(...,                   examples=["Diabetes"], description="Primary clinical diagnosis")
    severity:           str   = Field(...,                   examples=["Moderate"], description="Clinically assessed severity")
    activity_level:     str   = Field(...,                   examples=["Moderate"], description="Lifestyle activity level")
    daily_caloric:      int   = Field(..., ge=800, le=5000, examples=[2200],  description="Target daily caloric intake (kcal)")
    cholesterol:        float = Field(..., ge=50,  le=500,  examples=[210.0], description="Serum cholesterol (mg/dL)")
    blood_pressure:     int   = Field(..., ge=60,  le=250,  examples=[135],   description="Systolic BP (mmHg)")
    glucose:            float = Field(..., ge=40,  le=600,  examples=[150.0], description="Fasting plasma glucose (mg/dL)")
    weekly_exercise:    float = Field(default=3.0, ge=0, le=40,              description="Exercise hours per week")
    adherence:          float = Field(default=70.0, ge=0, le=100,            description="Clinical diet adherence (0-100%)")
    nutrient_imbalance: float = Field(default=2.5, ge=0, le=10,             description="Nutrient imbalance metric (0-10)")
    restrictions:       str   = Field(default="None",                        description="Religious or lifestyle restrictions")
    allergies:          str   = Field(default="None",                        description="Medically diagnosed food allergies")
    cuisine:            str   = Field(default="Indian",                      description="Cultural cuisine preference")

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

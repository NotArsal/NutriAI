# NutriPlanner Model Card
**Version 1.0 | Format: HuggingFace Model Card Standard**

---

## Model Details

| Property | Value |
|---|---|
| **Model name** | NutriPlanner Ensemble |
| **Version** | 1.0.0 |
| **Type** | 3-model ensemble (GBM classifier + RF regressor + RF classifier) |
| **Framework** | scikit-learn 1.2.2 |
| **Developed by** | NutriPlanner Research Team |
| **License** | MIT |
| **Contact** | See repository README |

### Architecture

| Model | Algorithm | Task | Output |
|---|---|---|---|
| `diet_model.pkl` | Gradient Boosting Classifier | Multi-class classification (3 classes) | Diet protocol: Balanced / Low_Carb / Low_Sodium |
| `risk_model.pkl` | Random Forest Regressor | Regression | Health risk score 0–100 with 90% CI |
| `meal_model.pkl` | Random Forest Classifier | Multi-class classification (3 classes) | Meal category: Balanced-Macro / High-Protein / Heart-Healthy |

---

## Intended Use

### Primary Use Cases
- Informational clinical nutrition guidance for adult patients (18–100 years)
- Personalised diet protocol recommendation based on biomarker profile
- Health risk stratification for clinical decision support
- Meal planning assistance based on dietary preferences and allergens

### Out-of-Scope Uses
- ❌ Replacing professional medical advice or clinical diagnosis
- ❌ Paediatric patients (< 18 years)
- ❌ Pregnant or breastfeeding individuals
- ❌ Patients with rare metabolic disorders (phenylketonuria, maple syrup urine disease, etc.)
- ❌ Medication dosing or pharmaceutical decisions
- ❌ Emergency or acute care settings

---

## Training Data

### Dataset
> ⚠️ **Current models are trained on synthetic data. Real-world performance is UNKNOWN.**  
> Upgrade to NHANES + UCI datasets is documented in `docs/datasets.md`.

| Property | Detail |
|---|---|
| **Size** | 1,000 synthetic patient records |
| **Generation method** | Probabilistic simulation based on clinical knowledge |
| **Demographics** | Age 18–80, Male/Female binary, 4 cuisine groups |
| **Conditions** | Diabetes (25%), Hypertension (25%), Obesity (25%), None (25%) |
| **Severity split** | Mild: 33%, Moderate: 33%, Severe: 33% |
| **Activity split** | Sedentary: 33%, Moderate: 33%, Active: 33% |

### Input Features (18 total)

| Feature | Type | Range | Description |
|---|---|---|---|
| Age | Numeric | 18–100 | Years |
| Weight_kg | Numeric | 20–300 | Kilograms |
| Height_cm | Numeric | 100–250 | Centimetres |
| BMI | Numeric | derived | kg/m² |
| Daily_Caloric_Intake | Numeric | 500–6000 | kcal/day |
| Cholesterol_mg/dL | Numeric | 50–400 | Total cholesterol |
| Blood_Pressure_mmHg | Numeric | 60–220 | Systolic BP |
| Glucose_mg/dL | Numeric | 40–400 | Fasting blood glucose |
| Weekly_Exercise_Hours | Numeric | 0–40 | Hours/week |
| Adherence_to_Diet_Plan | Numeric | 0–100 | Percentage |
| Dietary_Nutrient_Imbalance_Score | Numeric | 0–5 | Composite score |
| Gender | Categorical | Male/Female | Biological sex |
| Disease_Type | Categorical | None/Diabetes/Hypertension/Obesity | Primary diagnosis |
| Severity | Categorical | Mild/Moderate/Severe | Disease severity |
| Physical_Activity_Level | Categorical | Sedentary/Moderate/Active | Activity classification |
| Dietary_Restrictions | Categorical | None/Low_Sodium/Low_Sugar | Dietary restrictions |
| Allergies | Categorical | None/Gluten/Peanuts | Known allergens |
| Preferred_Cuisine | Categorical | Indian/Chinese/Italian/Mexican | Cuisine preference |

---

## Evaluation Metrics

| Model | Metric | Value | Notes |
|---|---|---|---|
| Diet classifier | 5-fold CV accuracy | 1.00 | ⚠️ Indicates overfitting on synthetic data |
| Risk regressor | RMSE | 3.93 | On synthetic test split |
| Meal classifier | 5-fold CV accuracy | 1.00 | ⚠️ Indicates overfitting on synthetic data |

> **Important**: CV accuracy of 1.0 is a strong indicator of dataset memorisation. Real-world performance with NHANES data is expected to be 0.75–0.88 (typical for this problem class per literature).

---

## Explainability

SHAP explanations are computed via `shap.TreeExplainer` (Lundberg & Lee, 2017) and returned with every `/predict` response when `SHAP_ENABLED=true`. The top-5 features by absolute SHAP value are surfaced to the user.

**Confidence Intervals**: 90% CI on risk score is derived from the 5th/95th percentile of individual Random Forest tree predictions, implementing the Meinshausen (2006) Quantile Regression Forest method.

---

## Known Limitations

1. **Synthetic training data** — models may not generalise to real patient populations
2. **Binary gender encoding** — non-binary gender identities are not represented
3. **Limited cuisine coverage** — only 4 cuisines (Indian, Chinese, Italian, Mexican)
4. **No temporal modelling** — snapshot-only, no longitudinal health trajectory
5. **No medication interaction modelling** — drug effects on biomarkers ignored
6. **Single disease label** — comorbidities (Diabetes + Hypertension) are not modelled
7. **English-only** — all outputs are in English regardless of patient language

---

## Bias Analysis

### Demographic Bias
- Training data is synthetically balanced across disease conditions (25% each)
- Real-world disease prevalence differs significantly (NHANES: Diabetes ~10%, Hypertension ~46%)
- Ethnic and socioeconomic factors are absent — both are known confounders for dietary patterns

### Measurement Bias
- Blood pressure is systolic-only (diastolic ignored)
- Cholesterol is total-only (LDL/HDL split not available)
- Glucose is fasting-only (post-prandial not captured)

### Recommendation Bias
- Diet protocols are a simplification of clinical guidelines (ADA, DASH, Dietary Guidelines for Americans)
- Low-Sodium is assigned deterministically to Hypertension — real-world protocols are more nuanced

---

## Ethical Considerations

- This system is **not a medical device** under FDA/CE regulation
- Outputs must not be used without physician review
- Patient data should be processed in compliance with HIPAA/GDPR
- The system disclaimer ("Always consult a licensed dietitian or physician") is mandatory in all user interfaces

---

## Citation

```bibtex
@software{nutriplanner2024,
  title   = {NutriPlanner: ML-Powered Clinical Nutrition Recommendation System},
  year    = {2024},
  version = {1.0.0},
  url     = {https://github.com/your-org/nutriplanner},
  note    = {Gradient Boosting + Random Forest ensemble for personalised dietary guidance}
}
```

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2024 | Initial release — synthetic data, 3-model ensemble |
| 2.0.0 | 2025 | Added SHAP explainability and confidence intervals |
| 3.0.0 | 2026 | Layered architecture, structlog, rate limiting |

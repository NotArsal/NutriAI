# Research Datasets for NutriPlanner

This document identifies real-world clinical datasets to replace the current synthetic 1,000-record training set, along with a complete preprocessing pipeline.

---

## Recommended Datasets

### 1. NHANES — National Health and Nutrition Examination Survey
**Best for:** Glucose, BMI, blood pressure, dietary intake, physical activity, demographics

| Property | Detail |
|---|---|
| Source | US Centers for Disease Control (CDC) |
| Size | ~40,000 participants per 2-year cycle |
| Download | https://wwwn.cdc.gov/nchs/nhanes/ |
| Format | SAS XPT files (readable with `pandas` + `pyreadstat`) |
| Key files | `DEMO_*.XPT` (demographics), `BMX_*.XPT` (BMI), `BPX_*.XPT` (BP), `GLU_*.XPT` (glucose), `TCHOL_*.XPT` (cholesterol), `PAQIAF_*.XPT` (physical activity), `DR1TOT_*.XPT` (dietary recall) |
| License | Public domain (US Government) |
| Cycle | Use 2017–2018 (most recent pre-pandemic, largest) |

**Recommended merge:**
```python
# Merge on SEQN (participant ID)
import pandas as pd
import pyreadstat

demo, _ = pyreadstat.read_xport("DEMO_J.XPT")  # demographics
bmx, _  = pyreadstat.read_xport("BMX_J.XPT")   # body measures
bpx, _  = pyreadstat.read_xport("BPX_J.XPT")   # blood pressure
glu, _  = pyreadstat.read_xport("GLU_J.XPT")   # glucose
chol, _ = pyreadstat.read_xport("TCHOL_J.XPT") # cholesterol
paq, _  = pyreadstat.read_xport("PAQ_J.XPT")   # physical activity

df = demo.merge(bmx, on="SEQN").merge(bpx, on="SEQN").merge(glu, on="SEQN") \
         .merge(chol, on="SEQN").merge(paq, on="SEQN")
```

---

### 2. UCI Heart Disease Dataset
**Best for:** Cardiovascular risk features — age, cholesterol, blood pressure, chest pain type

| Property | Detail |
|---|---|
| Source | UCI ML Repository — Cleveland Clinic Foundation |
| Size | 303 patients (14 features) |
| Download | https://archive.ics.uci.edu/dataset/45/heart+disease |
| Format | CSV |
| License | CC BY 4.0 |

```python
from ucimlrepo import fetch_ucirepo
heart = fetch_ucirepo(id=45)
X = heart.data.features
y = heart.data.targets
```

---

### 3. Diabetes Health Indicators Dataset (Kaggle)
**Best for:** Diabetes classification with 21 CDC behavioral risk features

| Property | Detail |
|---|---|
| Source | Kaggle — derived from BRFSS 2015 CDC survey |
| Size | 70,692 records (balanced) |
| Download | https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset |
| Format | CSV |
| License | CC0: Public Domain |
| Key features | HighBP, HighChol, BMI, Smoker, PhysActivity, Fruits, Veggies, Age, Sex |

---

### 4. Food-101 Nutrition Dataset (supplementary)
**Best for:** Meal classification by cuisine/macros

| Property | Detail |
|---|---|
| Source | ETH Zürich + USDA FoodData Central |
| USDA API | https://fdc.nal.usda.gov/api-guide.html (free API key) |
| Format | JSON (API) |

---

## Complete Preprocessing Pipeline

```python
"""
scripts/preprocess_nhanes.py
Run: python scripts/preprocess_nhanes.py
Output: ml/training_data.csv (ready for model retraining)
"""
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import KNNImputer
import pyreadstat
from pathlib import Path

DATA_DIR = Path("data/nhanes")

def load_nhanes() -> pd.DataFrame:
    demo, _ = pyreadstat.read_xport(DATA_DIR / "DEMO_J.XPT")
    bmx, _  = pyreadstat.read_xport(DATA_DIR / "BMX_J.XPT")
    bpx, _  = pyreadstat.read_xport(DATA_DIR / "BPX_J.XPT")
    glu, _  = pyreadstat.read_xport(DATA_DIR / "GLU_J.XPT")
    chol, _ = pyreadstat.read_xport(DATA_DIR / "TCHOL_J.XPT")
    paq, _  = pyreadstat.read_xport(DATA_DIR / "PAQ_J.XPT")

    df = (demo
          .merge(bmx,  on="SEQN", how="inner")
          .merge(bpx,  on="SEQN", how="inner")
          .merge(glu,  on="SEQN", how="inner")
          .merge(chol, on="SEQN", how="inner")
          .merge(paq,  on="SEQN", how="left"))

    # Rename to NutriPlanner feature names
    df = df.rename(columns={
        "RIDAGEYR": "Age",
        "RIAGENDR": "Gender",         # 1=Male, 2=Female
        "BMXWT":   "Weight_kg",
        "BMXHT":   "Height_cm",
        "BMXBMI":  "BMI",
        "BPXSY1":  "Blood_Pressure_mmHg",
        "LBXGLU":  "Glucose_mg/dL",
        "LBXTC":   "Cholesterol_mg/dL",
        "PAQ605":  "Weekly_Exercise_Hours",
    })

    # Gender encoding
    df["Gender"] = df["Gender"].map({1: "Male", 2: "Female"})

    # Exercise: PAQ605 = 1 if active, 2 if not
    # Convert to approx hours per week
    df["Weekly_Exercise_Hours"] = df["Weekly_Exercise_Hours"].map({1: 5.0, 2: 1.0}).fillna(2.0)

    # Derive disease labels from biomarkers (clinical thresholds)
    df["Disease_Type"] = "None"
    df.loc[df["Glucose_mg/dL"] >= 126, "Disease_Type"] = "Diabetes"
    df.loc[df["Blood_Pressure_mmHg"] >= 130, "Disease_Type"] = "Hypertension"
    df.loc[df["BMI"] >= 30, "Disease_Type"] = "Obesity"

    # Severity from deviation from normal
    def assign_severity(row):
        if row["Disease_Type"] == "Diabetes":
            if row["Glucose_mg/dL"] > 200: return "Severe"
            if row["Glucose_mg/dL"] > 150: return "Moderate"
            return "Mild"
        if row["Disease_Type"] == "Hypertension":
            if row["Blood_Pressure_mmHg"] > 160: return "Severe"
            if row["Blood_Pressure_mmHg"] > 140: return "Moderate"
            return "Mild"
        return "Mild"

    df["Severity"] = df.apply(assign_severity, axis=1)

    # Derived target: Diet Protocol
    def assign_diet(row):
        if row["Disease_Type"] == "Diabetes": return "Low_Carb"
        if row["Disease_Type"] == "Hypertension": return "Low_Sodium"
        return "Balanced"

    df["Diet_Protocol"] = df.apply(assign_diet, axis=1)

    # Risk score (0–100) as continuous target
    df["Risk_Score"] = np.clip(
        (df["Glucose_mg/dL"] - 70) / 130 * 25 +
        (df["Blood_Pressure_mmHg"] - 90) / 90 * 25 +
        (df["Cholesterol_mg/dL"] - 150) / 100 * 20 +
        (df["BMI"] - 18.5) / 30 * 15 +
        df["Weekly_Exercise_Hours"].map(lambda x: 0 if x >= 5 else 4 if x >= 2 else 10) +
        np.random.uniform(0, 5, len(df)),  # noise to prevent over-determinism
        0, 100
    )

    # KNN imputation for missing values
    numeric_cols = ["Age", "Weight_kg", "Height_cm", "BMI",
                    "Blood_Pressure_mmHg", "Glucose_mg/dL", "Cholesterol_mg/dL",
                    "Weekly_Exercise_Hours", "Risk_Score"]
    imputer = KNNImputer(n_neighbors=5)
    df[numeric_cols] = imputer.fit_transform(df[numeric_cols])

    # Filter adults only
    df = df[df["Age"] >= 18].copy()

    # Drop rows with critical missing values
    df = df.dropna(subset=["Gender", "Disease_Type"])

    return df[["Age", "Gender", "Weight_kg", "Height_cm", "BMI",
               "Blood_Pressure_mmHg", "Glucose_mg/dL", "Cholesterol_mg/dL",
               "Weekly_Exercise_Hours", "Disease_Type", "Severity",
               "Diet_Protocol", "Risk_Score"]]


if __name__ == "__main__":
    df = load_nhanes()
    print(f"Loaded {len(df)} records, shape: {df.shape}")
    print(df["Disease_Type"].value_counts())
    output = Path("ml/training_data.csv")
    output.parent.mkdir(exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved to {output}")
```

---

## Model Retraining Script

After running the preprocessing pipeline, retrain the models:

```python
"""
scripts/retrain_models.py
Run: python scripts/retrain_models.py
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error

DATA_PATH = Path("ml/training_data.csv")
OUTPUT_DIR = Path("ml")

df = pd.read_csv(DATA_PATH)

# Encode categoricals
le_gender   = LabelEncoder().fit(["Female", "Male"])
le_disease  = LabelEncoder().fit(["Diabetes", "Hypertension", "None", "Obesity"])
le_severity = LabelEncoder().fit(["Mild", "Moderate", "Severe"])
le_diet     = LabelEncoder().fit(["Balanced", "Low_Carb", "Low_Sodium"])

df["Gender_enc"]      = le_gender.transform(df["Gender"])
df["Disease_Type_enc"] = le_disease.transform(df["Disease_Type"])
df["Severity_enc"]    = le_severity.transform(df["Severity"])
df["Diet_enc"]        = le_diet.transform(df["Diet_Protocol"])

FEATURES = ["Age", "Weight_kg", "Height_cm", "BMI",
            "Glucose_mg/dL", "Cholesterol_mg/dL", "Blood_Pressure_mmHg",
            "Weekly_Exercise_Hours", "Gender_enc", "Disease_Type_enc", "Severity_enc"]

X = df[FEATURES].values
y_diet = df["Diet_enc"].values
y_risk = df["Risk_Score"].values

# Diet model — Gradient Boosting
diet_model = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
diet_cv    = cross_val_score(diet_model, X, y_diet, cv=5, scoring="accuracy")
diet_model.fit(X, y_diet)
print(f"Diet CV accuracy: {diet_cv.mean():.3f} ± {diet_cv.std():.3f}")

# Risk model — Random Forest (enables per-tree CI)
risk_model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)
risk_model.fit(X, y_risk)
rmse = mean_squared_error(y_risk, risk_model.predict(X), squared=False)
print(f"Risk RMSE: {rmse:.2f}")

# Save
joblib.dump(diet_model, OUTPUT_DIR / "diet_model.pkl")
joblib.dump(risk_model, OUTPUT_DIR / "risk_model.pkl")
print("Models saved.")
```

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
import joblib
import os
import json

# 1. Load Data
data_path = r"D:\Projects\nutriai_backend\datasets\diet_recommendations_dataset.csv"
df = pd.read_csv(data_path)

print("--- Diet Recommendation Dataset Info ---")
print(f"Shape: {df.shape}")

# 2. Preprocessing
target = 'Diet_Recommendation'
df = df.drop(columns=['Patient_ID'], errors='ignore')
features = df.columns.drop(target)

# Encoders dict to save later
encoders = {}
X = df[features].copy()
y = df[target].copy()

# Encode Categorical Features
cat_cols = X.select_dtypes(include=['object', 'category']).columns
for col in cat_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    encoders[col] = le.classes_.tolist()

# Encode Target
le_target = LabelEncoder()
y = le_target.fit_transform(y)
encoders['target'] = le_target.classes_.tolist()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Model Training & Comparison
print("\n--- Model Training & Comparison ---")
models = {
    "Logistic Regression (Baseline)": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(random_state=42),
    "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
}

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    results[name] = {"Accuracy": acc, "F1-Score": f1}
    print(f"{name} -> Accuracy: {acc:.4f} | F1-Score: {f1:.4f}")

# 4. Hyperparameter Tuning (XGBoost usually wins, let's tune Random Forest and XGBoost)
print("\n--- Tuning XGBoost ---")
xgb = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.2]
}
grid = GridSearchCV(xgb, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid.fit(X_train, y_train)
best_model = grid.best_estimator_

y_pred_best = best_model.predict(X_test)
best_acc = accuracy_score(y_test, y_pred_best)
best_f1 = f1_score(y_test, y_pred_best, average='weighted')

print(f"Best XGBoost Params: {grid.best_params_}")
print(f"Best Model Test Accuracy: {best_acc:.4f} | F1-Score: {best_f1:.4f}")
print("\nClassification Report:\n", classification_report(y_test, y_pred_best, target_names=le_target.classes_))

# 5. Save the best model
out_dir = r"D:\Projects\nutriai_backend\ml"
os.makedirs(out_dir, exist_ok=True)

joblib.dump(best_model, os.path.join(out_dir, "new_diet_classifier.pkl"))
joblib.dump(list(X.columns), os.path.join(out_dir, "new_diet_features.pkl"))

meta = {
    "target_classes": encoders['target'],
    "feature_encoders": {k: v for k, v in encoders.items() if k != 'target'}
}
with open(os.path.join(out_dir, "new_diet_meta.json"), "w") as f:
    json.dump(meta, f, indent=4)

print(f"\nModel and metadata saved to {out_dir}")

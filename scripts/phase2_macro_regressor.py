import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

print("--- Building Macro Regressor ---")

# 1. Load Data
data_path = r"D:\Projects\nutriai_backend\datasets\final_nutrition_dataset.csv"
df = pd.read_csv(data_path)

print(f"Dataset Shape: {df.shape}")

# 2. Features and Targets
# We want to predict Daily Calories and Daily Protein based on Age and Weight
# Input features
X = df[['Age (years)', 'Weight_Energy']].copy()
X.columns = ['Age', 'Weight'] # Rename for simplicity

# Target variables (Energy Requirement kcal/day, Protein RDA g/day)
y = df[['Energy Requirement (kcal/day)', 'RDA (g/day)']].copy()
y.columns = ['Calories', 'Protein']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train Model
# A Random Forest Regressor handles multi-output regression natively
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 4. Evaluate
y_pred = model.predict(X_test)
mae_cal = mean_absolute_error(y_test['Calories'], y_pred[:, 0])
mae_pro = mean_absolute_error(y_test['Protein'], y_pred[:, 1])
r2 = r2_score(y_test, y_pred)

print(f"Macro Regressor Performance:")
print(f"MAE Calories: {mae_cal:.2f} kcal")
print(f"MAE Protein: {mae_pro:.2f} g")
print(f"R² Score: {r2:.4f}")

# 5. Save Model
out_dir = r"D:\Projects\nutriai_backend\ml"
os.makedirs(out_dir, exist_ok=True)

joblib.dump(model, os.path.join(out_dir, "new_macro_regressor.pkl"))
print("Model saved to ml/new_macro_regressor.pkl")

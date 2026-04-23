import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import NearestNeighbors
import joblib
import os
import json

print("--- Building KNN Meal Recommender ---")

# 1. Load Data
data_path = r"D:\Projects\nutriai_backend\datasets\Food_and_Nutrition__.csv"
df = pd.read_csv(data_path)

print(f"Dataset Shape: {df.shape}")

# 2. Preprocessing
# We want to recommend meals based on nutritional targets and restrictions
# The key features to match on: Calories, Protein, Carbohydrates, Fat, Sodium
num_features = ['Calories', 'Protein', 'Carbohydrates', 'Fat', 'Sodium']

# We also want to loosely match on Disease and Dietary Preference by one-hot encoding or weighting them.
# For a simple robust KNN, matching on purely numerical macros is best, and we can filter by diet/disease beforehand,
# OR we can include encoded categorical variables with high weight so the KNN penalty is huge for mismatches.
# Let's include Dietary Preference and Disease.

cat_features = ['Dietary Preference', 'Disease']
encoders = {}

X = df[num_features].copy()

# Ensure numeric types
for col in num_features:
    X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

for col in cat_features:
    le = LabelEncoder()
    # fill na just in case
    df[col] = df[col].fillna("None")
    X[col] = le.fit_transform(df[col])
    # multiply by a large weight (e.g., 1000) so KNN strictly tries to match the category
    X[col] = X[col] * 1000 
    encoders[col] = le.classes_.tolist()

# Standardize numerical features
scaler = StandardScaler()
X[num_features] = scaler.fit_transform(X[num_features])

# 3. Train NearestNeighbors Model
# algorithm='brute' is fast enough for ~1700 rows and allows flexible distance metrics.
knn = NearestNeighbors(n_neighbors=3, metric='euclidean', algorithm='brute')
knn.fit(X)

# 4. Save the Model and necessary data for inference
out_dir = r"D:\Projects\nutriai_backend\ml"
os.makedirs(out_dir, exist_ok=True)

joblib.dump(knn, os.path.join(out_dir, "new_meal_knn.pkl"))
joblib.dump(scaler, os.path.join(out_dir, "new_meal_scaler.pkl"))

# Save the target columns to map index back to meal suggestions
suggestions_df = df[['Breakfast Suggestion', 'Lunch Suggestion', 'Dinner Suggestion', 'Snack Suggestion', 'Calories', 'Protein', 'Dietary Preference', 'Disease']]
joblib.dump(suggestions_df, os.path.join(out_dir, "new_meal_database.pkl"))

meta = {
    "num_features": num_features,
    "cat_features": cat_features,
    "encoders": encoders,
    "weight_penalty": 1000
}
with open(os.path.join(out_dir, "new_meal_meta.json"), "w") as f:
    json.dump(meta, f, indent=4)

print("KNN Model, Scaler, and Meal Database saved successfully.")

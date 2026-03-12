"""
Crop Recommendation v2.2 — Top-3 Recommendations
=================================================
"""

import joblib
import numpy as np
import pandas as pd

model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "season", "soil_type", "irrigation"]

input_data = {
    "N": 23, "P": 43, "K": 43,
    "temperature": 32, "humidity": 32,
    "ph": 5, "rainfall": 2355,
    "season": 0,      # Kharif
    "soil_type": 1,   # Loamy
    "irrigation": 1,  # Irrigated
}

X = pd.DataFrame([input_data])[FEATURES]

proba = model.predict_proba(X)[0]
top3_idx = np.argsort(proba)[-3:][::-1]
top3_labels = label_encoder.inverse_transform(top3_idx)
top3_scores = proba[top3_idx]

season_names = {0: "Kharif", 1: "Rabi", 2: "Zaid"}
soil_names = {0: "sandy", 1: "loamy", 2: "clay"}
irrig_names = {0: "rainfed", 1: "irrigated"}

print("=" * 50)
print("TOP 3 CROP RECOMMENDATIONS (v2.2)")
print("=" * 50)
print(f"Season:     {season_names.get(input_data['season'], '?')}")
print(f"Soil:       {soil_names.get(input_data['soil_type'], '?')}")
print(f"Irrigation: {irrig_names.get(input_data['irrigation'], '?')}")
print()

for i, (crop, score) in enumerate(zip(top3_labels, top3_scores), start=1):
    print(f"  {i}. {crop}  ({score*100:.2f}%)")

print("=" * 50)
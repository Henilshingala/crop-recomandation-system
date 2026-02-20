"""
Crop Recommendation v2.2 — Single Inference Test
=================================================
"""


import joblib
import pandas as pd

model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "season", "soil_type", "irrigation"]

print("=" * 60)
print("CROP PREDICTION — v2.2 (CALIBRATED)")
print("=" * 60)

# Season: 0=Kharif, 1=Rabi, 2=Zaid
# Soil:   0=sandy,  1=loamy, 2=clay
# Irrigation: 0=rainfed, 1=irrigated
sample = {
    "N": 90, "P": 42, "K": 43,
    "temperature": 24.5, "humidity": 68,
    "ph": 6.7, "rainfall": 120,
    "season": 1,      # Rabi
    "soil_type": 1,   # Loamy
    "irrigation": 1,  # Irrigated
}

X_new = pd.DataFrame([sample])[FEATURES]

pred_encoded = model.predict(X_new)[0]
pred_label = label_encoder.inverse_transform([pred_encoded])[0]

season_names = {0: "Kharif", 1: "Rabi", 2: "Zaid"}
soil_names = {0: "sandy", 1: "loamy", 2: "clay"}
irrig_names = {0: "rainfed", 1: "irrigated"}

print("Input parameters:")
for k, v in sample.items():
    if k == "season":
        print(f"  {k:12s}: {v} ({season_names.get(v, '?')})")
    elif k == "soil_type":
        print(f"  {k:12s}: {v} ({soil_names.get(v, '?')})")
    elif k == "irrigation":
        print(f"  {k:12s}: {v} ({irrig_names.get(v, '?')})")
    else:
        print(f"  {k:12s}: {v}")

print(f"\nPredicted crop: {pred_label}")
print("=" * 60)
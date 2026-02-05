import joblib
import pandas as pd

# ===============================
# LOAD SAVED ARTIFACTS
# ===============================
model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")

FEATURES = [
    "N", "P", "K",
    "temperature", "humidity", "ph", "rainfall"
]

print("=" * 60)
print("STEP 7 — CROP PREDICTION (INFERENCE MODE)")
print("=" * 60)

# ===============================
# SAMPLE INPUT (CHANGE THIS)
# ===============================
sample = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 24.5,
    "humidity": 68,
    "ph": 6.7,
    "rainfall": 120
}

X_new = pd.DataFrame([sample])[FEATURES]

# ===============================
# PREDICTION
# ===============================
pred_encoded = model.predict(X_new)[0]
pred_label = label_encoder.inverse_transform([pred_encoded])[0]

# ===============================
# OUTPUT
# ===============================
print("Input parameters:")
for k, v in sample.items():
    print(f"  {k:12s}: {v}")

print("\nPredicted crop:")
print(f"  ➜ {pred_label}")

print("=" * 60)
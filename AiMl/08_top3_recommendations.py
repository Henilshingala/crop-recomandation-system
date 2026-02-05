import joblib
import numpy as np
import pandas as pd

# Load trained assets
model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")

# -------------------------------
# INPUT (change values anytime)
# -------------------------------
input_data = {
    "N" : 100,
    "P" : 50,
    "K" : 50,
    "temperature" : 26,
    "humidity" : 88,
    "ph" : 6.5,
    "rainfall" : 260
}

# Convert to DataFrame
X = pd.DataFrame([input_data])

# Predict probabilities
proba = model.predict_proba(X)[0]

# Get top 3 indices
top3_idx = np.argsort(proba)[-3:][::-1]

# Decode labels
top3_labels = label_encoder.inverse_transform(top3_idx)
top3_scores = proba[top3_idx]

# -------------------------------
# OUTPUT
# -------------------------------
print("=" * 50)
print("TOP 3 CROP RECOMMENDATIONS")
print("=" * 50)

for i, (crop, score) in enumerate(zip(top3_labels, top3_scores), start=1):
    print(f"{i}. {crop}  ({score*100:.2f}%)")

print("=" * 50)
import joblib
import numpy as np
import pandas as pd

model = joblib.load("D:\downloads\CRS\AiMl\model_rf.joblib")
label_encoder = joblib.load("D:\downloads\CRS\AiMl\label_encoder.joblib")

input_data = {
    "N" : 23,
    "P" : 43,
    "K" : 43,
    "temperature" : 32,
    "humidity" : 32,
    "ph" : 5,
    "rainfall" : 2355
}

X = pd.DataFrame([input_data])

# Predict probabilities
proba = model.predict_proba(X)[0]

# Get top 3 indices
top3_idx = np.argsort(proba)[-3:][::-1]

# Decode labels
top3_labels = label_encoder.inverse_transform(top3_idx)
top3_scores = proba[top3_idx]

print("=" * 50)
print("TOP 3 CROP RECOMMENDATIONS")
print("=" * 50)

for i, (crop, score) in enumerate(zip(top3_labels, top3_scores), start=1):
    print(f"{i}. {crop}  ({score*100:.2f}%)")

print("=" * 50)
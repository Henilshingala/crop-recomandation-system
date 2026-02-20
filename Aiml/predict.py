"""
Crop Recommendation v2.2 — Prediction Script
=============================================
Loads the v2.2 calibrated model and makes predictions.
Includes season + soil_type + irrigation features.
"""

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "model_rf.joblib"
ENCODER_PATH = "label_encoder.joblib"

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "season", "soil_type", "irrigation"]

SEASON_REVERSE = {0: "Kharif", 1: "Rabi", 2: "Zaid"}
SOIL_REVERSE = {0: "sandy", 1: "loamy", 2: "clay"}
IRRIG_REVERSE = {0: "rainfed", 1: "irrigated"}

print("Loading v2.2 calibrated model …")
model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)


def infer_season(temperature: float) -> int:
    if temperature >= 28: return 0
    elif temperature <= 22: return 1
    else: return 2


def predict_top_crops(input_dict: dict, top_n: int = 3):
    if "season" not in input_dict:
        input_dict["season"] = infer_season(input_dict["temperature"])
    if "soil_type" not in input_dict:
        input_dict["soil_type"] = 1  # default loamy
    if "irrigation" not in input_dict:
        input_dict["irrigation"] = 0  # default rainfed

    X = pd.DataFrame([input_dict])[FEATURES]
    proba = model.predict_proba(X)[0]
    top_idx = np.argsort(proba)[-top_n:][::-1]

    results = []
    for rank, idx in enumerate(top_idx, start=1):
        crop_name = label_encoder.inverse_transform([idx])[0]
        results.append({
            "rank": rank,
            "crop": crop_name,
            "confidence": round(float(proba[idx]) * 100, 2),
        })
    return results


if __name__ == "__main__":
    test_input = {
        "N": 100, "P": 50, "K": 50,
        "temperature": 28, "humidity": 85,
        "ph": 6.5, "rainfall": 2000,
        "soil_type": 2,  # clay
        "irrigation": 1,  # irrigated
    }

    print("\n" + "=" * 60)
    print("PREDICTION DEMO (v2.2 — Calibrated)")
    print("=" * 60)
    print("Input:")
    for k, v in test_input.items():
        if k == "soil_type":
            print(f"  {k:12s}: {v} ({SOIL_REVERSE.get(v, '?')})")
        elif k == "irrigation":
            print(f"  {k:12s}: {v} ({IRRIG_REVERSE.get(v, '?')})")
        else:
            print(f"  {k:12s}: {v}")

    results = predict_top_crops(test_input, top_n=5)
    season = infer_season(test_input["temperature"])
    print(f"\nInferred Season: {SEASON_REVERSE[season]}")
    print("\nTop 5 Recommendations:")
    for r in results:
        print(f"  {r['rank']}. {r['crop']:20s} ({r['confidence']:.1f}%)")
    print("=" * 60)

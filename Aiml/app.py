"""
Crop Recommendation ML API — HuggingFace Space (v2.2)
======================================================
FastAPI service with calibrated model, season + soil_type + irrigation features.
"""

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="Crop Recommendation ML API", version="2.2")

model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")
try:
    nutrients_df = pd.read_csv("Nutrient.csv")
except FileNotFoundError:
    nutrients_df = pd.DataFrame()

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "season", "soil_type", "irrigation"]

SEASON_MAP = {"Kharif": 0, "Rabi": 1, "Zaid": 2}
SEASON_REVERSE = {0: "Kharif", 1: "Rabi", 2: "Zaid"}
SOIL_MAP = {"sandy": 0, "loamy": 1, "clay": 2}
SOIL_REVERSE = {0: "sandy", 1: "loamy", 2: "clay"}
IRRIG_MAP = {"rainfed": 0, "irrigated": 1}
IRRIG_REVERSE = {0: "rainfed", 1: "irrigated"}


def infer_season(temperature: float) -> int:
    if temperature >= 28:
        return 0
    elif temperature <= 22:
        return 1
    else:
        return 2


class PredictionInput(BaseModel):
    N: float = Field(..., description="Nitrogen content (kg/ha)")
    P: float = Field(..., description="Phosphorus content (kg/ha)")
    K: float = Field(..., description="Potassium content (kg/ha)")
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Humidity (%)")
    ph: float = Field(..., description="Soil pH")
    rainfall: float = Field(..., description="Rainfall (mm)")
    season: Optional[int] = Field(
        None,
        description="Season (0=Kharif, 1=Rabi, 2=Zaid). Auto-inferred if not provided."
    )
    soil_type: Optional[int] = Field(
        1,
        description="Soil type (0=sandy, 1=loamy, 2=clay). Defaults to loamy."
    )
    irrigation: Optional[int] = Field(
        0,
        description="Irrigation (0=rainfed, 1=irrigated). Defaults to rainfed."
    )
    top_n: Optional[int] = Field(3, description="Number of top predictions to return")


def get_nutrition(crop_name: str) -> Optional[dict]:
    try:
        if nutrients_df is None or nutrients_df.empty or "food_name" not in nutrients_df.columns:
            return None
        nutrient_row = nutrients_df[
            nutrients_df["food_name"].str.lower().str.contains(
                crop_name.lower(), na=False
            )
        ]
        if not nutrient_row.empty:
            row = nutrient_row.iloc[0]
            return {
                "protein_g": float(row["protein_g_per_kg"]),
                "fat_g": float(row["fat_g_per_kg"]),
                "carbs_g": float(row["carbs_g_per_kg"]),
                "fiber_g": float(row["fiber_g_per_kg"]),
                "iron_mg": float(row["iron_mg_per_kg"]),
                "calcium_mg": float(row["calcium_mg_per_kg"]),
                "vitamin_a_mcg": float(row["vitamin_a_mcg_per_kg"]),
                "vitamin_c_mg": float(row["vitamin_c_mg_per_kg"]),
                "energy_kcal": float(row["energy_kcal_per_kg"]),
                "water_g": float(row["water_g_per_kg"]),
            }
    except Exception:
        pass
    return None


@app.post("/predict")
def predict(data: PredictionInput):
    try:
        season = data.season if data.season is not None else infer_season(data.temperature)
        soil_type = data.soil_type if data.soil_type is not None else 1
        irrigation = data.irrigation if data.irrigation is not None else 0
        top_n = data.top_n or 3

        input_dict = {
            "N": data.N, "P": data.P, "K": data.K,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "ph": data.ph,
            "rainfall": data.rainfall,
            "season": season,
            "soil_type": soil_type,
            "irrigation": irrigation,
        }
        df = pd.DataFrame([input_dict])[FEATURES]

        probs = model.predict_proba(df)[0]
        top_indices = np.argsort(probs)[-top_n:][::-1]

        predictions = []
        for idx in top_indices:
            crop_name = label_encoder.inverse_transform([idx])[0]
            confidence = float(probs[idx])
            nutrition = get_nutrition(crop_name)
            predictions.append({
                "crop": crop_name,
                "confidence": confidence,
                "nutrition": nutrition,
            })

        return {
            "predictions": predictions,
            "season_used": SEASON_REVERSE.get(season, "Unknown"),
            "soil_type_used": SOIL_REVERSE.get(soil_type, "Unknown"),
            "irrigation_used": IRRIG_REVERSE.get(irrigation, "Unknown"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def health():
    return {
        "status": "ML Model is Live",
        "model_version": "2.2",
        "model_loaded": True,
        "calibrated": True,
        "available_crops": list(label_encoder.classes_),
        "features": FEATURES,
    }


@app.get("/crops")
def get_crops():
    return {"crops": list(label_encoder.classes_)}

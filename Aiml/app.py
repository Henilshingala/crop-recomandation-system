"""
Crop Recommendation ML API — V3 Stacked Ensemble
===============================================
Statistically optimal model with real-world data integration.
Features: 11 parameters (includes moisture).
Architecture: Stacked Ensemble (RF + XGB + LGBM) with Bayesian Calibration.
"""

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_api_v3")

app = FastAPI(title="Crop Recommendation ML API", version="3.0")

# ═══════════════════════════════════════════════════════════════════════════
# LOAD ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

try:
    logger.info("Loading V3 Stacked Ensemble artifacts...")
    stacked_model = joblib.load("stacked_ensemble_v3.joblib")
    label_encoder = joblib.load("label_encoder_v3.joblib")
    config = joblib.load("stacked_v3_config.joblib")
    nutrients_df = pd.read_csv("Nutrient.csv")
    
    FOLD_MODELS = stacked_model["fold_models"]
    META_LEARNER = stacked_model["meta_learner"]
    FEATURES = config["feature_names"]  # ['n', 'p', 'k', ...]
    
    # Inference Tuning Params
    TEMPERATURE = config.get("temperature", 1.0)
    INV_FREQ_WEIGHTS = np.array(config.get("inv_freq_weights", []))
    CLASS_THRESHOLDS = np.array(config.get("class_thresholds", []))
    ENTROPY_THRESHOLD = config.get("entropy_threshold", 0.4)
    DOMINANCE_PENALTY = config.get("dominance_penalty", 0.15)
    
    logger.info("✓ V3 Artifacts loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load V3 artifacts: {e}")
    # Fallback/Safe state for startup
    FEATURES = ["n", "p", "k", "temperature", "humidity", "ph", "rainfall", "season", "soil_type", "irrigation", "moisture"]

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES & POST-PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def apply_temperature(proba: np.ndarray, T: float) -> np.ndarray:
    if T == 1.0: return proba
    log_p = np.log(np.clip(proba, 1e-10, 1.0))
    scaled = log_p / T
    scaled -= scaled.max()
    e = np.exp(scaled)
    return e / e.sum()

def apply_inv_freq(proba: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if len(weights) == 0: return proba
    adj = proba * weights
    return adj / (adj.sum() + 1e-10)

def apply_entropy_penalty(proba: np.ndarray, threshold: float, penalty: float) -> np.ndarray:
    ent = -np.sum(proba * np.log(proba + 1e-10))
    if ent < threshold:
        top = np.argmax(proba)
        removed = proba[top] * penalty
        proba[top] -= removed
        others = np.ones(len(proba), dtype=bool)
        others[top] = False
        s = proba[others].sum()
        if s > 0:
            proba[others] += removed * (proba[others] / s)
    return proba

def infer_season(temperature: float) -> int:
    if temperature >= 28: return 0  # Kharif
    elif temperature <= 22: return 1 # Rabi
    else: return 2 # Zaid

# ═══════════════════════════════════════════════════════════════════════════
# API MODELS & HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

# Crop name mapping for nutrition lookup (Real-world -> Nutrient.csv names)
NUTRITION_MAPPING = {
    "pigeonpea": "pigeonpeas",
    "sesamum": "sesame",
    "pearl_millet": "bajra",
    "finger_millet": "ragi",
    "sorghum": "jowar",
}

class PredictionInput(BaseModel):
    N: float = Field(..., ge=0, le=300, description="Nitrogen content (kg/ha)")
    P: float = Field(..., ge=0, le=200, description="Phosphorus content (kg/ha)")
    K: float = Field(..., ge=0, le=200, description="Potassium content (kg/ha)")
    temperature: float = Field(..., ge=-10, le=55, description="Temperature (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Humidity (%)")
    ph: float = Field(..., ge=3.0, le=10.0, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=1000, description="Rainfall (mm)")
    moisture: Optional[float] = Field(43.5, ge=0, le=100, description="Soil moisture (%)")
    season: Optional[int] = Field(None, ge=0, le=2, description="0=Kharif, 1=Rabi, 2=Zaid")
    soil_type: Optional[int] = Field(1, ge=0, le=4, description="0=sandy, 1=loamy, 2=clay")
    irrigation: Optional[int] = Field(0, ge=0, le=1, description="0=rainfed, 1=irrigated")
    top_n: Optional[int] = Field(3, ge=1, le=10, description="Number of predictions to return")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    logger.error(f"Validation Error: {error_details}")
    return JSONResponse(
        status_code=422,
        content={"detail": error_details, "message": "Invalid input format or missing fields"}
    )

def get_nutrition(crop_name: str) -> Optional[dict]:
    try:
        # Use mapping for real-world crop names
        search_name = NUTRITION_MAPPING.get(crop_name.lower(), crop_name.lower())
        match = nutrients_df[nutrients_df["food_name"].str.contains(search_name, case=False, na=False)]
        if not match.empty:
            row = match.iloc[0]
            return {
                "protein_g": float(row["protein_g_per_kg"]),
                "fat_g": float(row["fat_g_per_kg"]),
                "carbs_g": float(row["carbs_g_per_kg"]),
                "fiber_g": float(row["fiber_g_per_kg"]),
                "iron_mg": float(row["iron_mg_per_kg"]),
                "calcium_mg": float(row["calcium_mg_per_kg"]),
                "energy_kcal": float(row["energy_kcal_per_kg"]),
                "water_g": float(row["water_g_per_kg"]),
            }
    except (KeyError, ValueError) as e:
        logger.warning("Invalid nutrition data for %s: %s", crop_name, e)
    except Exception as e:
        logger.error("Unexpected error in nutrition lookup for %s: %s", crop_name, e)
    return None

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/predict")
async def predict(data: PredictionInput):
    try:
        # 1. Prepare Features
        season = data.season if data.season is not None else infer_season(data.temperature)
        
        # Map fields to match model's expected lower-case names
        input_data = {
            "n": data.N, "p": data.P, "k": data.K,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "ph": data.ph,
            "rainfall": data.rainfall,
            "moisture": data.moisture,
            "season": season,
            "soil_type": data.soil_type,
            "irrigation": data.irrigation
        }
        
        X = pd.DataFrame([input_data])[FEATURES]
        
        # 2. Base Model Predictions (OOO-style)
        base_preds = []
        for name in ["BalancedRF", "XGBoost", "LightGBM"]:
            model_list = FOLD_MODELS[name]
            # Average predictions across folds
            fold_probs = np.mean([m.predict_proba(X)[0] for m in model_list], axis=0)
            base_preds.append(fold_probs)
        
        # 3. Meta-Learner Prediction
        meta_features = np.hstack(base_preds).reshape(1, -1)
        proba = META_LEARNER.predict_proba(meta_features)[0]
        
        # 4. Post-processing
        proba = apply_temperature(proba, TEMPERATURE)
        proba = apply_inv_freq(proba, INV_FREQ_WEIGHTS)
        
        # Apply class thresholds if available
        if len(CLASS_THRESHOLDS) > 0:
            proba = proba / (CLASS_THRESHOLDS + 1e-10)
            proba = proba / proba.sum()
            
        proba = apply_entropy_penalty(proba, ENTROPY_THRESHOLD, DOMINANCE_PENALTY)
        
        # 5. Format Response
        top_n = data.top_n or 3
        top_indices = np.argsort(proba)[-top_n:][::-1]
        
        predictions = []
        for idx in top_indices:
            crop_name = label_encoder.inverse_transform([idx])[0]
            conf = float(proba[idx])
            predictions.append({
                "crop": crop_name,
                "confidence": round(conf * 100, 2),
                "nutrition": get_nutrition(crop_name)
            })
            
        return {
            "predictions": predictions,
            "model_info": {
                "version": "3.0",
                "type": "stacked-ensemble-v3",
                "features": len(FEATURES)
            },
            "environment_info": {
                "season_used": ["Kharif", "Rabi", "Zaid"][season],
                "inferred": data.season is None
            }
        }
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict")
def predict_hint():
    return {"message": "Use POST with JSON body.", "version": "3.0"}

@app.get("/")
def health():
    return {
        "status": "online",
        "version": "3.0",
        "model": "Stacked Ensemble v3 (Optimized)",
        "crops_supported": len(label_encoder.classes_)
    }

@app.get("/crops")
def get_crops():
    return {"crops": sorted(list(label_encoder.classes_))}

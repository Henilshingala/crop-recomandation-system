"""
Crop Recommendation ML API — V4 Production Ready
===============================================
Multi-model system with real, synthetic, and hybrid predictors.
Features: Dynamic model loading, proper scaling, no bias.
"""

import time
import json
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import os
from pathlib import Path

# Import V4 predictors
from predictors.real_v4 import RealPredictorV4
from predictors.synthetic_v4 import SyntheticPredictorV4
from predictors.both_v4 import BothPredictorV4
from config import config
from logging_config import structured_logger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_api_v4")

app = FastAPI(title="Crop Recommendation ML API", version="4.0")

# ═══════════════════════════════════════════════════════════════════════════
# LOAD ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

# Load nutrition data
try:
    nutrients_df = pd.read_csv("Nutrient.csv")
    logger.info("✓ Nutrition data loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load nutrition data: {e}")
    nutrients_df = pd.DataFrame()

# Crop name mapping for nutrition lookup
NUTRITION_MAPPING = {
    "pigeonpea": "pigeonpeas",
    "sesamum": "sesame",
    "pearl_millet": "bajra",
    "finger_millet": "ragi",
    "sorghum": "jowar",
}

# ═══════════════════════════════════════════════════════════════════════════
# API MODELS & HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

class PredictionInput(BaseModel):
    N: float = Field(..., description="Nitrogen content (kg/ha)")
    P: float = Field(..., description="Phosphorus content (kg/ha)")
    K: float = Field(..., description="Potassium content (kg/ha)")
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Humidity (%)")
    ph: float = Field(..., description="Soil pH")
    rainfall: float = Field(..., description="Rainfall (mm)")
    moisture: Optional[float] = Field(50.0, description="Soil moisture (%)")
    season: Optional[int] = Field(None, description="0=Kharif, 1=Rabi, 2=Zaid")
    soil_type: Optional[int] = Field(1, description="0=sandy, 1=loamy, 2=clay, 3=silty")
    irrigation: Optional[int] = Field(0, description="0=rainfed, 1=irrigated")
    mode: Optional[str] = Field("real", description="Prediction mode: real, synthetic, both")
    top_n: Optional[int] = Field(3, description="Number of top predictions to return")

VALID_MODES = {"real", "synthetic", "both"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    logger.error(f"Validation Error: {error_details}")
    return JSONResponse(
        status_code=422,
        content={"detail": error_details, "message": "Invalid input format or missing fields"},
    )

def get_nutrition(crop_name: str) -> Optional[dict]:
    """Get nutrition information for a crop."""
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
    except:
        pass
    return None

def _load_model_registry():
    """Load model registry configuration."""
    with open("model_registry.json", "r") as f:
        return json.load(f)

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/predict")
async def predict(data: PredictionInput):
    """Make crop prediction based on input parameters."""
    start_time = time.time()
    mode = (data.mode or "real").strip().lower()
    
    if mode not in VALID_MODES:
        structured_logger.log_error(
            "validation_error",
            f"Invalid mode '{mode}'",
            {"provided_mode": mode, "valid_modes": list(VALID_MODES)}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{mode}'. Must be one of: real, synthetic, both",
        )

    try:
        # Initialize predictor based on mode
        if mode == "real":
            predictor = RealPredictorV4()
        elif mode == "synthetic":
            predictor = SyntheticPredictorV4()
        else:  # both
            predictor = BothPredictorV4()
        
        # Prepare prediction parameters
        predict_params = {
            "N": data.N,
            "P": data.P,
            "K": data.K,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "ph": data.ph,
            "rainfall": data.rainfall,
            "top_n": data.top_n or 3,
            "season": data.season,
            "soil_type": data.soil_type,
            "irrigation": data.irrigation,
        }
        
        # Add moisture for real and both modes
        if mode in ["real", "both"]:
            predict_params["moisture"] = data.moisture
        
        # Make prediction
        result = predictor.predict(**predict_params)
        
        # Add nutrition information
        for pred in result["predictions"]:
            pred["nutrition"] = get_nutrition(pred["crop"])
        
        # Log prediction
        latency_ms = (time.time() - start_time) * 1000
        structured_logger.log_prediction(
            mode=mode,
            latency_ms=latency_ms,
            additional_data={
                "top_n": data.top_n or 3,
                "crop_count": len(result["predictions"]),
                "model_type": result["model_info"]["type"]
            }
        )
        
        return result
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        structured_logger.log_error(
            "prediction_error",
            str(e),
            {"mode": mode, "latency_ms": latency_ms}
        )
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict")
def predict_hint():
    """Get prediction endpoint information."""
    return {
        "message": "Use POST with JSON body for predictions.",
        "version": "4.0",
        "modes": list(VALID_MODES),
        "example": {
            "N": 50, "P": 30, "K": 40,
            "temperature": 25, "humidity": 65, "ph": 6.5, "rainfall": 100,
            "mode": "real", "top_n": 3
        }
    }

@app.get("/crops")
def get_crops():
    """Get available crops for each mode."""
    try:
        registry = _load_model_registry()
        
        crops_info = {}
        for mode_name, mode_config in registry["models"].items():
            if mode_name != "both":
                crops_info[mode_name] = {
                    "crop_count": mode_config["crop_count"],
                    "features": mode_config["features"],
                    "type": mode_config["type"]
                }
        
        return {
            "crops": crops_info,
            "version": "4.0",
            "total_modes": len(VALID_MODES)
        }
    except Exception as e:
        logger.error(f"Failed to get crops info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint with detailed status."""
    try:
        registry = _load_model_registry()
        
        # Check predictor availability
        predictors_status = {}
        for mode in VALID_MODES:
            try:
                if mode == "real":
                    predictor = RealPredictorV4()
                elif mode == "synthetic":
                    predictor = SyntheticPredictorV4()
                else:
                    predictor = BothPredictorV4()
                
                predictors_status[mode] = {
                    "loaded": True,
                    "crop_count": predictor.crop_count
                }
            except Exception as e:
                predictors_status[mode] = {
                    "loaded": False,
                    "error": str(e)
                }
        
        health_data = {
            "status": "healthy",
            "version": "4.0",
            "timestamp": pd.Timestamp.now().isoformat(),
            "models": predictors_status,
            "memory_usage": {
                "real_predictor_loaded": predictors_status.get("real", {}).get("loaded", False),
                "synthetic_predictor_loaded": predictors_status.get("synthetic", {}).get("loaded", False),
                "both_predictor_loaded": predictors_status.get("both", {}).get("loaded", False),
            },
            "configuration": {
                "log_level": config.get("LOG_LEVEL", "INFO"),
                "structured_logging": config.get("STRUCTURED_LOGGING", True),
                "workers": config.get("WORKERS", 4)
            }
        }
        
        # Log health check
        structured_logger.log_health_check("healthy", health_data)
        
        return health_data
        
    except Exception as e:
        structured_logger.log_error(
            "health_check_error",
            str(e),
            {"status": "unhealthy"}
        )
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Crop Recommendation API V4",
        "version": "4.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "crops": "/crops"
        },
        "modes": list(VALID_MODES)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

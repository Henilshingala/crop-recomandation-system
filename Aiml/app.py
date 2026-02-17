import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Crop Recommendation ML API")

# Load model and data files
model = joblib.load("model_rf.joblib")
label_encoder = joblib.load("label_encoder.joblib")
nutrients_df = pd.read_csv("Nutrient.csv")

class PredictionInput(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float

@app.post("/predict")
def predict(data: PredictionInput):
    """Predict crop and return nutrition data"""
    try:
        # Prepare input
        df = pd.DataFrame([data.dict()])
        
        # Get prediction
        prediction = model.predict(df)[0]
        crop_name = label_encoder.inverse_transform([prediction])[0]
        
        # Get confidence
        probs = model.predict_proba(df)[0]
        confidence = float(max(probs))
        
        # Get nutrition data
        nutrition = None
        nutrient_row = nutrients_df[
            nutrients_df['food_name'].str.lower().str.contains(crop_name.lower(), na=False)
        ]
        
        if not nutrient_row.empty:
            row = nutrient_row.iloc[0]
            nutrition = {
                'protein_g': float(row['protein_g_per_kg']),
                'fat_g': float(row['fat_g_per_kg']),
                'carbs_g': float(row['carbs_g_per_kg']),
                'fiber_g': float(row['fiber_g_per_kg']),
                'iron_mg': float(row['iron_mg_per_kg']),
                'calcium_mg': float(row['calcium_mg_per_kg']),
                'vitamin_a_mcg': float(row['vitamin_a_mcg_per_kg']),
                'vitamin_c_mg': float(row['vitamin_c_mg_per_kg']),
                'energy_kcal': float(row['energy_kcal_per_kg']),
                'water_g': float(row['water_g_per_kg'])
            }
        
        return {
            "crop": crop_name,
            "confidence": confidence,
            "nutrition": nutrition
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health():
    """Health check endpoint"""
    return {
        "status": "ML Model is Live",
        "model_loaded": True,
        "available_crops": list(label_encoder.classes_)
    }

@app.get("/crops")
def get_crops():
    """Get list of all available crops"""
    return {"crops": list(label_encoder.classes_)}

"""
Synthetic predictor V4 - Uses 10 features with proper scaling.
"""

import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from .season_utils import infer_season, get_season_name


def _load_model_registry():
    with open("model_registry.json", "r") as f:
        return json.load(f)


REGISTRY = _load_model_registry()
SYNTHETIC_CONFIG = REGISTRY["models"]["synthetic"]
FEATURES = SYNTHETIC_CONFIG["features"]


class SyntheticPredictorV4:
    def __init__(self):
        self.model_file = SYNTHETIC_CONFIG["model_file"]
        self.encoder_file = SYNTHETIC_CONFIG["encoder_file"]
        self.scaler_file = SYNTHETIC_CONFIG["scaler_file"]
        
        self.model = joblib.load(self.model_file)
        self.label_encoder = joblib.load(self.encoder_file)
        self.scaler = joblib.load(self.scaler_file)
        self.crops = list(self.label_encoder.classes_)
        self.crop_count = len(self.crops)

    def _get_proba(
        self,
        N: float,
        P: float,
        K: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
        season: Optional[int] = None,
        soil_type: int = 1,
        irrigation: int = 0,
    ) -> np.ndarray:
        """Return raw probability array for all crops."""
        season = season if season is not None else infer_season(temperature)
        input_data = {
            "N": N, "P": P, "K": K,
            "temperature": temperature, "humidity": humidity, "ph": ph, "rainfall": rainfall,
            "season": season, "soil_type": soil_type, "irrigation": irrigation,
        }
        
        # Create DataFrame with exact feature order
        X = pd.DataFrame([input_data])[FEATURES]
        
        # Apply scaling
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict_proba(X_scaled)[0]

    def predict(
        self,
        N: float,
        P: float,
        K: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
        top_n: int = 3,
        season: Optional[int] = None,
        soil_type: int = 1,
        irrigation: int = 0,
    ) -> Dict[str, Any]:
        season = season if season is not None else infer_season(temperature)
        proba = self._get_proba(N, P, K, temperature, humidity, ph, rainfall, season, soil_type, irrigation)

        top_indices = np.argsort(proba)[-top_n:][::-1]

        predictions = []
        for idx in top_indices:
            crop_name = self.label_encoder.inverse_transform([idx])[0]
            conf = float(proba[idx])
            predictions.append({"crop": crop_name, "confidence": round(conf * 100, 2)})

        return {
            "predictions": predictions,
            "model_info": {
                "version": "4.0",
                "type": SYNTHETIC_CONFIG["type"],
                "mode": "synthetic",
                "crops": self.crop_count,
                "model_file": self.model_file,
                "encoder_file": self.encoder_file,
                "scaler_file": self.scaler_file,
                "features": FEATURES,
            },
            "environment_info": {
                "season_used": get_season_name(season),
                "inferred": season is None,
                "soil_type": soil_type,
                "irrigation": irrigation,
            },
        }

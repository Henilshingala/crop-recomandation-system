"""
Real-world predictor: stacked_ensemble_v3 (19 crops).
No probability manipulation — raw meta-learner output.
"""

import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from .season_utils import infer_season, get_season_name


def _load_model_registry():
    with open("model_registry.json", "r") as f:
        return json.load(f)


REGISTRY = _load_model_registry()
REAL_CONFIG = REGISTRY["models"]["real"]
FEATURES = REAL_CONFIG["features"]


class RealPredictor:
    def __init__(self):
        self.model_file = REAL_CONFIG["model_file"]
        self.encoder_file = REAL_CONFIG["encoder_file"]
        self.config_file = REAL_CONFIG["config_file"]
        
        self.stacked_model = joblib.load(self.model_file)
        self.label_encoder = joblib.load(self.encoder_file)
        self.config = joblib.load(self.config_file)
        self.FEATURES = self.config.get("feature_names", FEATURES)

        self.FOLD_MODELS = self.stacked_model["fold_models"]
        self.META_LEARNER = self.stacked_model["meta_learner"]
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
        moisture: float = 43.5,
        season: Optional[int] = None,
        soil_type: int = 1,
        irrigation: int = 0,
    ) -> np.ndarray:
        """Return raw probability array for all crops (for blending in BothPredictor)."""
        season = season if season is not None else infer_season(temperature)
        input_data = {
            "n": N, "p": P, "k": K,
            "temperature": temperature, "humidity": humidity, "ph": ph, "rainfall": rainfall,
            "moisture": moisture, "season": season, "soil_type": soil_type, "irrigation": irrigation,
        }
        X = pd.DataFrame([input_data])[self.FEATURES]
        base_preds = []
        for name in ["BalancedRF", "XGBoost", "LightGBM"]:
            model_list = self.FOLD_MODELS[name]
            fold_probs = np.mean([m.predict_proba(X)[0] for m in model_list], axis=0)
            base_preds.append(fold_probs)
        meta_features = np.hstack(base_preds).reshape(1, -1)
        return self.META_LEARNER.predict_proba(meta_features)[0]

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
        moisture: float = 43.5,
        season: Optional[int] = None,
        soil_type: int = 1,
        irrigation: int = 0,
    ) -> Dict[str, Any]:
        proba = self._get_proba(N, P, K, temperature, humidity, ph, rainfall, moisture, season, soil_type, irrigation)

        season_val = season if season is not None else infer_season(temperature)
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
                "type": REAL_CONFIG["type"],
                "mode": "real",
                "crops": self.crop_count,
                "model_file": self.model_file,
                "encoder_file": self.encoder_file,
            },
            "environment_info": {
                "season_used": get_season_name(season_val),
                "inferred": season is None,
            },
        }

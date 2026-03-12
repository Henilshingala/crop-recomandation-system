"""
Both predictor V4 - Hybrid model with confidence-adaptive blending.
"""

import json
import joblib
import numpy as np
from typing import Dict, Any, Optional

from .real_v4 import RealPredictorV4
from .synthetic_v4 import SyntheticPredictorV4
from .season_utils import infer_season, get_season_name


def _load_model_registry():
    with open("model_registry.json", "r") as f:
        return json.load(f)


REGISTRY = _load_model_registry()
BOTH_CONFIG = REGISTRY["models"]["both"]


class BothPredictorV4:
    def __init__(self):
        self.config_file = BOTH_CONFIG["config_file"]
        self.hybrid_config = joblib.load(self.config_file)
        
        # Load both predictors
        self.real_predictor = RealPredictorV4()
        self.synthetic_predictor = SyntheticPredictorV4()
        
        # Get unified crop list
        real_crops = set(self.real_predictor.crops)
        synthetic_crops = set(self.synthetic_predictor.crops)
        self.unified_crops = sorted(list(real_crops.union(synthetic_crops)))
        self.crop_count = len(self.unified_crops)
        
        # Create crop to index mapping
        self.crop_to_index = {crop: idx for idx, crop in enumerate(self.unified_crops)}

    def _blend_probabilities(self, real_proba, synthetic_proba, confidence_threshold=0.3):
        """Blend probabilities using confidence-adaptive approach."""
        # Get real and synthetic predictions with confidence
        real_top_confidence = np.max(real_proba)
        synthetic_top_confidence = np.max(synthetic_proba)
        
        # Adaptive blending based on confidence
        if real_top_confidence > confidence_threshold and synthetic_top_confidence > confidence_threshold:
            # Both confident - use configured weights
            real_weight = self.hybrid_config["blend_weights"]["real"]
            synthetic_weight = self.hybrid_config["blend_weights"]["synthetic"]
        elif real_top_confidence > confidence_threshold:
            # Real more confident
            real_weight = 0.8
            synthetic_weight = 0.2
        elif synthetic_top_confidence > confidence_threshold:
            # Synthetic more confident
            real_weight = 0.2
            synthetic_weight = 0.8
        else:
            # Both uncertain - equal weights
            real_weight = 0.5
            synthetic_weight = 0.5
        
        # Create unified probability array
        unified_proba = np.zeros(len(self.unified_crops))
        
        # Add real probabilities
        for i, crop in enumerate(self.real_predictor.crops):
            if crop in self.crop_to_index:
                unified_proba[self.crop_to_index[crop]] += real_proba[i] * real_weight
        
        # Add synthetic probabilities
        for i, crop in enumerate(self.synthetic_predictor.crops):
            if crop in self.crop_to_index:
                unified_proba[self.crop_to_index[crop]] += synthetic_proba[i] * synthetic_weight
        
        return unified_proba

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
        moisture: float = 50.0,
    ) -> Dict[str, Any]:
        season = season if season is not None else infer_season(temperature)
        
        # Get probabilities from both models
        real_proba = self.real_predictor._get_proba(
            N, P, K, temperature, humidity, ph, rainfall, season, soil_type, irrigation, moisture
        )
        synthetic_proba = self.synthetic_predictor._get_proba(
            N, P, K, temperature, humidity, ph, rainfall, season, soil_type, irrigation
        )
        
        # Blend probabilities
        unified_proba = self._blend_probabilities(real_proba, synthetic_proba)
        
        # Get top predictions
        top_indices = np.argsort(unified_proba)[-top_n:][::-1]
        
        predictions = []
        for idx in top_indices:
            crop_name = self.unified_crops[idx]
            conf = float(unified_proba[idx])
            predictions.append({"crop": crop_name, "confidence": round(conf * 100, 2)})
        
        return {
            "predictions": predictions,
            "model_info": {
                "version": "4.0",
                "type": BOTH_CONFIG["type"],
                "mode": "both",
                "crops": self.crop_count,
                "real_crops": len(self.real_predictor.crops),
                "synthetic_crops": len(self.synthetic_predictor.crops),
                "common_crops": len(self.hybrid_config["common_crops"]),
                "config_file": self.config_file,
                "blend_weights": self.hybrid_config["blend_weights"],
            },
            "environment_info": {
                "season_used": get_season_name(season),
                "inferred": season is None,
                "soil_type": soil_type,
                "irrigation": irrigation,
                "moisture": moisture,
            },
        }

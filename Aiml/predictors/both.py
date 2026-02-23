"""
Both predictor: combines real (V3) + synthetic (model_rf) with simple blending.
No probability manipulation — raw blend of model outputs.
"""

import json
import numpy as np
from typing import Dict, Any, Optional

from .real import RealPredictor
from .synthetic import SyntheticPredictor
from .season_utils import infer_season, get_season_name


def _load_model_registry():
    with open("model_registry.json", "r") as f:
        return json.load(f)


REGISTRY = _load_model_registry()
BOTH_CONFIG = REGISTRY["models"]["both"]
CROP_MAPPINGS = REGISTRY["crop_mappings"]

CROP_NAME_MAP_REAL_TO_SYNTH = CROP_MAPPINGS["real_to_synthetic"]
CROP_NAME_MAP_SYNTH_TO_REAL = CROP_MAPPINGS["synthetic_to_real"]

W_REAL = BOTH_CONFIG["blend_weights"]["real"]
W_SYNTH = BOTH_CONFIG["blend_weights"]["synthetic"]


class BothPredictor:
    def __init__(self):
        self.real_pred = RealPredictor()
        self.synth_pred = SyntheticPredictor()

        real_mapped = {CROP_NAME_MAP_REAL_TO_SYNTH.get(c, c) for c in self.real_pred.crops}
        self.synth_only = {
            c for c in self.synth_pred.crops
            if c not in real_mapped
            and CROP_NAME_MAP_SYNTH_TO_REAL.get(c, c) not in set(self.real_pred.crops)
        }

        unified = list(self.synth_pred.crops)
        for c in self.real_pred.crops:
            m = CROP_NAME_MAP_REAL_TO_SYNTH.get(c, c)
            if m not in unified:
                unified.append(m)
        self.unified_crops = sorted(unified)

        self._ri = {c: i for i, c in enumerate(self.real_pred.crops)}
        self._si = {c: i for i, c in enumerate(self.synth_pred.crops)}

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
        pr = self.real_pred._get_proba(
            N, P, K, temperature, humidity, ph, rainfall,
            moisture=moisture,
            season=season,
            soil_type=soil_type,
            irrigation=irrigation,
        )
        ps = self.synth_pred._get_proba(
            N, P, K, temperature, humidity, ph, rainfall,
            season=season,
            soil_type=soil_type,
            irrigation=irrigation,
        )

        blended = np.zeros(len(self.unified_crops))
        for ui, crop in enumerate(self.unified_crops):
            rn = CROP_NAME_MAP_SYNTH_TO_REAL.get(crop, crop)
            p_r = float(pr[self._ri[rn]]) if rn in self._ri else 0.0
            p_s = float(ps[self._si[crop]]) if crop in self._si else 0.0

            if crop in self.synth_only:
                blended[ui] = W_SYNTH * p_s
            elif rn in self._ri and crop in self._si:
                blended[ui] = W_REAL * p_r + W_SYNTH * p_s
            elif rn in self._ri:
                blended[ui] = W_REAL * p_r
            else:
                blended[ui] = W_SYNTH * p_s

        s = blended.sum()
        if s > 0:
            blended = blended / s

        top_indices = np.argsort(blended)[-top_n:][::-1]

        predictions = []
        for idx in top_indices:
            crop_name = self.unified_crops[idx]
            conf = float(blended[idx])
            predictions.append({"crop": crop_name, "confidence": round(conf * 100, 2)})

        from .season_utils import infer_season
        season_val = season if season is not None else infer_season(temperature)

        season_used = get_season_name(season_val)

        return {
            "predictions": predictions,
            "model_info": {
                "version": "4.0",
                "type": BOTH_CONFIG["type"],
                "mode": "both",
                "crops": len(self.unified_crops),
                "blend_weights": BOTH_CONFIG["blend_weights"],
            },
            "environment_info": {
                "season_used": season_used,
                "inferred": season is None,
            },
        }

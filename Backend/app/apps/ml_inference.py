"""
Crop Recommendation System — ML Inference (Gateway Mode)
=========================================================
Routes prediction requests through the HuggingFace Space (v3 stacked
ensemble) and/or the local synthetic model.

Modes
─────
  "original"  → HuggingFace v3 (19 real-world crops)
  "synthetic" → Local model_rf.joblib (51 synthetic crops)
  "both"      → HF + synthetic, merged 60/40 by confidence

If HF is unreachable the caller always gets the synthetic fallback.
"""

import logging
import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
from django.conf import settings

from .services.hf_service import call_hf_model

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════
# Constants
# ═════════════════════════════════════════════════════════════════════════

W_ORIGINAL = 0.60          # weight for HF "original" in "both" mode
W_SYNTHETIC = 0.40         # weight for local synthetic in "both" mode

SYNTH_FEATURE_ORDER = [
    "N", "P", "K", "temperature", "humidity",
    "ph", "rainfall", "season", "soil_type", "irrigation",
]


# ═════════════════════════════════════════════════════════════════════════
# Resolve AIML directory  (only needed for local synthetic model)
# ═════════════════════════════════════════════════════════════════════════

def _get_aiml_dir() -> Path:
    env = os.environ.get("AI_ML_DIR")
    if env:
        return Path(env)
    return settings.BASE_DIR.parent.parent / "Aiml"


# ═════════════════════════════════════════════════════════════════════════
# Lazy-loaded synthetic model
# ═════════════════════════════════════════════════════════════════════════

_synth_model = None
_synth_encoder = None


def _load_synthetic():
    """Load model_rf.joblib + label_encoder.joblib once."""
    global _synth_model, _synth_encoder
    if _synth_model is not None:
        return
    aiml = _get_aiml_dir()
    _synth_model = joblib.load(aiml / "model_rf.joblib")
    _synth_encoder = joblib.load(aiml / "label_encoder.joblib")
    logger.info(
        "Synthetic model loaded — %d crops", len(_synth_encoder.classes_)
    )


# ═════════════════════════════════════════════════════════════════════════
# Risk helper
# ═════════════════════════════════════════════════════════════════════════

def _risk_level(confidence: float) -> str:
    """Map confidence % → risk label."""
    if confidence >= 80:
        return "low"
    if confidence >= 50:
        return "medium"
    return "high"


# ═════════════════════════════════════════════════════════════════════════
# Internal prediction strategies
# ═════════════════════════════════════════════════════════════════════════

def _predict_original(payload: dict) -> Optional[Dict]:
    """
    Call HuggingFace Space (v3 stacked ensemble).

    Returns normalised dict or None on failure.
    """
    hf_resp = call_hf_model(payload)
    if hf_resp is None:
        return None

    # HF response: { top_3: [{crop, confidence}, ...], model_info: {...} }
    top3_raw = hf_resp.get("top_3") or hf_resp.get("predictions") or []
    top3 = [
        {
            "crop": r.get("crop", "unknown"),
            "confidence": round(float(r.get("confidence", 0)), 2),
            "risk_level": _risk_level(float(r.get("confidence", 0))),
        }
        for r in top3_raw[:3]
    ]

    model_info = hf_resp.get("model_info", {})

    return {
        "mode": "original",
        "top_3": top3,
        "model_info": {
            "type": model_info.get("type", "stacked-ensemble-v3"),
            "coverage": model_info.get("coverage", 19),
            "version": model_info.get("version", "3.0"),
        },
    }


def _predict_synthetic(payload: dict) -> Dict:
    """
    Run the local model_rf.joblib (synthetic 51-crop RF).

    Always succeeds (raises on corrupt model file).
    """
    _load_synthetic()

    # Infer season from temperature
    temp = float(payload.get("temperature", 25))
    if temp >= 28:
        season = 0   # Kharif
    elif temp <= 22:
        season = 1   # Rabi
    else:
        season = 2   # Zaid

    row = [
        float(payload.get("N", 0)),
        float(payload.get("P", 0)),
        float(payload.get("K", 0)),
        temp,
        float(payload.get("humidity", 50)),
        float(payload.get("ph", 6.5)),
        float(payload.get("rainfall", 100)),
        season,
        int(payload.get("soil_type", 1)),
        int(payload.get("irrigation", 0)),
    ]
    X = np.array([row])
    proba = _synth_model.predict_proba(X)[0]
    top_idx = np.argsort(proba)[::-1][:3]

    top3 = [
        {
            "crop": _synth_encoder.classes_[i],
            "confidence": round(float(proba[i]) * 100, 2),
            "risk_level": _risk_level(float(proba[i]) * 100),
        }
        for i in top_idx
    ]

    return {
        "mode": "synthetic",
        "top_3": top3,
        "model_info": {
            "type": "random-forest-synthetic",
            "coverage": len(_synth_encoder.classes_),
            "version": "1.0",
        },
    }


def _predict_both(payload: dict) -> Dict:
    """
    Merge HF (original) + local (synthetic) at 60/40 confidence blend.

    If HF is unreachable, falls back to pure synthetic.
    """
    orig = _predict_original(payload)
    synth = _predict_synthetic(payload)

    if orig is None:
        logger.warning("HF unavailable — 'both' mode falling back to synthetic only")
        synth["mode"] = "both"
        synth["model_info"]["fallback"] = True
        return synth

    # Merge by crop name, summing weighted confidences
    merged: Dict[str, float] = {}
    for rec in orig["top_3"]:
        name = rec["crop"].lower()
        merged[name] = merged.get(name, 0) + W_ORIGINAL * rec["confidence"]
    for rec in synth["top_3"]:
        name = rec["crop"].lower()
        merged[name] = merged.get(name, 0) + W_SYNTHETIC * rec["confidence"]

    ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:3]
    top3 = [
        {
            "crop": name,
            "confidence": round(conf, 2),
            "risk_level": _risk_level(conf),
        }
        for name, conf in ranked
    ]

    return {
        "mode": "both",
        "top_3": top3,
        "model_info": {
            "type": "blended-original-synthetic",
            "coverage": orig["model_info"]["coverage"],
            "version": "3.0+1.0",
        },
    }


# ═════════════════════════════════════════════════════════════════════════
# Public API  (called by views.py)
# ═════════════════════════════════════════════════════════════════════════

def predict_top_crops(
    n: float,
    p: float,
    k: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    top_n: int = 3,
    soil_type: int = 1,
    irrigation: int = 0,
    moisture: float = 43.5,
    mode: str = "original",
) -> dict:
    """
    Convenience wrapper used by views.py.

    Parameters
    ----------
    mode : "original" | "synthetic" | "both"
    """
    payload = {
        "N": n, "P": p, "K": k,
        "temperature": temperature,
        "humidity": humidity,
        "ph": ph,
        "rainfall": rainfall,
        "moisture": moisture,
        "soil_type": soil_type,
        "irrigation": irrigation,
        "top_n": top_n,
    }

    if mode == "synthetic":
        return _predict_synthetic(payload)

    if mode == "both":
        return _predict_both(payload)

    # Default: "original" — try HF, fallback to synthetic
    result = _predict_original(payload)
    if result is not None:
        return result

    logger.warning("HF unreachable — falling back to synthetic model")
    fallback = _predict_synthetic(payload)
    fallback["mode"] = "original"
    fallback["model_info"]["fallback"] = True
    return fallback


def get_available_crops(mode: str = "original") -> List[str]:
    """Return crop list for the requested mode."""
    if mode == "synthetic":
        _load_synthetic()
        return sorted(_synth_encoder.classes_.tolist())
    # For original/both, return the 19 real-world crops as known constants
    return sorted([
        "chickpea", "cotton", "finger_millet", "groundnut", "jowar",
        "lentil", "maize", "moong", "pearl_millet", "pigeonpea",
        "rice", "safflower", "sesamum", "sorghum", "soybean",
        "sugarcane", "sunflower", "urad", "wheat",
    ])


# ═════════════════════════════════════════════════════════════════════════
# Compatibility shim  (get_predictor used by views.health_check)
# ═════════════════════════════════════════════════════════════════════════

class _PredictorShim:
    """Minimal shim so health_check can call get_predictor().get_available_crops()."""

    def get_available_crops(self, mode: str = "original") -> List[str]:
        return get_available_crops(mode)


def get_predictor() -> _PredictorShim:
    return _PredictorShim()

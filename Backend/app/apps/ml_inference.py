"""
Crop Recommendation System — ML Inference (Gateway-Only Mode)
==============================================================
All prediction requests are routed through the HuggingFace Space
(V6 multi-mode serving).  Zero ML libraries are loaded locally to
stay within Render's 512 MB free-tier RAM limit.

Modes (V6)
──────────
  "soil"     → V6 stacked ensemble (51 crops, Crop_recommendation_v2.csv)
  "extended" → Calibrated RF (51 crops, legacy fallback)
  "both"     → Confidence-adaptive hybrid blend

Deprecated aliases: "original" → "soil", "synthetic" → "extended"
"""

import logging
from typing import Dict, List, Optional

from .services.hf_service import call_hf_model

logger = logging.getLogger(__name__)


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
# HuggingFace prediction (V5 multi-mode)
# ═════════════════════════════════════════════════════════════════════════

def _predict_via_hf(payload: dict, mode: str = "soil") -> Optional[Dict]:
    """
    Call HuggingFace Space V6 and normalise the response.

    V6 response format:
    {
        "mode": "soil",
        "predictions": [...],
        "top_3": [...],
        "model_info": {...},
        "confidence_info": {...},
        "environment_info": {...},
        "warning": "..."  (optional)
    }

    Returns normalised dict or None on failure.
    """
    hf_resp = call_hf_model(payload)
    if hf_resp is None:
        return None

    # V5: top_3 already has crop, confidence, risk_level, nutrition
    top3_raw = hf_resp.get("top_3") or hf_resp.get("predictions") or []
    top3 = [
        {
            "crop": r.get("crop", "unknown"),
            "confidence": round(float(r.get("confidence", 0)), 2),
            "risk_level": r.get("risk_level") or _risk_level(float(r.get("confidence", 0))),
        }
        for r in top3_raw[:3]
    ]

    model_info = hf_resp.get("model_info", {})
    confidence_info = hf_resp.get("confidence_info", {})

    result = {
        "mode": hf_resp.get("mode", mode),
        "top_3": top3,
        "model_info": {
            "type": model_info.get("type", "unknown"),
            "coverage": model_info.get("crops", model_info.get("coverage", 0)),
            "version": model_info.get("version", "6.0"),
            "checksum": model_info.get("checksum"),
        },
        "confidence_info": {
            "top_probability": confidence_info.get("top_probability", 0),
            "entropy": confidence_info.get("entropy", 0),
            "low_confidence": confidence_info.get("low_confidence", False),
        },
    }

    # Pass through any warnings from V5
    warning = hf_resp.get("warning")
    if warning:
        result["warning"] = warning

    return result


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
    mode: str = "soil",
) -> dict:
    """
    Convenience wrapper used by views.py.

    Each mode routes to HuggingFace Space where V6 dispatches to
    the correct model.  Mode is sent as part of the payload.
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
        "mode": mode,
        "top_n": top_n,
    }

    result = _predict_via_hf(payload, mode=mode)
    if result is not None:
        return result

    # HF is down — return a minimal error payload so the view can 503
    raise ConnectionError("HuggingFace Space is unreachable after retries")


# ═════════════════════════════════════════════════════════════════════════
# Crop lists (static — no model loading required)
# ═════════════════════════════════════════════════════════════════════════

# V6: all modes share the same 51-crop set from Crop_recommendation_v2.csv
_V6_CROPS = sorted([
    "apple", "bajra", "banana", "barley", "ber", "blackgram",
    "brinjal", "carrot", "castor", "chickpea", "citrus", "coconut",
    "coffee", "cole_crop", "cotton", "cucumber", "custard_apple",
    "date_palm", "gourd", "grapes", "green_chilli", "groundnut",
    "guava", "jowar", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "mustard", "okra",
    "onion", "papaya", "pigeonpeas", "pomegranate", "potato", "radish",
    "ragi", "rice", "sapota", "sesame", "soybean", "spinach",
    "sugarcane", "tobacco", "tomato", "watermelon", "wheat",
])


def get_available_crops(mode: str = "soil") -> List[str]:
    """Return crop list for the requested mode (all 51 in V6)."""
    return list(_V6_CROPS)


# ═════════════════════════════════════════════════════════════════════════
# Compatibility shim  (get_predictor used by views.health_check)
# ═════════════════════════════════════════════════════════════════════════

class _PredictorShim:
    """Minimal shim so health_check can call get_predictor().get_available_crops()."""

    def get_available_crops(self, mode: str = "soil") -> List[str]:
        return get_available_crops(mode)


def get_predictor() -> _PredictorShim:
    return _PredictorShim()

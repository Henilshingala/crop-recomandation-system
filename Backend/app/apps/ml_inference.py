"""
Crop Recommendation System — ML Inference (Gateway-Only Mode)
==============================================================
All prediction requests are routed through the HuggingFace Space
(v3 stacked ensemble).  Zero ML libraries are loaded locally to
stay within Render's 512 MB free-tier RAM limit.

Modes
─────
  "original"  → HuggingFace v3 (19 real-world crops)
  "synthetic" → Also routed to HF (same model)
  "both"      → Also routed to HF (same model)
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
# HuggingFace prediction (all modes)
# ═════════════════════════════════════════════════════════════════════════

def _predict_via_hf(payload: dict, mode: str = "original") -> Optional[Dict]:
    """
    Call HuggingFace Space (v3 stacked ensemble) and normalise the response.

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
        "mode": mode,
        "top_3": top3,
        "model_info": {
            "type": model_info.get("type", "stacked-ensemble-v3"),
            "coverage": model_info.get("coverage", 19),
            "version": model_info.get("version", "3.0"),
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

    All modes route to HuggingFace Space.  The *mode* tag is preserved
    in the response so the frontend knows what was requested.
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

    result = _predict_via_hf(payload, mode=mode)
    if result is not None:
        return result

    # HF is down — return a minimal error payload so the view can 503
    raise ConnectionError("HuggingFace Space is unreachable after retries")


# ═════════════════════════════════════════════════════════════════════════
# Crop lists (static — no model loading required)
# ═════════════════════════════════════════════════════════════════════════

_ORIGINAL_CROPS = sorted([
    "barley", "castor", "chickpea", "cotton", "finger_millet",
    "groundnut", "linseed", "maize", "mustard", "pearl_millet",
    "pigeonpea", "rice", "safflower", "sesamum", "sorghum",
    "soybean", "sugarcane", "sunflower", "wheat",
])

_SYNTHETIC_CROPS = sorted([
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


def get_available_crops(mode: str = "original") -> List[str]:
    """Return crop list for the requested mode."""
    if mode == "synthetic":
        return list(_SYNTHETIC_CROPS)
    if mode == "both":
        return sorted(set(_ORIGINAL_CROPS) | set(_SYNTHETIC_CROPS))
    return list(_ORIGINAL_CROPS)


# ═════════════════════════════════════════════════════════════════════════
# Compatibility shim  (get_predictor used by views.health_check)
# ═════════════════════════════════════════════════════════════════════════

class _PredictorShim:
    """Minimal shim so health_check can call get_predictor().get_available_crops()."""

    def get_available_crops(self, mode: str = "original") -> List[str]:
        return get_available_crops(mode)


def get_predictor() -> _PredictorShim:
    return _PredictorShim()

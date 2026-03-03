"""
Crop Recommendation System — ML Inference (Gateway-Only Mode)
==============================================================
All prediction requests are routed through the HuggingFace Space
(V7 unified advisory engine).  Zero ML libraries are loaded locally
to stay within Render's 512 MB free-tier RAM limit.

V7 Architecture
───────────────
  POST /recommend  → Unified endpoint (runs all 3 models internally,
                     returns aggregated Top-3 with no model exposure)
  POST /predict    → Legacy endpoint (kept for backward compat)
"""

import logging
from typing import Dict, List, Optional

from .services.hf_service import call_hf_model, call_hf_recommend

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


def _tier_to_risk(tier: str) -> str:
    """Map advisory_tier to legacy risk_level."""
    if "Strongly" in tier:
        return "low"
    if "Monitoring" in tier:
        return "low"
    if "Conditional" in tier:
        return "medium"
    return "high"


# ═════════════════════════════════════════════════════════════════════════
# V7 Unified recommendation (calls /recommend)
# ═════════════════════════════════════════════════════════════════════════

def _recommend_via_hf(payload: dict) -> Optional[Dict]:
    """
    Call HuggingFace Space /recommend and normalise the response
    to the format expected by views.py.

    V7 /recommend response:
    {
        "top_recommendations": [
            {
                "crop": "...", "confidence": ..., "advisory_tier": "...",
                "stress_index": ..., "explanation": "...",
                "model_consensus": "strong/moderate/weak",
                "nutrition": {...}
            }
        ],
        "stress_index": ...,
        "environment_info": {...},
        "warning": "..."
    }
    """
    hf_resp = call_hf_recommend(payload)
    if hf_resp is None:
        return None

    top_recs = hf_resp.get("top_recommendations", [])
    top3 = []
    for r in top_recs[:3]:
        top3.append({
            "crop": r.get("crop", "unknown"),
            "confidence": round(float(r.get("confidence", 0)), 2),
            "advisory_tier": r.get("advisory_tier", "Not Recommended"),
            "risk_level": _tier_to_risk(r.get("advisory_tier", "")),
            "stress_index": r.get("stress_index", 0),
            "explanation": r.get("explanation", ""),
            "model_consensus": r.get("model_consensus", "weak"),
            "nutrition": r.get("nutrition"),
        })

    result = {
        "top_3": top3,
        "model_info": {
            "type": "unified-advisory-v8.1",
            "coverage": 51,
            "version": "8.1",
        },
        "stress_index": hf_resp.get("stress_index", 0),
        "stress_per_feature": hf_resp.get("stress_per_feature", {}),
        "environment_info": hf_resp.get("environment_info", {}),
        "fallback_mode": hf_resp.get("fallback_mode", False),
        "all_not_recommended": hf_resp.get("all_not_recommended", False),
        "disclaimer": hf_resp.get("disclaimer", ""),
    }

    warning = hf_resp.get("warning")
    if warning:
        result["warning"] = warning

    return result


# ═════════════════════════════════════════════════════════════════════════
# Legacy HF prediction (V6/V7 /predict — kept for compat)
# ═════════════════════════════════════════════════════════════════════════

def _predict_via_hf(payload: dict, mode: str = "soil") -> Optional[Dict]:
    """
    Call HuggingFace Space V7 /predict and normalise the response.
    """
    hf_resp = call_hf_model(payload)
    if hf_resp is None:
        return None

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

    result = {
        "mode": hf_resp.get("mode", mode),
        "top_3": top3,
        "model_info": {
            "type": model_info.get("type", "unknown"),
            "coverage": model_info.get("crops", model_info.get("coverage", 0)),
            "version": model_info.get("version", "7.0"),
            "checksum": model_info.get("checksum"),
        },
    }

    warning = hf_resp.get("warning")
    if warning:
        result["warning"] = warning

    return result


# ═════════════════════════════════════════════════════════════════════════
# Public API  (called by views.py)
# ═════════════════════════════════════════════════════════════════════════

def recommend_crops(
    n: float,
    p: float,
    k: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    soil_type: int = 1,
    irrigation: int = 0,
    moisture: float = 43.5,
) -> dict:
    """
    V7 unified recommendation — calls /recommend (no mode).
    All 3 models run internally; returns aggregated top-3.
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
    }

    result = _recommend_via_hf(payload)
    if result is not None:
        return result

    raise ConnectionError("HuggingFace Space is unreachable after retries")


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
    Legacy wrapper — kept for backward compat.
    Calls /predict with mode parameter.
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

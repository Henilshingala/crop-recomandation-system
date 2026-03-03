"""
Crop Recommendation ML API — V7 Farmer Advisory Engine
=======================================================
Soil-driven stacked ensemble + agronomic feasibility constraints.

Architecture upgrades over V6:
  1. Agronomic hard constraint layer (per-crop pH/temp/rain/humidity limits)
  2. OOD confidence dampening (30% penalty per OOD feature, 65% cap)
  3. Stress score calculation (normalized distance from safe midpoints)
  4. Calibrated confidence = 0.6*model + 0.2*agreement + 0.2*inv_entropy
  5. Model selection rebalancing (blend on disagreement)
  6. Advisory risk tiers (Strongly Recommended -> Not Recommended)
  7. Structured agronomic explanation per crop
  8. Hard confidence cap at 92%

Models:
  "soil"      -> V6 stacked ensemble (51 crops)
  "extended"  -> Calibrated RF (51 crops)
  "both"      -> Confidence-adaptive blend
"""

import hashlib
import json
import math
import time
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple
import logging
import os

# ===================================================================
# LOGGING
# ===================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_api_v7")

app = FastAPI(title="Crop Recommendation ML API", version="7.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===================================================================
# FEATURE RANGES
# ===================================================================

_RANGES_PATH = os.path.join(BASE_DIR, "feature_ranges.json")
with open(_RANGES_PATH, encoding="utf-8") as _f:
    FEATURE_RANGES: dict = json.load(_f)

_ACC = FEATURE_RANGES["acceptance"]
_V6_FEAT = FEATURE_RANGES["v6_soil_model"]["features"]

TRAINING_RANGES = {
    "soil": {k: {"min": v["min"], "max": v["max"]} for k, v in _V6_FEAT.items()},
    "extended": {k: {"min": v["min"], "max": v["max"]} for k, v in _V6_FEAT.items()},
}
TRAINING_RANGES["both"] = TRAINING_RANGES["soil"]

logger.info("Loaded feature_ranges.json")

# ===================================================================
# CONSTANTS — V7 ADVISORY ENGINE
# ===================================================================

HARD_CONFIDENCE_CAP = 0.92
OOD_DAMPEN_FACTOR = 0.30
OOD_CAP_THRESHOLD = 0.50
OOD_MAX_CONFIDENCE = 0.65
STRESS_HIGH_THRESHOLD = 0.60
STRESS_REDUCTION_MIN = 0.20
STRESS_REDUCTION_MAX = 0.40
AGRONOMIC_PENALTY_MILD = 0.05
AGRONOMIC_PENALTY_EXTREME = 0.001
ENTROPY_WARNING_THRESHOLD = 2.0
RELIABILITY_WEIGHT_CONFIDENCE = 0.7
RELIABILITY_WEIGHT_ENTROPY = 0.3
AGREEMENT_BONUS = 5.0

MODE_ALIASES = {
    "soil": "soil", "extended": "extended", "both": "both",
    "original": "soil", "synthetic": "extended",
}
VALID_MODES = set(MODE_ALIASES.keys())
CANONICAL_MODES = {"soil", "extended", "both"}

# ===================================================================
# STEP 1 — AGRONOMIC HARD CONSTRAINT DICTIONARY
# Per-crop biologically feasible ranges (ICAR / FAO literature)
# ===================================================================

CROP_AGRO_CONSTRAINTS = {
    "apple":          {"ph_range": [5.5, 7.0], "temp_range": [10, 28], "rainfall_range": [500, 1500], "humidity_range": [40, 80]},
    "bajra":          {"ph_range": [6.0, 8.0], "temp_range": [25, 42], "rainfall_range": [200, 700],  "humidity_range": [20, 65]},
    "banana":         {"ph_range": [5.5, 7.5], "temp_range": [20, 40], "rainfall_range": [1000, 3000],"humidity_range": [60, 95]},
    "barley":         {"ph_range": [6.0, 8.5], "temp_range": [5, 25],  "rainfall_range": [300, 1000], "humidity_range": [30, 70]},
    "ber":            {"ph_range": [6.5, 9.0], "temp_range": [30, 48], "rainfall_range": [100, 600],  "humidity_range": [10, 50]},
    "blackgram":      {"ph_range": [5.5, 7.5], "temp_range": [25, 38], "rainfall_range": [400, 900],  "humidity_range": [50, 85]},
    "brinjal":        {"ph_range": [5.5, 7.0], "temp_range": [20, 35], "rainfall_range": [300, 1000], "humidity_range": [50, 80]},
    "carrot":         {"ph_range": [6.0, 7.0], "temp_range": [10, 25], "rainfall_range": [300, 800],  "humidity_range": [50, 80]},
    "castor":         {"ph_range": [5.0, 8.0], "temp_range": [20, 38], "rainfall_range": [300, 800],  "humidity_range": [30, 70]},
    "chickpea":       {"ph_range": [6.0, 8.0], "temp_range": [15, 30], "rainfall_range": [300, 700],  "humidity_range": [30, 60]},
    "citrus":         {"ph_range": [5.5, 7.5], "temp_range": [15, 35], "rainfall_range": [500, 1500], "humidity_range": [40, 80]},
    "coconut":        {"ph_range": [5.0, 8.0], "temp_range": [22, 38], "rainfall_range": [1000, 3200],"humidity_range": [60, 95]},
    "coffee":         {"ph_range": [5.0, 6.5], "temp_range": [15, 28], "rainfall_range": [1000, 2500],"humidity_range": [60, 90]},
    "cole_crop":      {"ph_range": [6.0, 7.5], "temp_range": [5, 22],  "rainfall_range": [400, 1500], "humidity_range": [50, 85]},
    "cotton":         {"ph_range": [5.5, 8.5], "temp_range": [25, 40], "rainfall_range": [500, 1200], "humidity_range": [40, 75]},
    "cucumber":       {"ph_range": [5.5, 7.5], "temp_range": [18, 35], "rainfall_range": [300, 1000], "humidity_range": [50, 85]},
    "custard_apple":  {"ph_range": [5.5, 8.0], "temp_range": [25, 42], "rainfall_range": [200, 800],  "humidity_range": [30, 70]},
    "date_palm":      {"ph_range": [7.0, 9.0], "temp_range": [30, 48], "rainfall_range": [50, 400],   "humidity_range": [10, 50]},
    "gourd":          {"ph_range": [5.5, 7.5], "temp_range": [20, 38], "rainfall_range": [300, 1000], "humidity_range": [50, 85]},
    "grapes":         {"ph_range": [5.5, 7.5], "temp_range": [15, 35], "rainfall_range": [400, 1000], "humidity_range": [30, 70]},
    "green_chilli":   {"ph_range": [5.5, 7.5], "temp_range": [20, 35], "rainfall_range": [400, 1000], "humidity_range": [50, 80]},
    "groundnut":      {"ph_range": [5.5, 7.5], "temp_range": [22, 38], "rainfall_range": [400, 1000], "humidity_range": [40, 75]},
    "guava":          {"ph_range": [5.0, 7.5], "temp_range": [18, 38], "rainfall_range": [400, 1500], "humidity_range": [40, 80]},
    "jowar":          {"ph_range": [5.5, 8.5], "temp_range": [25, 42], "rainfall_range": [300, 800],  "humidity_range": [30, 70]},
    "jute":           {"ph_range": [5.0, 7.5], "temp_range": [25, 38], "rainfall_range": [1000, 2500],"humidity_range": [60, 95]},
    "kidneybeans":    {"ph_range": [5.5, 7.0], "temp_range": [15, 28], "rainfall_range": [300, 800],  "humidity_range": [40, 70]},
    "lentil":         {"ph_range": [6.0, 8.0], "temp_range": [10, 28], "rainfall_range": [200, 600],  "humidity_range": [30, 65]},
    "maize":          {"ph_range": [5.5, 7.5], "temp_range": [18, 35], "rainfall_range": [400, 1200], "humidity_range": [40, 80]},
    "mango":          {"ph_range": [5.5, 7.5], "temp_range": [24, 42], "rainfall_range": [500, 2500], "humidity_range": [40, 80]},
    "mothbeans":      {"ph_range": [6.5, 8.5], "temp_range": [25, 42], "rainfall_range": [200, 600],  "humidity_range": [20, 60]},
    "mungbean":       {"ph_range": [5.5, 7.5], "temp_range": [25, 38], "rainfall_range": [400, 800],  "humidity_range": [50, 80]},
    "muskmelon":      {"ph_range": [6.0, 7.5], "temp_range": [22, 38], "rainfall_range": [200, 600],  "humidity_range": [40, 70]},
    "mustard":        {"ph_range": [5.5, 8.0], "temp_range": [10, 28], "rainfall_range": [200, 600],  "humidity_range": [30, 65]},
    "okra":           {"ph_range": [6.0, 7.5], "temp_range": [22, 38], "rainfall_range": [400, 1000], "humidity_range": [50, 80]},
    "onion":          {"ph_range": [6.0, 7.5], "temp_range": [10, 30], "rainfall_range": [300, 800],  "humidity_range": [40, 75]},
    "papaya":         {"ph_range": [5.5, 7.5], "temp_range": [22, 38], "rainfall_range": [600, 2000], "humidity_range": [50, 85]},
    "pigeonpeas":     {"ph_range": [5.0, 8.0], "temp_range": [20, 38], "rainfall_range": [600, 1500], "humidity_range": [40, 80]},
    "pomegranate":    {"ph_range": [5.5, 8.0], "temp_range": [22, 40], "rainfall_range": [200, 800],  "humidity_range": [30, 65]},
    "potato":         {"ph_range": [5.0, 7.0], "temp_range": [10, 25], "rainfall_range": [400, 1000], "humidity_range": [50, 85]},
    "radish":         {"ph_range": [5.5, 7.0], "temp_range": [8, 22],  "rainfall_range": [200, 800],  "humidity_range": [50, 80]},
    "ragi":           {"ph_range": [5.0, 7.5], "temp_range": [20, 35], "rainfall_range": [500, 1200], "humidity_range": [50, 80]},
    "rice":           {"ph_range": [5.0, 7.5], "temp_range": [20, 38], "rainfall_range": [800, 3000], "humidity_range": [60, 95]},
    "sapota":         {"ph_range": [6.0, 8.0], "temp_range": [20, 38], "rainfall_range": [600, 2000], "humidity_range": [50, 85]},
    "sesame":         {"ph_range": [5.5, 8.0], "temp_range": [25, 40], "rainfall_range": [200, 700],  "humidity_range": [30, 65]},
    "soybean":        {"ph_range": [5.5, 7.5], "temp_range": [20, 35], "rainfall_range": [500, 1200], "humidity_range": [50, 80]},
    "spinach":        {"ph_range": [6.0, 7.5], "temp_range": [8, 25],  "rainfall_range": [300, 800],  "humidity_range": [50, 80]},
    "sugarcane":      {"ph_range": [5.0, 8.5], "temp_range": [22, 40], "rainfall_range": [800, 2500], "humidity_range": [55, 90]},
    "tobacco":        {"ph_range": [5.0, 7.5], "temp_range": [18, 35], "rainfall_range": [400, 1200], "humidity_range": [50, 80]},
    "tomato":         {"ph_range": [5.5, 7.5], "temp_range": [18, 35], "rainfall_range": [300, 1000], "humidity_range": [50, 80]},
    "watermelon":     {"ph_range": [5.5, 7.5], "temp_range": [22, 38], "rainfall_range": [300, 800],  "humidity_range": [40, 75]},
    "wheat":          {"ph_range": [5.5, 8.0], "temp_range": [8, 25],  "rainfall_range": [250, 1000], "humidity_range": [30, 70]},
}

# ===================================================================
# UTILITIES
# ===================================================================

def infer_season(temperature: float) -> int:
    if temperature >= 28:
        return 0   # Kharif
    if temperature <= 22:
        return 1   # Rabi
    return 2       # Zaid


def get_season_name(code: int) -> str:
    return ["Kharif", "Rabi", "Zaid"][code] if 0 <= code <= 2 else "Unknown"


def file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def compute_entropy(proba: np.ndarray) -> float:
    p = proba[proba > 0]
    return float(-np.sum(p * np.log(p)))


def validate_distribution(input_dict: dict, mode: str) -> list:
    warnings = []
    ranges = TRAINING_RANGES.get(mode, TRAINING_RANGES["soil"])
    for field, bounds in ranges.items():
        if field not in input_dict:
            continue
        val = input_dict[field]
        if val < bounds["min"] or val > bounds["max"]:
            warnings.append({
                "field": field,
                "value": val,
                "training_range": [bounds["min"], bounds["max"]],
            })
    return warnings


# ===================================================================
# STEP 1 — AGRONOMIC CONSTRAINT ENFORCEMENT
# ===================================================================

def apply_agronomic_constraints(
    proba: np.ndarray,
    crops_list: list,
    input_dict: dict,
    label_encoder=None,
) -> Tuple[np.ndarray, Dict[str, list]]:
    """
    Penalise probabilities for crops whose agronomic requirements
    are violated by current conditions. Applied BEFORE normalisation.
    """
    adjusted = proba.copy()
    ph = input_dict.get("ph", 6.5)
    temp = input_dict.get("temperature", 25)
    rain = input_dict.get("rainfall", 500)
    hum = input_dict.get("humidity", 60)

    violations: Dict[str, list] = {}

    for idx in range(len(proba)):
        if label_encoder is not None:
            crop = label_encoder.inverse_transform([idx])[0]
        else:
            crop = crops_list[idx]

        constraints = CROP_AGRO_CONSTRAINTS.get(crop)
        if constraints is None:
            continue

        crop_violations = []

        # pH check
        ph_lo, ph_hi = constraints["ph_range"]
        if ph < ph_lo or ph > ph_hi:
            crop_violations.append(f"pH {ph:.1f} outside [{ph_lo}, {ph_hi}]")
            if ph < 4.0 or ph > 9.5:
                adjusted[idx] *= AGRONOMIC_PENALTY_EXTREME
            else:
                adjusted[idx] *= AGRONOMIC_PENALTY_MILD

        # Temperature check
        t_lo, t_hi = constraints["temp_range"]
        if temp < t_lo or temp > t_hi:
            crop_violations.append(f"temp {temp:.1f}C outside [{t_lo}, {t_hi}]")
            if temp < 0 or temp > 48:
                adjusted[idx] *= AGRONOMIC_PENALTY_EXTREME
            else:
                adjusted[idx] *= AGRONOMIC_PENALTY_MILD

        # Rainfall check
        r_lo, r_hi = constraints["rainfall_range"]
        if rain < r_lo or rain > r_hi:
            crop_violations.append(f"rainfall {rain:.0f}mm outside [{r_lo}, {r_hi}]")
            adjusted[idx] *= AGRONOMIC_PENALTY_MILD

        # Humidity check
        h_lo, h_hi = constraints["humidity_range"]
        if hum < h_lo or hum > h_hi:
            crop_violations.append(f"humidity {hum:.0f}% outside [{h_lo}, {h_hi}]")
            adjusted[idx] *= AGRONOMIC_PENALTY_MILD

        if crop_violations:
            violations[crop] = crop_violations

    # Renormalise
    total = adjusted.sum()
    if total > 0:
        adjusted /= total
    else:
        adjusted = np.ones_like(proba) / len(proba)

    return adjusted, violations


# ===================================================================
# STEP 2 — OOD CONFIDENCE DAMPENING
# ===================================================================

CORE_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


def compute_ood_dampening(ood_warnings: list) -> Tuple[float, float, str]:
    """
    Returns (multiplier, cap, reason).
    multiplier applied to raw confidence, cap is hard ceiling.
    """
    if not ood_warnings:
        return 1.0, 1.0, ""

    n_ood = len(ood_warnings)
    n_total = len(CORE_FEATURES)
    ood_ratio = n_ood / n_total

    multiplier = 1.0 - (OOD_DAMPEN_FACTOR * ood_ratio)
    cap = 1.0

    if ood_ratio >= OOD_CAP_THRESHOLD:
        cap = OOD_MAX_CONFIDENCE

    fields = ", ".join(w["field"] for w in ood_warnings)
    reason = (
        f"OOD: {n_ood}/{n_total} features ({fields}), "
        f"mult={multiplier:.3f}, cap={cap:.0%}"
    )
    return multiplier, cap, reason


# ===================================================================
# STEP 3 — STRESS SCORE CALCULATION
# ===================================================================

STRESS_REFERENCE = {
    "N":           {"mid": 80,  "half_width": 80},
    "P":           {"mid": 50,  "half_width": 50},
    "K":           {"mid": 50,  "half_width": 50},
    "temperature": {"mid": 25,  "half_width": 15},
    "humidity":    {"mid": 65,  "half_width": 35},
    "ph":          {"mid": 6.5, "half_width": 2.0},
    "rainfall":    {"mid": 800, "half_width": 800},
}


def compute_stress_index(input_dict: dict) -> Tuple[float, Dict[str, float]]:
    per_feature = {}
    for feat, ref in STRESS_REFERENCE.items():
        val = input_dict.get(feat)
        if val is None:
            continue
        distance = abs(val - ref["mid"])
        normalised = min(distance / ref["half_width"], 2.0) / 2.0
        per_feature[feat] = round(normalised, 4)

    if not per_feature:
        return 0.0, {}

    overall = sum(per_feature.values()) / len(per_feature)
    return round(overall, 4), per_feature


def apply_stress_reduction(
    confidence: float, stress_index: float,
) -> Tuple[float, float]:
    """
    High stress (>0.6) reduces confidence by 20-40%.
    Returns (adjusted, reduction_fraction).
    """
    if stress_index <= STRESS_HIGH_THRESHOLD:
        return confidence, 0.0

    t = min((stress_index - STRESS_HIGH_THRESHOLD) / (1.0 - STRESS_HIGH_THRESHOLD), 1.0)
    reduction = STRESS_REDUCTION_MIN + t * (STRESS_REDUCTION_MAX - STRESS_REDUCTION_MIN)
    adjusted = confidence * (1.0 - reduction)
    return adjusted, reduction


def flatten_distribution(proba: np.ndarray, stress_index: float) -> np.ndarray:
    """Blend toward uniform when stress is high (increases entropy)."""
    if stress_index <= STRESS_HIGH_THRESHOLD:
        return proba

    t = min((stress_index - STRESS_HIGH_THRESHOLD) / (1.0 - STRESS_HIGH_THRESHOLD), 1.0)
    blend = 0.3 * t
    uniform = np.ones_like(proba) / len(proba)
    flattened = (1.0 - blend) * proba + blend * uniform

    total = flattened.sum()
    if total > 0:
        flattened /= total
    return flattened


# ===================================================================
# STEP 6 — ADVISORY RISK TIERS
# ===================================================================

def advisory_tier(confidence_pct: float, is_ood: bool) -> str:
    if confidence_pct > 85:
        tier = "Strongly Recommended"
    elif confidence_pct > 60:
        tier = "Recommended with Monitoring"
    elif confidence_pct > 40:
        tier = "Conditional / Trial Basis"
    else:
        tier = "Not Recommended"

    if is_ood:
        downgrade = {
            "Strongly Recommended": "Recommended with Monitoring",
            "Recommended with Monitoring": "Conditional / Trial Basis",
            "Conditional / Trial Basis": "Not Recommended",
            "Not Recommended": "Not Recommended",
        }
        tier = downgrade[tier]

    return tier


# ===================================================================
# STEP 7 — EXPLANATION LAYER
# ===================================================================

def generate_explanation(
    crop: str, input_dict: dict, stress_per_feature: dict,
    agro_violations: Dict[str, list], confidence_pct: float,
    is_ood: bool, tier: str,
) -> str:
    """
    Structured agronomic explanation. Every sentence is data-driven.
    """
    temp = input_dict.get("temperature", 25)
    rain = input_dict.get("rainfall", 500)
    ph = input_dict.get("ph", 6.5)
    hum = input_dict.get("humidity", 60)

    parts = []
    constraints = CROP_AGRO_CONSTRAINTS.get(crop, {})

    # Temperature
    t_range = constraints.get("temp_range", [15, 35])
    if t_range[0] <= temp <= t_range[1]:
        parts.append(
            f"Temperature ({temp:.1f}C) is within the suitable range "
            f"[{t_range[0]}-{t_range[1]}C] for {crop}."
        )
    elif temp < t_range[0]:
        deficit = t_range[0] - temp
        parts.append(
            f"Temperature ({temp:.1f}C) is {deficit:.1f}C below {crop}'s "
            f"minimum ({t_range[0]}C). Cold stress risk."
        )
    else:
        excess = temp - t_range[1]
        parts.append(
            f"Temperature ({temp:.1f}C) is {excess:.1f}C above {crop}'s "
            f"maximum ({t_range[1]}C). Heat stress risk."
        )

    # Rainfall
    r_range = constraints.get("rainfall_range", [300, 1500])
    if r_range[0] <= rain <= r_range[1]:
        parts.append(
            f"Rainfall ({rain:.0f}mm) matches {crop}'s water requirement "
            f"[{r_range[0]}-{r_range[1]}mm]."
        )
    elif rain < r_range[0]:
        parts.append(
            f"Rainfall ({rain:.0f}mm) is below {crop}'s minimum ({r_range[0]}mm). "
            "Supplementary irrigation strongly advised."
        )
    else:
        parts.append(
            f"Rainfall ({rain:.0f}mm) exceeds {crop}'s tolerance ({r_range[1]}mm). "
            "Waterlogging risk — ensure proper drainage."
        )

    # pH
    ph_range = constraints.get("ph_range", [5.5, 7.5])
    if ph_range[0] <= ph <= ph_range[1]:
        parts.append(
            f"Soil pH ({ph:.1f}) is within the optimal range [{ph_range[0]}-{ph_range[1]}]."
        )
    elif ph < ph_range[0]:
        parts.append(
            f"Soil pH ({ph:.1f}) is below {crop}'s ideal ({ph_range[0]}). "
            "Liming may be needed to reduce acidity."
        )
    else:
        parts.append(
            f"Soil pH ({ph:.1f}) exceeds {crop}'s upper limit ({ph_range[1]}). "
            "Soil amendment with sulfur or organic matter recommended."
        )

    # Humidity
    h_range = constraints.get("humidity_range", [40, 80])
    if hum < h_range[0]:
        parts.append(f"Humidity ({hum:.0f}%) is low for {crop} (needs >={h_range[0]}%).")
    elif hum > h_range[1]:
        parts.append(f"Humidity ({hum:.0f}%) is high — fungal disease risk for {crop}.")

    # Stress warnings
    high_stress = [f for f, v in stress_per_feature.items() if v > 0.6]
    if high_stress:
        parts.append(
            f"High agricultural stress on: {', '.join(high_stress)}. "
            "Monitor crop health closely."
        )

    # Boundary risk
    boundary = [f for f, v in stress_per_feature.items() if 0.4 < v <= 0.6]
    if boundary:
        parts.append(
            f"Near boundary conditions for: {', '.join(boundary)}. "
            "Slight environmental shifts could affect yield."
        )

    if is_ood:
        parts.append(
            "Some input values fall outside model training distribution. "
            "Confidence has been reduced accordingly."
        )

    return " ".join(parts)


# ===================================================================
# NUTRITION LOOKUP
# ===================================================================

NUTRITION_MAPPING = {
    "pigeonpea": "pigeonpeas", "sesamum": "sesame",
    "pearl_millet": "bajra", "finger_millet": "ragi", "sorghum": "jowar",
}

try:
    nutrients_df = pd.read_csv(os.path.join(BASE_DIR, "Nutrient.csv"))
    logger.info("Nutrition data loaded.")
except Exception as e:
    logger.error("Failed to load Nutrient.csv: %s", e)
    nutrients_df = pd.DataFrame()


def get_nutrition(crop_name: str) -> Optional[dict]:
    try:
        search = NUTRITION_MAPPING.get(crop_name.lower(), crop_name.lower())
        match = nutrients_df[
            nutrients_df["food_name"].str.contains(search, case=False, na=False)
        ]
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
    except Exception as e:
        logger.warning("Nutrition lookup failed for %s: %s", crop_name, e)
    return None


# ===================================================================
# MODEL CLASSES
# ===================================================================

class SoilPredictor:
    """V6 Stacked Ensemble — 51 crops, 10 features."""

    def __init__(self):
        t0 = time.time()
        model_file = os.path.join(BASE_DIR, "stacked_ensemble_v6.joblib")
        encoder_file = os.path.join(BASE_DIR, "label_encoder_v6.joblib")
        config_file = os.path.join(BASE_DIR, "stacked_v6_config.joblib")

        stacked = joblib.load(model_file)
        self.fold_models = stacked["fold_models"]
        self.meta_learner = stacked["meta_learner"]
        self.label_encoder = joblib.load(encoder_file)
        config = joblib.load(config_file)
        self.features = config["feature_names"]
        self.temperature_param = config.get("temperature", 0.9)

        self.crops = list(self.label_encoder.classes_)
        self.crop_count = len(self.crops)
        self.checksum = file_checksum(model_file)

        elapsed = (time.time() - t0) * 1000
        logger.info(
            "V6 Soil model loaded: %d crops, T=%.2f, checksum=%s (%.0fms)",
            self.crop_count, self.temperature_param, self.checksum, elapsed,
        )

    def predict_proba(self, input_dict: dict) -> np.ndarray:
        X = pd.DataFrame([input_dict])[self.features]
        base_preds = []
        for name in ["BalancedRF", "XGBoost", "LightGBM"]:
            fold_probs = np.mean(
                [m.predict_proba(X)[0] for m in self.fold_models[name]], axis=0
            )
            base_preds.append(fold_probs)

        meta_features = np.hstack(base_preds).reshape(1, -1)
        proba = self.meta_learner.predict_proba(meta_features)[0]

        if self.temperature_param != 1.0:
            log_p = np.log(np.clip(proba, 1e-10, 1.0))
            scaled = log_p / self.temperature_param
            scaled -= scaled.max()
            e = np.exp(scaled)
            proba = e / e.sum()

        return proba


class ExtendedPredictor:
    """Calibrated Random Forest — 51 crops, 10 features."""

    def __init__(self):
        t0 = time.time()
        model_file = os.path.join(BASE_DIR, "model_rf.joblib")
        encoder_file = os.path.join(BASE_DIR, "label_encoder.joblib")

        self.model = joblib.load(model_file)
        self.label_encoder = joblib.load(encoder_file)
        self.features = [
            "N", "P", "K", "temperature", "humidity",
            "ph", "rainfall", "season", "soil_type", "irrigation",
        ]

        self.crops = list(self.label_encoder.classes_)
        self.crop_count = len(self.crops)
        self.checksum = file_checksum(model_file)

        elapsed = (time.time() - t0) * 1000
        logger.info(
            "Extended RF: %d crops, checksum=%s (%.0fms)",
            self.crop_count, self.checksum, elapsed,
        )

    def predict_proba(self, input_dict: dict) -> np.ndarray:
        X = pd.DataFrame([input_dict])[self.features]
        return self.model.predict_proba(X)[0]


class HybridPredictor:
    """Confidence-adaptive blend of soil + extended."""

    V6_WEIGHT = 0.7
    RF_WEIGHT = 0.3
    CONFIDENCE_THRESHOLD = 0.3

    def __init__(self, soil: SoilPredictor, extended: ExtendedPredictor):
        self.soil = soil
        self.extended = extended

        soil_set = set(soil.crops)
        ext_set = set(extended.crops)
        self.unified_crops = sorted(soil_set | ext_set)
        self.crop_count = len(self.unified_crops)
        self.crop_to_idx = {c: i for i, c in enumerate(self.unified_crops)}

        logger.info("Hybrid predictor ready: %d crops", self.crop_count)

    def predict_proba(self, input_dict: dict) -> np.ndarray:
        soil_proba = self.soil.predict_proba(input_dict)
        ext_proba = self.extended.predict_proba(input_dict)

        sc = float(np.max(soil_proba))
        ec = float(np.max(ext_proba))

        if sc > self.CONFIDENCE_THRESHOLD and ec > self.CONFIDENCE_THRESHOLD:
            sw, ew = self.V6_WEIGHT, self.RF_WEIGHT
        elif sc > self.CONFIDENCE_THRESHOLD:
            sw, ew = 0.85, 0.15
        elif ec > self.CONFIDENCE_THRESHOLD:
            sw, ew = 0.15, 0.85
        else:
            sw, ew = 0.5, 0.5

        unified = np.zeros(self.crop_count)
        for i, crop in enumerate(self.soil.crops):
            if crop in self.crop_to_idx:
                unified[self.crop_to_idx[crop]] += soil_proba[i] * sw
        for i, crop in enumerate(self.extended.crops):
            if crop in self.crop_to_idx:
                unified[self.crop_to_idx[crop]] += ext_proba[i] * ew

        total = unified.sum()
        if total > 0:
            unified /= total
        return unified


# ===================================================================
# LOAD MODELS AT STARTUP
# ===================================================================

_soil: Optional[SoilPredictor] = None
_extended: Optional[ExtendedPredictor] = None
_hybrid: Optional[HybridPredictor] = None

try:
    _soil = SoilPredictor()
except Exception as e:
    logger.error("FAILED to load soil model: %s", e)

try:
    _extended = ExtendedPredictor()
except Exception as e:
    logger.error("FAILED to load extended model: %s", e)

if _soil and _extended:
    _hybrid = HybridPredictor(_soil, _extended)
else:
    logger.error("Cannot build hybrid — missing base model(s)")


def _assert_startup():
    errors = []
    if not _soil:
        errors.append("Soil model not loaded")
    elif _soil.crop_count != 51:
        errors.append(f"Soil has {_soil.crop_count} crops, expected 51")
    if not _extended:
        errors.append("Extended RF not loaded")
    elif _extended.crop_count != 51:
        errors.append(f"Extended RF has {_extended.crop_count} crops, expected 51")
    if not _hybrid:
        errors.append("Hybrid not available")
    if _soil:
        missing = [c for c in _soil.crops if c not in CROP_AGRO_CONSTRAINTS]
        if missing:
            errors.append(f"Missing agronomic constraints for: {missing}")
    for e in errors:
        logger.error("STARTUP: %s", e)
    if not errors:
        logger.info("All startup assertions passed (V7 advisory engine).")

_assert_startup()


# ===================================================================
# API MODELS
# ===================================================================

class PredictionInput(BaseModel):
    N: float = Field(..., ge=_ACC["N"]["min"], le=_ACC["N"]["max"])
    P: float = Field(..., ge=_ACC["P"]["min"], le=_ACC["P"]["max"])
    K: float = Field(..., ge=_ACC["K"]["min"], le=_ACC["K"]["max"])
    temperature: float = Field(..., ge=_ACC["temperature"]["min"],
                               le=_ACC["temperature"]["max"])
    humidity: float = Field(..., ge=_ACC["humidity"]["min"],
                            le=_ACC["humidity"]["max"])
    ph: float = Field(..., ge=_ACC["ph"]["min"], le=_ACC["ph"]["max"])
    rainfall: float = Field(..., ge=_ACC["rainfall"]["min"],
                            le=_ACC["rainfall"]["max"])
    moisture: Optional[float] = Field(43.5, ge=_ACC["moisture"]["min"],
                                      le=_ACC["moisture"]["max"])
    season: Optional[int] = Field(None, ge=_ACC["season"]["min"],
                                  le=_ACC["season"]["max"])
    soil_type: Optional[int] = Field(1, ge=_ACC["soil_type"]["min"],
                                     le=_ACC["soil_type"]["max"])
    irrigation: Optional[int] = Field(0, ge=_ACC["irrigation"]["min"],
                                      le=_ACC["irrigation"]["max"])
    mode: Optional[str] = Field("soil")
    top_n: Optional[int] = Field(3, ge=1, le=10)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Invalid input"},
    )


# ===================================================================
# V7 INFERENCE PIPELINE — single model
# ===================================================================

def run_model_pipeline(
    predictor, crops_list: list, input_dict: dict,
    model_name: str, model_type: str, checksum: str,
    feature_count: int, label_encoder=None,
    ood_warnings: list = None, stress_index: float = 0.0,
    stress_per_feature: dict = None,
) -> dict:
    """
    Full V7 pipeline for one model:
      Raw proba -> agronomic constraints -> stress flattening
      -> OOD dampening -> stress reduction -> 92% cap
    """
    raw_proba = predictor.predict_proba(input_dict)

    # Step 1: Agronomic constraints (before normalisation)
    constrained_proba, agro_violations = apply_agronomic_constraints(
        raw_proba, crops_list, input_dict, label_encoder,
    )

    # Step 3 (partial): Stress distribution flattening
    constrained_proba = flatten_distribution(constrained_proba, stress_index)

    # Top crop from constrained distribution
    top_idx = int(np.argmax(constrained_proba))
    raw_top_prob = float(constrained_proba[top_idx])

    if label_encoder is not None:
        top_crop = label_encoder.inverse_transform([top_idx])[0]
    else:
        top_crop = crops_list[top_idx]

    entropy = compute_entropy(constrained_proba)
    num_classes = len(crops_list)

    # Step 2: OOD dampening
    ood_mult, ood_cap, ood_reason = compute_ood_dampening(ood_warnings or [])
    dampened_prob = raw_top_prob * ood_mult
    dampened_prob = min(dampened_prob, ood_cap)

    # Step 3: Stress confidence reduction
    stress_adj_prob, stress_reduction = apply_stress_reduction(
        dampened_prob, stress_index,
    )

    # Step 8: Hard cap at 92%
    final_prob = min(stress_adj_prob, HARD_CONFIDENCE_CAP)
    final_conf_pct = round(final_prob * 100, 2)

    # Top-N with same V7 adjustments
    top_n_idx = np.argsort(constrained_proba)[-3:][::-1]
    is_ood = len(ood_warnings or []) > 0
    top_n = []
    for idx in top_n_idx:
        if label_encoder is not None:
            cname = label_encoder.inverse_transform([idx])[0]
        else:
            cname = crops_list[idx]

        cpct_raw = float(constrained_proba[idx])
        cpct_adj = cpct_raw * ood_mult
        cpct_adj = min(cpct_adj, ood_cap)
        cpct_adj, _ = apply_stress_reduction(cpct_adj, stress_index)
        cpct_adj = min(cpct_adj, HARD_CONFIDENCE_CAP)
        cpct = round(cpct_adj * 100, 2)

        tier = advisory_tier(cpct, is_ood)
        top_n.append({
            "crop": cname,
            "confidence": cpct,
            "advisory_tier": tier,
            "nutrition": get_nutrition(cname),
        })

    # Reliability score
    max_ent = float(np.log(num_classes)) if num_classes > 1 else 1.0
    norm_ent = min(entropy / max_ent, 1.0) if max_ent > 0 else 0.0
    reliability = round(
        (final_prob * RELIABILITY_WEIGHT_CONFIDENCE
         + (1.0 - norm_ent) * RELIABILITY_WEIGHT_ENTROPY) * 100, 2
    )
    reliability = min(reliability, 100.0)

    return {
        "model_name": model_name,
        "model_type": model_type,
        "checksum": checksum,
        "crop": top_crop,
        "confidence": final_conf_pct,
        "raw_model_probability": round(raw_top_prob * 100, 2),
        "entropy": round(entropy, 4),
        "reliability_score": reliability,
        "num_classes": num_classes,
        "feature_count": feature_count,
        "top_3": top_n,
        "proba": constrained_proba,
        "crops_list": crops_list,
        "agro_violations": agro_violations,
        "ood_dampening": ood_reason,
        "stress_reduction": round(stress_reduction * 100, 1) if stress_reduction else 0.0,
    }


# ===================================================================
# PREDICT ENDPOINT — V7 Advisory Engine
# ===================================================================

@app.post("/predict")
async def predict(data: PredictionInput):
    start = time.time()
    raw_mode = (data.mode or "soil").strip().lower()

    if raw_mode not in VALID_MODES:
        raise HTTPException(
            400, f"Invalid mode '{raw_mode}'. Use: {sorted(CANONICAL_MODES)}"
        )

    mode = MODE_ALIASES[raw_mode]
    deprecated_mode = raw_mode != mode

    # Season
    season = (data.season if data.season is not None
              else infer_season(data.temperature))

    input_dict = {
        "N": data.N, "P": data.P, "K": data.K,
        "temperature": data.temperature, "humidity": data.humidity,
        "ph": data.ph, "rainfall": data.rainfall,
        "season": season,
        "soil_type": data.soil_type,
        "irrigation": data.irrigation,
    }

    canonical = {
        "N": data.N, "P": data.P, "K": data.K,
        "temperature": data.temperature, "humidity": data.humidity,
        "ph": data.ph, "rainfall": data.rainfall,
    }

    # OOD detection
    ood_warnings = validate_distribution(canonical, mode)
    is_ood = len(ood_warnings) > 0

    # Stress index
    stress_index, stress_per_feature = compute_stress_index(canonical)

    # Run ALL 3 models through V7 pipeline
    model_results: Dict[str, dict] = {}

    pkw = dict(
        input_dict=input_dict,
        ood_warnings=ood_warnings,
        stress_index=stress_index,
        stress_per_feature=stress_per_feature,
    )

    try:
        if _soil:
            model_results["soil"] = run_model_pipeline(
                predictor=_soil, crops_list=_soil.crops,
                model_name="soil", model_type="stacked-ensemble-v6",
                checksum=_soil.checksum,
                feature_count=len(_soil.features),
                label_encoder=_soil.label_encoder, **pkw,
            )
    except Exception as e:
        logger.warning("Soil pipeline failed: %s", e)

    try:
        if _extended:
            model_results["extended"] = run_model_pipeline(
                predictor=_extended, crops_list=_extended.crops,
                model_name="extended", model_type="calibrated-rf",
                checksum=_extended.checksum,
                feature_count=len(_extended.features),
                label_encoder=_extended.label_encoder, **pkw,
            )
    except Exception as e:
        logger.warning("Extended pipeline failed: %s", e)

    try:
        if _hybrid:
            model_results["hybrid"] = run_model_pipeline(
                predictor=_hybrid, crops_list=_hybrid.unified_crops,
                model_name="hybrid", model_type="hybrid-v6-rf",
                checksum=(
                    f"{_soil.checksum}+{_extended.checksum}"
                    if _soil and _extended else "n/a"
                ),
                feature_count=10, label_encoder=None, **pkw,
            )
    except Exception as e:
        logger.warning("Hybrid pipeline failed: %s", e)

    if not model_results:
        raise HTTPException(503, "All models failed")

    # Step 5: Model selection rebalancing
    top_crops = {m: r["crop"] for m, r in model_results.items()}
    unique_crops = set(top_crops.values())

    # Agreement bonus
    crop_votes: Dict[str, list] = {}
    for mname, mres in model_results.items():
        crop_votes.setdefault(mres["crop"], []).append(mname)

    for crop, voters in crop_votes.items():
        if len(voters) >= 2:
            for mname in voters:
                model_results[mname]["reliability_score"] = round(min(
                    model_results[mname]["reliability_score"] + AGREEMENT_BONUS,
                    100.0,
                ), 2)
                model_results[mname]["agreement_bonus"] = True

    # If all models disagree, boost hybrid
    if len(unique_crops) == len(model_results) and len(model_results) >= 2:
        if "hybrid" in model_results:
            model_results["hybrid"]["reliability_score"] = round(min(
                model_results["hybrid"]["reliability_score"] + 10.0, 100.0,
            ), 2)
            model_results["hybrid"]["disagreement_override"] = True

    # If entropy is similar, slightly boost hybrid
    if "soil" in model_results and "extended" in model_results:
        ent_diff = abs(
            model_results["soil"]["entropy"]
            - model_results["extended"]["entropy"]
        )
        if ent_diff < 0.2 and "hybrid" in model_results:
            model_results["hybrid"]["reliability_score"] = round(min(
                model_results["hybrid"]["reliability_score"] + 3.0, 100.0,
            ), 2)

    # Select best
    best_name = max(
        model_results,
        key=lambda m: model_results[m]["reliability_score"],
    )
    best = model_results[best_name]

    # Step 4: Calibrated confidence
    agreement_score = (
        1.0 if len(unique_crops) == 1
        else (0.5 if len(unique_crops) == 2 else 0.0)
    )
    max_ent = (float(np.log(best["num_classes"]))
               if best["num_classes"] > 1 else 1.0)
    inv_entropy = (max(0.0, 1.0 - (best["entropy"] / max_ent))
                   if max_ent > 0 else 0.0)

    calibrated_conf = (
        0.6 * (best["confidence"] / 100)
        + 0.2 * agreement_score
        + 0.2 * inv_entropy
    )
    calibrated_conf = min(calibrated_conf, HARD_CONFIDENCE_CAP)
    calibrated_conf_pct = round(calibrated_conf * 100, 2)

    # Primary for backward compat
    primary = (model_results.get(mode, best) if mode != "both"
               else model_results.get("hybrid", best))

    # Top-N predictions from primary
    top_n_count = data.top_n or 3
    pri_proba = primary["proba"]
    pri_crops = primary["crops_list"]
    pri_le = None
    if primary["model_name"] == "soil" and _soil:
        pri_le = _soil.label_encoder
    elif primary["model_name"] == "extended" and _extended:
        pri_le = _extended.label_encoder

    top_idx = np.argsort(pri_proba)[-top_n_count:][::-1]
    predictions = []
    for idx in top_idx:
        if pri_le is not None:
            cname = pri_le.inverse_transform([idx])[0]
        else:
            cname = pri_crops[idx]

        cpct_raw = float(pri_proba[idx])
        ood_mult, ood_cap, _ = compute_ood_dampening(ood_warnings)
        cpct_adj = cpct_raw * ood_mult
        cpct_adj = min(cpct_adj, ood_cap)
        cpct_adj, _ = apply_stress_reduction(cpct_adj, stress_index)
        cpct_adj = min(cpct_adj, HARD_CONFIDENCE_CAP)
        cpct = round(cpct_adj * 100, 2)

        tier = advisory_tier(cpct, is_ood)
        predictions.append({
            "crop": cname,
            "confidence": cpct,
            "advisory_tier": tier,
            "nutrition": get_nutrition(cname),
        })

    # Step 7: Explanation
    explanation = generate_explanation(
        crop=best["crop"],
        input_dict=canonical,
        stress_per_feature=stress_per_feature,
        agro_violations=best.get("agro_violations", {}),
        confidence_pct=calibrated_conf_pct,
        is_ood=is_ood,
        tier=advisory_tier(calibrated_conf_pct, is_ood),
    )

    latency = round((time.time() - start) * 1000, 1)

    # Comparisons
    comparisons = {}
    for mname, mres in model_results.items():
        comparisons[mname] = {
            "crop": mres["crop"],
            "confidence": mres["confidence"],
            "raw_model_probability": mres["raw_model_probability"],
            "reliability_score": mres["reliability_score"],
            "entropy": mres["entropy"],
            "agreement_bonus": mres.get("agreement_bonus", False),
            "stress_reduction_pct": mres["stress_reduction"],
            "ood_dampening": mres["ood_dampening"],
            "agro_violations_count": len(mres.get("agro_violations", {})),
            "top_3": mres["top_3"],
        }

    best_tier = advisory_tier(calibrated_conf_pct, is_ood)

    resp: Dict[str, Any] = {
        # V7 advisory
        "best_model": best_name,
        "best_crop": best["crop"],
        "calibrated_confidence": calibrated_conf_pct,
        "best_reliability": best["reliability_score"],
        "advisory_tier": best_tier,
        "explanation": explanation,
        "stress_index": stress_index,
        "stress_per_feature": stress_per_feature,
        "comparisons": comparisons,

        # backward compat
        "mode": mode,
        "predictions": predictions,
        "top_3": predictions[:3],
        "model_info": {
            "version": "7.0",
            "type": primary["model_type"],
            "crops": primary["num_classes"],
            "checksum": primary["checksum"],
            "features_used": primary["feature_count"],
        },
        "confidence_info": {
            "calibrated_confidence": calibrated_conf_pct,
            "raw_model_probability": best["raw_model_probability"],
            "entropy": best["entropy"],
            "low_confidence": calibrated_conf_pct < 40,
        },
        "environment_info": {
            "season_used": get_season_name(season),
            "season_inferred": data.season is None,
            "soil_type": data.soil_type,
            "irrigation": data.irrigation,
            "moisture": data.moisture,
        },
        "latency_ms": latency,
    }

    if deprecated_mode:
        resp["deprecation_notice"] = (
            f"Mode '{raw_mode}' is deprecated. Use '{mode}' directly."
        )

    warning_parts = []
    if ood_warnings:
        resp["ood_warnings"] = ood_warnings
        fields = ", ".join(w["field"] for w in ood_warnings)
        warning_parts.append(f"OOD features: {fields}. Confidence dampened.")
    if stress_index > STRESS_HIGH_THRESHOLD:
        warning_parts.append(
            f"High agricultural stress (index={stress_index:.2f}). "
            "Confidence reduced."
        )
    if calibrated_conf_pct < 40:
        warning_parts.append("Low confidence — conditions may be unsuitable.")
    if best.get("entropy", 0) > ENTROPY_WARNING_THRESHOLD:
        warning_parts.append("High entropy — model uncertain.")
    if warning_parts:
        resp["warning"] = " ".join(warning_parts)

    logger.info(
        "PREDICT best=%s crop=%s cal=%.1f%% raw=%.1f%% tier=%s "
        "stress=%.2f ood=%d ms=%.0f "
        "N=%.1f P=%.1f K=%.1f T=%.1f H=%.1f pH=%.1f R=%.1f",
        best_name, best["crop"], calibrated_conf_pct,
        best["raw_model_probability"], best_tier,
        stress_index, len(ood_warnings), latency,
        data.N, data.P, data.K, data.temperature, data.humidity,
        data.ph, data.rainfall,
    )

    return resp


# ===================================================================
# INFO ENDPOINTS
# ===================================================================

@app.get("/predict")
def predict_hint():
    return {
        "message": "Use POST with JSON body.",
        "version": "7.0",
        "modes": sorted(CANONICAL_MODES),
        "aliases": {"original": "soil", "synthetic": "extended"},
        "advisory_tiers": [
            "Strongly Recommended (>85%)",
            "Recommended with Monitoring (60-85%)",
            "Conditional / Trial Basis (40-60%)",
            "Not Recommended (<40%)",
        ],
    }


@app.get("/")
def health():
    return {
        "status": "online",
        "version": "7.0",
        "architecture": "V7 Farmer Advisory Engine",
        "features": [
            "agronomic_constraints",
            "ood_dampening",
            "stress_scoring",
            "calibrated_confidence",
            "model_rebalancing",
            "advisory_tiers",
            "explanation_layer",
            "confidence_cap_92pct",
        ],
        "models": {
            "soil": {
                "loaded": _soil is not None,
                "type": "stacked-ensemble-v6",
                "crops": _soil.crop_count if _soil else 0,
                "checksum": _soil.checksum if _soil else None,
            },
            "extended": {
                "loaded": _extended is not None,
                "type": "calibrated-rf",
                "crops": _extended.crop_count if _extended else 0,
                "checksum": _extended.checksum if _extended else None,
            },
            "both": {
                "loaded": _hybrid is not None,
                "type": "hybrid-v6-rf",
                "crops": _hybrid.crop_count if _hybrid else 0,
            },
        },
    }


@app.get("/crops")
def get_crops():
    out = {}
    if _soil:
        out["soil"] = sorted(_soil.crops)
    if _extended:
        out["extended"] = sorted(_extended.crops)
    if _hybrid:
        out["both"] = sorted(_hybrid.unified_crops)
    return out


@app.get("/limits")
def get_limits():
    return FEATURE_RANGES


@app.get("/constraints")
def get_constraints():
    """Per-crop agronomic constraint dictionary."""
    return CROP_AGRO_CONSTRAINTS


# ===================================================================
# /recommend — UNIFIED ADVISORY ENDPOINT (no mode exposed)
# ===================================================================

class RecommendInput(BaseModel):
    """Input schema for /recommend — no mode field."""
    N: float = Field(..., ge=_ACC["N"]["min"], le=_ACC["N"]["max"])
    P: float = Field(..., ge=_ACC["P"]["min"], le=_ACC["P"]["max"])
    K: float = Field(..., ge=_ACC["K"]["min"], le=_ACC["K"]["max"])
    temperature: float = Field(..., ge=_ACC["temperature"]["min"],
                               le=_ACC["temperature"]["max"])
    humidity: float = Field(..., ge=_ACC["humidity"]["min"],
                            le=_ACC["humidity"]["max"])
    ph: float = Field(..., ge=_ACC["ph"]["min"], le=_ACC["ph"]["max"])
    rainfall: float = Field(..., ge=_ACC["rainfall"]["min"],
                            le=_ACC["rainfall"]["max"])
    moisture: Optional[float] = Field(43.5, ge=_ACC["moisture"]["min"],
                                      le=_ACC["moisture"]["max"])
    season: Optional[int] = Field(None, ge=_ACC["season"]["min"],
                                  le=_ACC["season"]["max"])
    soil_type: Optional[int] = Field(1, ge=_ACC["soil_type"]["min"],
                                     le=_ACC["soil_type"]["max"])
    irrigation: Optional[int] = Field(0, ge=_ACC["irrigation"]["min"],
                                      le=_ACC["irrigation"]["max"])


def _consensus_label(vote_count: int, total_models: int) -> str:
    """Classify model agreement strength."""
    if vote_count >= total_models:
        return "strong"
    if vote_count >= 2:
        return "moderate"
    return "weak"


@app.post("/recommend")
async def recommend(data: RecommendInput):
    """
    Unified advisory endpoint.

    Runs all 3 internal models, collects 3×Top-3 = 9 candidates,
    scores them with the aggregation formula, and returns the
    global Top-3 with no model architecture exposed.
    """
    start = time.time()

    season = (data.season if data.season is not None
              else infer_season(data.temperature))

    input_dict = {
        "N": data.N, "P": data.P, "K": data.K,
        "temperature": data.temperature, "humidity": data.humidity,
        "ph": data.ph, "rainfall": data.rainfall,
        "season": season,
        "soil_type": data.soil_type,
        "irrigation": data.irrigation,
    }

    canonical = {
        "N": data.N, "P": data.P, "K": data.K,
        "temperature": data.temperature, "humidity": data.humidity,
        "ph": data.ph, "rainfall": data.rainfall,
    }

    # Pre-compute shared signals
    ood_warnings = validate_distribution(canonical, "soil")
    is_ood = len(ood_warnings) > 0
    stress_index, stress_per_feature = compute_stress_index(canonical)

    pkw = dict(
        input_dict=input_dict,
        ood_warnings=ood_warnings,
        stress_index=stress_index,
        stress_per_feature=stress_per_feature,
    )

    # Run all 3 models through V7 pipeline
    model_results: Dict[str, dict] = {}
    model_configs = []
    if _soil:
        model_configs.append(("soil", _soil, _soil.crops, "stacked-ensemble-v6",
                              _soil.checksum, len(_soil.features), _soil.label_encoder))
    if _extended:
        model_configs.append(("extended", _extended, _extended.crops, "calibrated-rf",
                              _extended.checksum, len(_extended.features), _extended.label_encoder))
    if _hybrid:
        model_configs.append(("hybrid", _hybrid, _hybrid.unified_crops, "hybrid-v6-rf",
                              f"{_soil.checksum}+{_extended.checksum}" if _soil and _extended else "n/a",
                              10, None))

    for mname, pred, crops, mtype, chk, fcnt, le in model_configs:
        try:
            model_results[mname] = run_model_pipeline(
                predictor=pred, crops_list=crops,
                model_name=mname, model_type=mtype,
                checksum=chk, feature_count=fcnt,
                label_encoder=le, **pkw,
            )
        except Exception as e:
            logger.warning("%s pipeline failed: %s", mname, e)

    if not model_results:
        raise HTTPException(503, "All models failed")

    total_models = len(model_results)

    # Collect 9 candidates (3 models × top 3)
    # Track how many models agree on each crop
    crop_votes: Dict[str, int] = {}
    for mres in model_results.values():
        seen_in_model = set()
        for entry in mres.get("top_3", []):
            cname = entry["crop"]
            if cname not in seen_in_model:
                crop_votes[cname] = crop_votes.get(cname, 0) + 1
                seen_in_model.add(cname)

    # Build candidate list — deduplicate by crop, keep best confidence
    candidates: Dict[str, dict] = {}
    for mname, mres in model_results.items():
        for entry in mres.get("top_3", []):
            cname = entry["crop"]
            conf = entry["confidence"] / 100.0  # normalise to 0-1

            # Agreement bonus: +10% if 2+ models have this crop in top-3
            agreement = 0.10 if crop_votes.get(cname, 0) >= 2 else 0.0

            # Inverse entropy (from the model that produced this candidate)
            num_classes = mres.get("num_classes", 51)
            max_ent = float(np.log(num_classes)) if num_classes > 1 else 1.0
            entropy = mres.get("entropy", 0)
            inv_entropy = max(0.0, 1.0 - (entropy / max_ent)) if max_ent > 0 else 0.0

            # Low stress bonus
            low_stress = 0.10 if stress_index < 0.3 else 0.0

            # Final score
            score = (
                0.5 * conf
                + 0.2 * agreement
                + 0.2 * inv_entropy
                + 0.1 * low_stress
            )
            score = min(score, HARD_CONFIDENCE_CAP)

            if cname not in candidates or score > candidates[cname]["_score"]:
                tier_pct = round(score * 100, 2)
                candidates[cname] = {
                    "crop": cname,
                    "confidence": tier_pct,
                    "advisory_tier": advisory_tier(tier_pct, is_ood),
                    "stress_index": stress_index,
                    "explanation": generate_explanation(
                        crop=cname,
                        input_dict=canonical,
                        stress_per_feature=stress_per_feature,
                        agro_violations=mres.get("agro_violations", {}),
                        confidence_pct=tier_pct,
                        is_ood=is_ood,
                        tier=advisory_tier(tier_pct, is_ood),
                    ),
                    "model_consensus": _consensus_label(
                        crop_votes.get(cname, 0), total_models,
                    ),
                    "nutrition": get_nutrition(cname),
                    "_score": score,
                }

    # Sort by score descending, take top 3
    ranked = sorted(candidates.values(), key=lambda c: c["_score"], reverse=True)[:3]

    # Strip internal scoring field
    top_recommendations = []
    for c in ranked:
        c.pop("_score", None)
        top_recommendations.append(c)

    latency = round((time.time() - start) * 1000, 1)

    resp: Dict[str, Any] = {
        "top_recommendations": top_recommendations,
        "stress_index": stress_index,
        "stress_per_feature": stress_per_feature,
        "environment_info": {
            "season_used": get_season_name(season),
            "season_inferred": data.season is None,
            "soil_type": data.soil_type,
            "irrigation": data.irrigation,
            "moisture": data.moisture,
        },
        "latency_ms": latency,
    }

    warning_parts = []
    if ood_warnings:
        fields = ", ".join(w["field"] for w in ood_warnings)
        warning_parts.append(f"Some values ({fields}) fall outside typical ranges. Confidence adjusted.")
    if stress_index > STRESS_HIGH_THRESHOLD:
        warning_parts.append(
            f"High agricultural stress detected (index={stress_index:.2f}). "
            "Recommendations may have reduced confidence."
        )
    if top_recommendations and top_recommendations[0]["confidence"] < 40:
        warning_parts.append("Conditions may be challenging for most crops. Consider consulting local experts.")
    if warning_parts:
        resp["warning"] = " ".join(warning_parts)

    logger.info(
        "RECOMMEND top=%s conf=%.1f%% consensus=%s stress=%.2f ood=%d ms=%.0f",
        top_recommendations[0]["crop"] if top_recommendations else "?",
        top_recommendations[0]["confidence"] if top_recommendations else 0,
        top_recommendations[0]["model_consensus"] if top_recommendations else "?",
        stress_index, len(ood_warnings), latency,
    )

    return resp


@app.get("/recommend")
def recommend_hint():
    return {
        "message": "Use POST with JSON body.",
        "version": "7.1",
        "description": "Unified advisory engine — no model selection required.",
        "required_fields": ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"],
        "optional_fields": ["soil_type", "irrigation", "moisture", "season"],
    }

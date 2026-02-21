"""Crop Recommendation ML API — HuggingFace Space (v3.0)

Serves the v3 stacked ensemble only. No fallback to legacy models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_VERSION = "3.0"
BASE_DIR = Path(__file__).resolve().parent

FEATURES_PUBLIC = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "season",
    "soil_type",
    "irrigation",
    "moisture",
]

SEASON_MAP = {"Kharif": 0, "Rabi": 1, "Zaid": 2}
SEASON_REVERSE = {0: "Kharif", 1: "Rabi", 2: "Zaid"}
SOIL_MAP = {"sandy": 0, "loamy": 1, "clay": 2}
SOIL_REVERSE = {0: "sandy", 1: "loamy", 2: "clay"}
IRRIG_MAP = {"rainfed": 0, "irrigated": 1}
IRRIG_REVERSE = {0: "rainfed", 1: "irrigated"}


def _load_required_artifacts():
    try:
        stacked_model = joblib.load(BASE_DIR / "stacked_ensemble_v3.joblib")
        label_encoder = joblib.load(BASE_DIR / "label_encoder_v3.joblib")
        inference_config = joblib.load(BASE_DIR / "stacked_v3_config.joblib")
        binary_classifiers = joblib.load(BASE_DIR / "binary_classifiers_v3.joblib")
    except Exception as e:
        raise RuntimeError("V3 model not found") from e

    if not isinstance(stacked_model, dict) or "fold_models" not in stacked_model or "meta_learner" not in stacked_model:
        raise RuntimeError("V3 model not found")

    feature_names = inference_config.get("feature_names")
    if not feature_names:
        feature_names = stacked_model.get("feature_names")
    if not feature_names:
        raise RuntimeError("V3 model not found")

    return stacked_model, label_encoder, inference_config, binary_classifiers, list(feature_names)


stacked_model, label_encoder, v3_config, binary_classifiers, FEATURES_MODEL = _load_required_artifacts()

app = FastAPI(title="Crop Recommendation ML API", version=APP_VERSION)


def infer_season(temperature: float) -> int:
    if temperature >= 28:
        return 0
    elif temperature <= 22:
        return 1
    else:
        return 2


class PredictionInput(BaseModel):
    N: float = Field(..., description="Nitrogen content (kg/ha)")
    P: float = Field(..., description="Phosphorus content (kg/ha)")
    K: float = Field(..., description="Potassium content (kg/ha)")
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Humidity (%)")
    ph: float = Field(..., description="Soil pH")
    rainfall: float = Field(..., description="Rainfall (mm)")
    moisture: float = Field(..., description="Soil moisture (%) or relative index")
    season: Optional[int] = Field(
        None,
        description="Season (0=Kharif, 1=Rabi, 2=Zaid). Auto-inferred if not provided."
    )
    soil_type: Optional[int] = Field(
        1,
        description="Soil type (0=sandy, 1=loamy, 2=clay). Defaults to loamy."
    )
    irrigation: Optional[int] = Field(
        0,
        description="Irrigation (0=rainfed, 1=irrigated). Defaults to rainfed."
    )
    top_n: Optional[int] = Field(3, description="Number of top predictions to return")


def _apply_temperature(proba: np.ndarray, temperature: float) -> np.ndarray:
    if temperature == 1.0:
        return proba
    log_p = np.log(np.clip(proba, 1e-12, 1.0))
    scaled = log_p / float(temperature)
    scaled -= scaled.max()
    e = np.exp(scaled)
    return e / (e.sum() + 1e-12)


def _apply_inv_freq(proba: np.ndarray, weights: np.ndarray) -> np.ndarray:
    adj = proba * weights
    return adj / (adj.sum() + 1e-12)


def _apply_thresholds(proba: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    adj = proba / np.clip(thresholds, 1e-6, None)
    return adj / (adj.sum() + 1e-12)


def _apply_entropy_penalty(
    proba: np.ndarray,
    dominant_mask: np.ndarray,
    penalty: float,
    entropy_threshold: float,
) -> np.ndarray:
    p = proba.copy()
    ent = -np.sum(p * np.log(p + 1e-12))
    if ent < float(entropy_threshold):
        top = int(np.argmax(p))
        if bool(dominant_mask[top]):
            removed = p[top] * float(penalty)
            p[top] -= removed
            others = np.ones(len(p), dtype=bool)
            others[top] = False
            s = p[others].sum()
            if s > 0:
                p[others] += removed * (p[others] / s)
    return p


def _build_feature_vector(data: PredictionInput) -> np.ndarray:
    season = data.season if data.season is not None else infer_season(data.temperature)
    soil_type = data.soil_type if data.soil_type is not None else 1
    irrigation = data.irrigation if data.irrigation is not None else 0

    # Public API uses N/P/K; model expects n/p/k.
    values = {
        "n": float(data.N),
        "p": float(data.P),
        "k": float(data.K),
        "temperature": float(data.temperature),
        "humidity": float(data.humidity),
        "ph": float(data.ph),
        "rainfall": float(data.rainfall),
        "season": float(season),
        "soil_type": float(soil_type),
        "irrigation": float(irrigation),
        "moisture": float(data.moisture),
    }

    x = np.array([[values[name] for name in FEATURES_MODEL]], dtype=float)

    feature_scaling = v3_config.get("feature_scaling") or {}
    if isinstance(feature_scaling, dict) and feature_scaling:
        for i, name in enumerate(FEATURES_MODEL):
            if name in feature_scaling:
                try:
                    x[0, i] *= float(feature_scaling[name])
                except Exception:
                    pass

    return x


def _stacked_predict_proba(x: np.ndarray) -> np.ndarray:
    fold_models = stacked_model["fold_models"]
    meta_learner = stacked_model["meta_learner"]

    n_classes = int(stacked_model.get("n_classes") or v3_config.get("n_classes") or len(label_encoder.classes_))

    preds = []
    for name in fold_models:
        models = fold_models[name]
        if not models:
            raise RuntimeError("V3 model not found")

        model_preds = np.zeros((len(x), n_classes), dtype=float)
        for m in models:
            model_preds += m.predict_proba(x) / len(models)
        preds.append(model_preds)

    meta_features = np.hstack(preds)
    return meta_learner.predict_proba(meta_features)[0]


def _apply_binary_refinement(x: np.ndarray, proba: np.ndarray) -> np.ndarray:
    if not isinstance(binary_classifiers, dict) or len(binary_classifiers) == 0:
        return proba

    top2 = np.argsort(proba)[-2:][::-1]
    a = str(label_encoder.inverse_transform([int(top2[0])])[0])
    b = str(label_encoder.inverse_transform([int(top2[1])])[0])

    key = (a, b)
    invert = False
    if key not in binary_classifiers:
        key = (b, a)
        invert = True
        if key not in binary_classifiers:
            return proba

    clf = binary_classifiers[key]
    pair = clf.predict_proba(x)[0]
    p_second = float(pair[1])
    if invert:
        # key=(b,a) means prob of 'a' (the second element) is pair[1]
        p_a = p_second
        p_b = 1.0 - p_second
    else:
        p_b = p_second
        p_a = 1.0 - p_second

    out = proba.copy()
    out[int(top2[0])] = p_a
    out[int(top2[1])] = p_b
    return out / (out.sum() + 1e-12)


@app.post("/predict")
def predict(data: PredictionInput):
    try:
        top_n = data.top_n or 3

        x = _build_feature_vector(data)
        proba = _stacked_predict_proba(x)

        # Calibration (v3 config)
        proba = _apply_temperature(proba, float(v3_config.get("temperature", 1.0)))
        inv_w = np.array(v3_config.get("inv_freq_weights", np.ones_like(proba)), dtype=float)
        if inv_w.shape[0] == proba.shape[0]:
            proba = _apply_inv_freq(proba, inv_w)
        thresholds = np.array(v3_config.get("class_thresholds", np.ones_like(proba) * 0.5), dtype=float)
        if thresholds.shape[0] == proba.shape[0]:
            proba = _apply_thresholds(proba, thresholds)

        dominant_mask = np.array(v3_config.get("dominant_mask", np.zeros_like(proba, dtype=bool)))
        if dominant_mask.shape[0] == proba.shape[0]:
            proba = _apply_entropy_penalty(
                proba,
                dominant_mask,
                penalty=float(v3_config.get("dominance_penalty", 0.15)),
                entropy_threshold=float(v3_config.get("entropy_threshold", 0.4)),
            )
            proba = proba / (proba.sum() + 1e-12)

        # Pairwise refinement for top-2 if a binary classifier exists.
        proba = _apply_binary_refinement(x, proba)

        top_indices = np.argsort(proba)[-top_n:][::-1]

        predictions = []
        for idx in top_indices:
            crop_name = label_encoder.inverse_transform([int(idx)])[0]
            confidence = float(proba[int(idx)])
            predictions.append({
                "crop": crop_name,
                "confidence": confidence,
                "nutrition": None,
            })

        return {
            "predictions": predictions,
            "season_used": SEASON_REVERSE.get(
                data.season if data.season is not None else infer_season(data.temperature),
                "Unknown",
            ),
            "soil_type_used": SOIL_REVERSE.get(data.soil_type if data.soil_type is not None else 1, "Unknown"),
            "irrigation_used": IRRIG_REVERSE.get(data.irrigation if data.irrigation is not None else 0, "Unknown"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def health():
    return {
        "status": "ML Model is Live",
        "model_version": APP_VERSION,
        "model_loaded": True,
        "calibrated": True,
        "available_crops": list(label_encoder.classes_),
        "features": FEATURES_PUBLIC,
    }


@app.get("/crops")
def get_crops():
    return {"crops": list(label_encoder.classes_)}

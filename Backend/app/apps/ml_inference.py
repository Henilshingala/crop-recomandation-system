"""
Crop Recommendation System — ML Inference (Dual-Mode, v3 Stacked Ensemble)
===========================================================================
Loads models at startup and exposes three prediction modes:

  "honest"  → stacked_ensemble_v3.joblib  (19 crops, stacked ensemble:
               BalancedRF + XGBoost + LightGBM + LogisticRegression meta)
  "v2"      → model_real_world_honest_v2.joblib  (19 crops, legacy v2)
  "hybrid"  → HybridPredictorV2  (54 unified crops, all 6 anti-bias fixes)

All inference is vectorised (single predict_proba call per model).
"""

import json
import logging
import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np

from django.conf import settings

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════
# Constants (duplicated from hybrid_model.py so backend has zero imports
# from the Aiml training scripts)
# ═════════════════════════════════════════════════════════════════════════

CROP_NAME_MAP_REAL_TO_SYNTH = {
    "pigeonpea":     "pigeonpeas",
    "sesamum":       "sesame",
    "pearl_millet":  "bajra",
    "finger_millet": "ragi",
    "sorghum":       "jowar",
}
CROP_NAME_MAP_SYNTH_TO_REAL = {v: k for k, v in CROP_NAME_MAP_REAL_TO_SYNTH.items()}

W_REAL_DEFAULT    = 0.60
W_SYNTH_DEFAULT   = 0.40
W_REAL_HIGH_CONF  = 0.75
W_SYNTH_HIGH_CONF = 0.25
W_REAL_LOW_CONF   = 0.50
W_SYNTH_LOW_CONF  = 0.50

# Anti-bias thresholds (must match hybrid_model.py training constants)
ENTROPY_THRESHOLD        = 0.4
DOMINANCE_FREQ_THRESHOLD = 0.25
DOMINANCE_PENALTY        = 0.12


# ═════════════════════════════════════════════════════════════════════════
# Resolve AIML directory
# ═════════════════════════════════════════════════════════════════════════

def _get_aiml_dir() -> Path:
    env = os.environ.get("AI_ML_DIR")
    if env:
        return Path(env)
    return settings.BASE_DIR.parent.parent / "Aiml"


# ═════════════════════════════════════════════════════════════════════════
# Anti-bias probability corrections
# ═════════════════════════════════════════════════════════════════════════

def apply_temperature(proba: np.ndarray, T: float) -> np.ndarray:
    """Softmax temperature scaling: p_i^{1/T} / Σ p_j^{1/T}."""
    if T == 1.0:
        return proba
    log_p = np.log(np.clip(proba, 1e-10, 1.0))
    scaled = log_p / T
    if proba.ndim == 1:
        scaled -= scaled.max()
        e = np.exp(scaled)
        return e / e.sum()
    else:
        scaled -= scaled.max(axis=1, keepdims=True)
        e = np.exp(scaled)
        return e / e.sum(axis=1, keepdims=True)


def apply_inv_freq(proba: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Multiply probs by inverse-frequency weights and renormalise."""
    adj = proba * weights
    if proba.ndim == 1:
        return adj / (adj.sum() + 1e-10)
    else:
        return adj / (adj.sum(axis=1, keepdims=True) + 1e-10)


def apply_entropy_penalty(
    proba: np.ndarray,
    dominant_mask: np.ndarray,
    penalty: float = DOMINANCE_PENALTY,
) -> np.ndarray:
    """Reduce dominant-crop probability when prediction entropy is very low."""
    p = proba.copy()
    ent = -np.sum(p * np.log(p + 1e-10))
    if ent < ENTROPY_THRESHOLD:
        top = int(np.argmax(p))
        if dominant_mask[top]:
            removed = p[top] * penalty
            p[top] -= removed
            others = np.ones(len(p), dtype=bool)
            others[top] = False
            s = p[others].sum()
            if s > 0:
                p[others] += removed * (p[others] / s)
            else:
                p[others] += removed / max(1, others.sum())
    return p


# ═════════════════════════════════════════════════════════════════════════
# HybridPredictorV2  (self-contained, all 6 anti-bias corrections)
# ═════════════════════════════════════════════════════════════════════════

class HybridPredictorV2:
    """
    Enhanced hybrid predictor with 6 anti-bias corrections:
      1. Temperature-scaled honest probabilities (T=0.75)
      2. Inverse-frequency normalisation (α=0.60)
      3. Confidence-adaptive blending (real ↔ synthetic)
      4. Entropy-based dominance penalty
      5. Binary-classifier overrides for confused crop pairs
      6. SHAP-informed feature scaling at input stage
    """

    def __init__(
        self,
        real_model,
        real_encoder,
        synth_model,
        synth_encoder,
        temperature: float = 1.0,
        inv_freq_weights: Optional[np.ndarray] = None,
        binary_classifiers: Optional[dict] = None,
        feature_scaling: Optional[dict] = None,
        dominance_rates: Optional[dict] = None,
    ):
        self.real_model    = real_model
        self.real_encoder  = real_encoder
        self.real_crops    = list(real_encoder.classes_)
        self.synth_model   = synth_model
        self.synth_encoder = synth_encoder
        self.synth_crops   = list(synth_encoder.classes_)

        self.temperature        = temperature
        self.inv_freq_weights   = inv_freq_weights
        self.binary_classifiers = binary_classifiers or {}
        self.feature_scaling    = feature_scaling or {}
        self.dominance_rates    = dominance_rates or {}

        # Synth-only crops
        real_mapped = {CROP_NAME_MAP_REAL_TO_SYNTH.get(c, c) for c in self.real_crops}
        self.synth_only = {
            c for c in self.synth_crops
            if c not in real_mapped
            and CROP_NAME_MAP_SYNTH_TO_REAL.get(c, c) not in set(self.real_crops)
        }

        # Unified crop list (canonical = synth name)
        unified = list(self.synth_crops)
        for c in self.real_crops:
            m = CROP_NAME_MAP_REAL_TO_SYNTH.get(c, c)
            if m not in unified:
                unified.append(m)
        self.unified_crops = sorted(unified)

        # Fast index maps
        self._ri = {c: i for i, c in enumerate(self.real_crops)}
        self._si = {c: i for i, c in enumerate(self.synth_crops)}

        # Dominant mask for entropy-penalty step
        self.dom_mask = np.zeros(len(self.unified_crops), dtype=bool)
        for ui, uc in enumerate(self.unified_crops):
            rn = CROP_NAME_MAP_SYNTH_TO_REAL.get(uc, uc)
            mn = CROP_NAME_MAP_REAL_TO_SYNTH.get(uc, uc)
            if (self.dominance_rates.get(rn, 0) > DOMINANCE_FREQ_THRESHOLD
                    or self.dominance_rates.get(mn, 0) > DOMINANCE_FREQ_THRESHOLD):
                self.dom_mask[ui] = True

    def _scale(self, f: dict) -> dict:
        out = f.copy()
        for k, s in self.feature_scaling.items():
            if k in out:
                out[k] = out[k] * s
        return out

    def predict(self, features: dict) -> dict:
        """
        Parameters
        ----------
        features : dict
            Keys: n, p, k, temperature, humidity, ph, rainfall,
                  season, soil_type, irrigation, moisture

        Returns
        -------
        dict with top1, top3, confidence, source_dominance, rule_triggered,
             real_top1, real_confidence, synth_top1, synth_confidence
        """
        f = self._scale(features)

        X_real = np.array([[
            f["n"], f["p"], f["k"],
            f["temperature"], f["humidity"], f["ph"], f["rainfall"],
            f["season"], f["soil_type"], f["irrigation"], f["moisture"],
        ]])
        X_synth = np.array([[
            f["n"], f["p"], f["k"],
            f["temperature"], f["humidity"], f["ph"], f["rainfall"],
            f["season"], f["soil_type"], f["irrigation"],
        ]])

        # Raw probabilities
        pr = self.real_model.predict_proba(X_real)[0]
        ps = self.synth_model.predict_proba(X_synth)[0]

        # 1 + 2: Temperature + inverse-frequency on honest probs
        pr = apply_temperature(pr, self.temperature)
        if self.inv_freq_weights is not None:
            pr = apply_inv_freq(pr, self.inv_freq_weights)

        real_top  = int(np.argmax(pr))
        real_crop = self.real_crops[real_top]
        real_conf = float(pr[real_top]) * 100

        synth_top  = int(np.argmax(ps))
        synth_crop = self.synth_crops[synth_top]
        synth_conf = float(ps[synth_top]) * 100

        # 3: Confidence-adaptive blending
        if real_conf > 85:
            w_r, w_s, rule = W_REAL_HIGH_CONF, W_SYNTH_HIGH_CONF, "HIGH_CONF_REAL"
        elif real_conf < 50:
            w_r, w_s, rule = W_REAL_LOW_CONF, W_SYNTH_LOW_CONF, "LOW_CONF_REAL"
        else:
            w_r, w_s, rule = W_REAL_DEFAULT, W_SYNTH_DEFAULT, "DEFAULT"

        damp = 1.0 - float(pr[real_top])
        blended = np.zeros(len(self.unified_crops))
        for ui, crop in enumerate(self.unified_crops):
            rn  = CROP_NAME_MAP_SYNTH_TO_REAL.get(crop, crop)
            p_r = float(pr[self._ri[rn]])    if rn   in self._ri else 0.0
            p_s = float(ps[self._si[crop]])  if crop in self._si else 0.0
            if crop in self.synth_only:
                blended[ui] = w_s * p_s * damp
            elif rn in self._ri and crop not in self._si:
                blended[ui] = w_r * p_r
            elif rn in self._ri:
                blended[ui] = w_r * p_r + w_s * p_s
            else:
                blended[ui] = w_s * p_s * damp

        t = blended.sum()
        if t > 0:
            blended /= t

        # 4: Entropy-based dominance penalty
        blended = apply_entropy_penalty(blended, self.dom_mask)
        t = blended.sum()
        if t > 0:
            blended /= t

        # 5: Binary classifier override for confused pairs
        top_ui   = int(np.argmax(blended))
        top_crop = self.unified_crops[top_ui]
        for (ca, cb), clf in self.binary_classifiers.items():
            ca_s = CROP_NAME_MAP_REAL_TO_SYNTH.get(ca, ca)
            cb_s = CROP_NAME_MAP_REAL_TO_SYNTH.get(cb, cb)
            if top_crop in (ca, cb, ca_s, cb_s):
                bp = clf.predict_proba(X_real)[0]
                if max(bp) > 0.70:
                    chosen   = ca if bp[0] > bp[1] else cb
                    chosen_s = CROP_NAME_MAP_REAL_TO_SYNTH.get(chosen, chosen)
                    if chosen_s in self.unified_crops and chosen_s != top_crop:
                        new_ui = self.unified_crops.index(chosen_s)
                        blended[new_ui], blended[top_ui] = (
                            blended[top_ui], blended[new_ui]
                        )
                break

        ranked = np.argsort(blended)[::-1]
        top1   = self.unified_crops[ranked[0]]
        top1_c = blended[ranked[0]] * 100
        top3   = [
            (self.unified_crops[ranked[j]], round(blended[ranked[j]] * 100, 2))
            for j in range(min(3, len(ranked)))
        ]

        if top1 in self.synth_only:
            source = "synthetic_only"
        else:
            rn  = CROP_NAME_MAP_SYNTH_TO_REAL.get(top1, top1)
            r_p = float(pr[self._ri[rn]]) if rn in self._ri else 0.0
            sn  = CROP_NAME_MAP_REAL_TO_SYNTH.get(top1, top1)
            s_p = (
                float(ps[self._si[sn]])    if sn   in self._si else
                float(ps[self._si[top1]])  if top1 in self._si else 0.0
            )
            source = "real" if w_r * r_p >= w_s * s_p else "synthetic"

        return {
            "top1": top1,
            "top3": top3,
            "confidence": round(top1_c, 2),
            "source_dominance": source,
            "rule_triggered": rule,
            "real_top1": real_crop,
            "real_confidence": round(real_conf, 2),
            "synth_top1": synth_crop,
            "synth_confidence": round(synth_conf, 2),
        }


# ═════════════════════════════════════════════════════════════════════════
# CropPredictor  (singleton, loads everything at first use)
# ═════════════════════════════════════════════════════════════════════════

class CropPredictor:
    """
    Dual-mode crop prediction engine.

    Modes
    ─────
    "honest" — 19-crop v3 stacked ensemble (BalancedRF + XGBoost + LightGBM + meta)
    "v2"     — 19-crop v2 honest model (legacy temperature + inv-freq + entropy)
    "hybrid" — 54-crop unified HybridPredictorV2 (all 6 anti-bias corrections)
    """

    _instance: Optional["CropPredictor"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    # ── lazy load ───────────────────────────────────────────────────────

    def _ensure_loaded(self):
        if self._loaded:
            return

        aiml = _get_aiml_dir()
        logger.info("CropPredictor: loading models from %s", aiml)

        # ── v3 stacked ensemble model (primary) ──────────────────────
        v3_model_path = aiml / "stacked_ensemble_v3.joblib"
        if v3_model_path.exists():
            try:
                v3_model = joblib.load(v3_model_path)
                self._v3_fold_models = v3_model["fold_models"]
                self._v3_meta_learner = v3_model["meta_learner"]
                self._v3_n_classes = v3_model["n_classes"]
                self._v3_available = True
                logger.info("  v3 stacked ensemble loaded — %d classes, %d base models",
                           self._v3_n_classes, len(self._v3_fold_models))
            except Exception as e:
                self._v3_available = False
                logger.warning("  v3 stacked model failed to load (%s) — using v2 fallback", e)
        else:
            self._v3_available = False
            logger.info("  stacked_ensemble_v3.joblib not found — using v2 model")

        # ── v3 config ────────────────────────────────────────────────
        v3_cfg_path = aiml / "stacked_v3_config.joblib"
        if v3_cfg_path.exists():
            v3_cfg = joblib.load(v3_cfg_path)
            self._v3_temperature = float(v3_cfg.get("temperature", 1.0))
            self._v3_inv_freq_weights = np.array(v3_cfg.get("inv_freq_weights", [])) if v3_cfg.get("inv_freq_weights") else None
            self._v3_class_thresholds = np.array(v3_cfg.get("class_thresholds", [])) if v3_cfg.get("class_thresholds") else None
            self._v3_dominance_rates = v3_cfg.get("dominance_rates", {})
            self._v3_feature_names = v3_cfg.get("feature_names", [])
            self._v3_crops = v3_cfg.get("crops", [])
            logger.info("  v3 config loaded — T=%.2f, α=%.2f, %d crops",
                       self._v3_temperature,
                       float(v3_cfg.get("inv_freq_alpha", 0.75)),
                       len(self._v3_crops))
        else:
            self._v3_temperature = 1.0
            self._v3_inv_freq_weights = None
            self._v3_class_thresholds = None
            self._v3_dominance_rates = {}
            self._v3_feature_names = []
            self._v3_crops = []

        # ── v3 label encoder ─────────────────────────────────────────
        v3_encoder_path = aiml / "label_encoder_v3.joblib"
        if v3_encoder_path.exists():
            self._v3_encoder = joblib.load(v3_encoder_path)
            self._v3_crops = list(self._v3_encoder.classes_)
        elif self._v3_available and not self._v3_crops:
            # Fallback to using crops from config
            pass

        # ── v2 honest model (legacy/fallback) ────────────────────────
        self._honest_model   = joblib.load(aiml / "model_real_world_honest_v2.joblib")
        self._honest_encoder = joblib.load(aiml / "label_encoder_real_honest.joblib")
        self._honest_crops   = list(self._honest_encoder.classes_)
        logger.info("  honest v2 model loaded — %d crops", len(self._honest_crops))

        # ── anti-bias config ─────────────────────────────────────────
        cfg_path = aiml / "hybrid_v2_config.joblib"
        if cfg_path.exists():
            cfg = joblib.load(cfg_path)
            self._temperature      = float(cfg.get("temperature", 1.0))
            self._inv_freq_weights = cfg.get("inv_freq_weights")
            self._binary_clfs      = cfg.get("binary_classifiers", {})
            self._feature_scaling  = cfg.get("feature_scaling", {})
            self._dominance_rates  = cfg.get("dominance_rates", {})
            logger.info(
                "  v2 config loaded — T=%.2f, α=%.2f, %d binary classifiers, %d scaling rules",
                self._temperature,
                float(cfg.get("inv_freq_alpha", 0.0)),
                len(self._binary_clfs),
                len(self._feature_scaling),
            )
        else:
            logger.warning("  hybrid_v2_config.joblib not found — using defaults")
            self._temperature      = 1.0
            self._inv_freq_weights = None
            self._binary_clfs      = {}
            self._feature_scaling  = {}
            self._dominance_rates  = {}

        # ── synthetic model (needed by hybrid mode) ──────────────────
        synth_model   = joblib.load(aiml / "model_rf.joblib")
        synth_encoder = joblib.load(aiml / "label_encoder.joblib")
        logger.info("  synthetic model loaded — %d crops", len(synth_encoder.classes_))

        # ── HybridPredictorV2 ─────────────────────────────────────────
        self._hybrid = HybridPredictorV2(
            real_model=self._honest_model,
            real_encoder=self._honest_encoder,
            synth_model=synth_model,
            synth_encoder=synth_encoder,
            temperature=self._temperature,
            inv_freq_weights=self._inv_freq_weights,
            binary_classifiers=self._binary_clfs,
            feature_scaling=self._feature_scaling,
            dominance_rates=self._dominance_rates,
        )
        logger.info(
            "  HybridPredictorV2 ready — %d unified crops",
            len(self._hybrid.unified_crops),
        )

        # ── metadata ─────────────────────────────────────────────
        meta_path = aiml / "hybrid_metadata.json"
        if meta_path.exists():
            with open(meta_path) as fh:
                self._hybrid_meta = json.load(fh)
        else:
            self._hybrid_meta = {}

        self._loaded = True
        logger.info("CropPredictor: all models loaded successfully")

    # ── public API ─────────────────────────────────────────────────────

    def predict(self, features: dict, mode: str = "honest") -> dict:
        """
        Run prediction in the specified mode.

        Parameters
        ----------
        features : dict
            n, p, k, temperature, humidity, ph, rainfall,
            season, soil_type, irrigation, moisture
        mode : "honest" | "v2" | "hybrid"

        Returns
        -------
        Structured dict matching the API response schema.
        """
        self._ensure_loaded()

        if mode == "hybrid":
            return self._predict_hybrid(features)
        if mode == "v2":
            return self._predict_honest_v2(features)
        # Default "honest" uses v3 stacked if available, else v2
        if self._v3_available:
            return self._predict_v3_stacked(features)
        return self._predict_honest_v2(features)

    def _predict_v3_stacked(self, f: dict) -> dict:
        """V3 stacked ensemble: 19 crops, BalancedRF + XGBoost + LightGBM + meta."""
        feat_order = [
            "n", "p", "k", "temperature", "humidity",
            "ph", "rainfall", "season", "soil_type",
            "irrigation", "moisture",
        ]
        row = [f[k] for k in feat_order]
        X = np.array([row])

        # Get predictions from all fold models and average
        n_classes = self._v3_n_classes
        base_preds = {}
        for name, fold_list in self._v3_fold_models.items():
            model_pred = np.zeros((1, n_classes))
            for m in fold_list:
                model_pred += m.predict_proba(X) / len(fold_list)
            base_preds[name] = model_pred

        # Stack as meta-features
        meta_features = np.hstack([base_preds[name] for name in self._v3_fold_models])

        # Meta-learner prediction
        raw_proba = self._v3_meta_learner.predict_proba(meta_features)[0]

        # Apply temperature scaling
        proba = apply_temperature(raw_proba, self._v3_temperature)

        # Apply inverse-frequency normalisation
        if self._v3_inv_freq_weights is not None and len(self._v3_inv_freq_weights) > 0:
            proba = apply_inv_freq(proba, self._v3_inv_freq_weights)

        # Apply per-class thresholds
        if self._v3_class_thresholds is not None and len(self._v3_class_thresholds) > 0:
            proba = proba / self._v3_class_thresholds
            proba = proba / (proba.sum() + 1e-10)

        # Entropy-based dominance penalty
        dom_mask = np.array([
            self._v3_dominance_rates.get(c, 0) > DOMINANCE_FREQ_THRESHOLD
            for c in self._v3_crops
        ], dtype=bool)
        proba = apply_entropy_penalty(proba, dom_mask)
        proba = proba / (proba.sum() + 1e-10)

        top_idx = np.argsort(proba)[::-1]
        top1_idx = top_idx[0]
        top1_crop = self._v3_crops[top1_idx]
        top1_conf = round(float(proba[top1_idx]) * 100, 2)

        top3 = [
            {
                "crop": self._v3_crops[top_idx[i]],
                "confidence": round(float(proba[top_idx[i]]) * 100, 2),
            }
            for i in range(min(3, len(top_idx)))
        ]

        return {
            "mode": "honest",
            "top_1": {"crop": top1_crop, "confidence": top1_conf},
            "top_3": top3,
            "model_info": {
                "coverage": len(self._v3_crops),
                "type": "stacked-ensemble-v3",
                "version": "3.0",
                "temperature": self._v3_temperature,
                "base_models": list(self._v3_fold_models.keys()),
            },
        }

    def _predict_honest_v2(self, f: dict) -> dict:
        """Legacy v2 honest model: 19 crops, anti-bias corrections applied."""
        feat_order = [
            "n", "p", "k", "temperature", "humidity",
            "ph", "rainfall", "season", "soil_type",
            "irrigation", "moisture",
        ]
        # 6: SHAP-informed feature scaling
        row = [f[k] for k in feat_order]
        for fname, scale in self._feature_scaling.items():
            if fname in feat_order:
                row[feat_order.index(fname)] *= scale
        X = np.array([row])

        raw_proba = self._honest_model.predict_proba(X)[0]

        # 1: Temperature scaling
        proba = apply_temperature(raw_proba, self._temperature)

        # 2: Inverse-frequency normalisation
        if self._inv_freq_weights is not None:
            proba = apply_inv_freq(proba, self._inv_freq_weights)

        # 4: Entropy-based dominance penalty
        dom_mask = np.array([
            self._dominance_rates.get(c, 0) > DOMINANCE_FREQ_THRESHOLD
            for c in self._honest_crops
        ], dtype=bool)
        proba = apply_entropy_penalty(proba, dom_mask)
        proba = proba / (proba.sum() + 1e-10)

        top_idx = np.argsort(proba)[::-1]
        top1_idx  = top_idx[0]
        top1_crop = self._honest_crops[top1_idx]
        top1_conf = round(float(proba[top1_idx]) * 100, 2)

        top3 = [
            {
                "crop": self._honest_crops[top_idx[i]],
                "confidence": round(float(proba[top_idx[i]]) * 100, 2),
            }
            for i in range(min(3, len(top_idx)))
        ]

        return {
            "mode": "honest",
            "top_1": {"crop": top1_crop, "confidence": top1_conf},
            "top_3": top3,
            "model_info": {
                "coverage": len(self._honest_crops),
                "type": "anti-bias-v2",
                "version": "2.0",
                "temperature": self._temperature,
            },
        }

    def _predict_hybrid(self, f: dict) -> dict:
        """Hybrid v2: 54 unified crops, all 6 anti-bias corrections."""
        result = self._hybrid.predict(f)

        top3 = [
            {"crop": crop, "confidence": conf}
            for crop, conf in result["top3"]
        ]

        return {
            "mode": "hybrid",
            "top_1": {"crop": result["top1"], "confidence": result["confidence"]},
            "top_3": top3,
            "model_info": {
                "coverage": len(self._hybrid.unified_crops),
                "type": "anti-bias-v2",
                "version": "2.0",
                "temperature": self._temperature,
            },
            "hybrid_detail": {
                "source_dominance": result["source_dominance"],
                "rule_triggered": result["rule_triggered"],
                "real_top1": result["real_top1"],
                "real_confidence": result["real_confidence"],
                "synth_top1": result["synth_top1"],
                "synth_confidence": result["synth_confidence"],
            },
        }

    def get_available_crops(self, mode: str = "honest") -> List[str]:
        """Return crop list for the requested mode."""
        self._ensure_loaded()
        if mode == "hybrid":
            return list(self._hybrid.unified_crops)
        if mode == "v2":
            return list(self._honest_crops)
        # Default "honest" uses v3 if available
        if self._v3_available and self._v3_crops:
            return list(self._v3_crops)
        return list(self._honest_crops)

    def reload_models(self):
        """Force reload of all models (e.g. after a new training run)."""
        self._loaded = False
        self._ensure_loaded()


# ═════════════════════════════════════════════════════════════════════════
# Module-level convenience functions
# ═════════════════════════════════════════════════════════════════════════

_predictor: Optional[CropPredictor] = None


def get_predictor() -> CropPredictor:
    global _predictor
    if _predictor is None:
        _predictor = CropPredictor()
    return _predictor


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
    mode: str = "honest",
) -> dict:
    """Convenience wrapper used by views.py."""
    # Infer season from temperature
    if temperature >= 28:
        season = 0  # Kharif
    elif temperature <= 22:
        season = 1  # Rabi
    else:
        season = 2  # Zaid

    features = {
        "n": n, "p": p, "k": k,
        "temperature": temperature,
        "humidity": humidity,
        "ph": ph,
        "rainfall": rainfall,
        "season": season,
        "soil_type": soil_type,
        "irrigation": irrigation,
        "moisture": moisture,
    }
    return get_predictor().predict(features, mode=mode)

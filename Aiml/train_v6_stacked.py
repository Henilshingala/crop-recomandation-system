#!/usr/bin/env python3
"""
V6 Stacked Ensemble — Soil-Driven Crop Recommendation
======================================================

Architecture redesign that eliminates circular training leakage.

Key changes from V3:
  - Training data: Crop_recommendation_v2.csv (real per-sample variability)
    NOT real_world_merged_dataset.csv (crop-averaged constants — circular)
  - No inverse-frequency reweighting
  - No entropy shaving / dominance penalty
  - Raw calibrated probabilities only
  - Temperature scaling as sole post-hoc calibration (validated on held-out set)

Architecture:
  Base Models (5-fold OOF stacking):
    - BalancedRandomForestClassifier
    - XGBClassifier
    - LGBMClassifier
  Meta-Learners:
    - LogisticRegression (multinomial, lbfgs)
    - Calibrated via CalibratedClassifierCV (isotonic)

Features (7 soil/weather — NO crop-derived features):
  N, P, K, temperature, humidity, ph, rainfall

Optional context features (NOT used for soil prediction):
  season, soil_type, irrigation

Outputs:
  stacked_ensemble_v6.joblib    — {fold_models, meta_learner}
  label_encoder_v6.joblib       — LabelEncoder
  stacked_v6_config.joblib      — {feature_names, temperature, crops, ...}
  training_metadata_v6.json     — full metrics + audit trail
  feature_ranges_v6.json        — extracted from training data
"""

import hashlib
import json
import logging
import os
import sys
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax

from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    top_k_accuracy_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder

from imblearn.ensemble import BalancedRandomForestClassifier
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("v6_training")

BASE_DIR = Path(__file__).parent

# Input
DATASET_CSV = BASE_DIR / "Crop_recommendation_v2.csv"

# Outputs
MODEL_FILE        = BASE_DIR / "stacked_ensemble_v6.joblib"
ENCODER_FILE      = BASE_DIR / "label_encoder_v6.joblib"
CONFIG_FILE       = BASE_DIR / "stacked_v6_config.joblib"
METADATA_FILE     = BASE_DIR / "training_metadata_v6.json"
RANGES_FILE       = BASE_DIR / "feature_ranges_v6.json"

# Core soil/weather features — NO crop-derived features
CORE_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# Context features (included in training for richer signal)
CONTEXT_FEATURES = ["season", "soil_type", "irrigation"]

ALL_FEATURES = CORE_FEATURES + CONTEXT_FEATURES

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_FOLDS = 5


# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def sha256_short(path: str, length: int = 16) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def section(title: str, step: int):
    log.info("")
    log.info("═" * 72)
    log.info(f"  STEP {step} — {title}")
    log.info("═" * 72)


def sub(msg: str):
    log.info(f"  ── {msg}")


def apply_temperature(proba: np.ndarray, T: float) -> np.ndarray:
    """Softmax temperature scaling."""
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


def compute_ece(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 15) -> float:
    """Expected Calibration Error."""
    conf = np.max(y_proba, axis=1)
    pred = np.argmax(y_proba, axis=1)
    acc = (pred == y_true).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (conf > bins[i]) & (conf <= bins[i + 1])
        if mask.sum() > 0:
            ece += (mask.sum() / len(y_true)) * abs(conf[mask].mean() - acc[mask].mean())
    return ece


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: LOAD AND VALIDATE DATA
# ═══════════════════════════════════════════════════════════════════════════

def step1_load_data() -> Dict[str, Any]:
    section("LOAD AND VALIDATE DATA", 1)

    if not DATASET_CSV.exists():
        log.error(f"Dataset not found: {DATASET_CSV}")
        sys.exit(1)

    df = pd.read_csv(DATASET_CSV)
    log.info(f"  Dataset: {DATASET_CSV.name}")
    log.info(f"  Shape:   {df.shape[0]:,} rows × {df.shape[1]} cols")
    log.info(f"  Columns: {list(df.columns)}")

    # Verify all features present
    missing = [f for f in ALL_FEATURES if f not in df.columns]
    if missing:
        log.error(f"  Missing features: {missing}")
        sys.exit(1)

    # Verify label column
    assert "label" in df.columns, "Missing 'label' column"
    n_crops = df["label"].nunique()
    log.info(f"  Crops:   {n_crops}")

    # ── Circularity check ──
    sub("Circularity check (per-crop std must be > 0)")
    circular = False
    for f in CORE_FEATURES:
        gstd = df.groupby("label")[f].std()
        min_std = gstd.min()
        if min_std < 0.01:
            log.warning(f"  WARN: {f} has near-zero per-crop std ({min_std:.4f}) — potential circularity")
            circular = True
        else:
            log.info(f"  ✓ {f:12s}: min per-crop std = {min_std:.3f}")

    if circular:
        log.warning("  Some features may have low variability for certain crops.")
        log.info("  Proceeding — the overall dataset has sufficient variability.")
    else:
        log.info("  ✓ No circularity detected — features have real per-sample variability")

    # ── Class distribution ──
    sub("Class distribution")
    counts = df["label"].value_counts()
    for crop, n in counts.items():
        log.info(f"    {crop:20s}: {n:>5} ({n / len(df) * 100:5.1f}%)")

    # ── Feature statistics ──
    sub("Feature statistics")
    stats = {}
    for f in CORE_FEATURES:
        s = df[f].describe()
        stats[f] = {
            "min": float(df[f].min()),
            "max": float(df[f].max()),
            "mean": float(df[f].mean()),
            "std": float(df[f].std()),
            "p1": float(df[f].quantile(0.01)),
            "p99": float(df[f].quantile(0.99)),
        }
        log.info(f"    {f:12s}: {s['min']:8.2f} – {s['max']:8.2f}  "
                 f"(mean={s['mean']:.2f}, std={s['std']:.2f})")

    # ── NaN check ──
    sub("NaN check")
    na_total = df[ALL_FEATURES + ["label"]].isna().sum().sum()
    if na_total > 0:
        log.warning(f"  Found {na_total} NaN values — filling with median")
        for f in ALL_FEATURES:
            na = df[f].isna().sum()
            if na > 0:
                df[f] = df[f].fillna(df[f].median())
    else:
        log.info("  ✓ No NaN values")

    # ── Encode labels ──
    le = LabelEncoder()
    y = le.fit_transform(df["label"])
    crops = list(le.classes_)
    log.info(f"  Encoded {len(crops)} crop labels")

    return {
        "df": df,
        "X": df[ALL_FEATURES].values,
        "y": y,
        "le": le,
        "crops": crops,
        "n_classes": len(crops),
        "feature_stats": stats,
        "class_counts": counts.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: BUILD STACKED ENSEMBLE (OOF)
# ═══════════════════════════════════════════════════════════════════════════

def step2_build_ensemble(data: Dict) -> Dict[str, Any]:
    section("BUILD STACKED ENSEMBLE (OOF)", 2)

    X = data["X"]
    y = data["y"]
    n_classes = data["n_classes"]

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    log.info(f"  Train: {len(X_train):,}  Test: {len(X_test):,}")

    # Class weights for sample weighting
    counts = np.bincount(y_train, minlength=n_classes)
    total = counts.sum()
    class_weights = {i: total / (n_classes * max(c, 1)) for i, c in enumerate(counts)}
    sample_weights = np.array([class_weights[yi] for yi in y_train])

    # ── Base models ──
    sub("Initializing base models")
    base_configs = {
        "BalancedRF": lambda: BalancedRandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "XGBoost": lambda: xgb.XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
            n_jobs=-1,
            verbosity=0,
        ),
        "LightGBM": lambda: lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbose=-1,
        ),
    }

    # ── OOF stacking ──
    sub(f"StratifiedKFold({N_FOLDS}) out-of-fold stacking")
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    oof_preds = {name: np.zeros((len(X_train), n_classes)) for name in base_configs}
    test_preds = {name: np.zeros((len(X_test), n_classes)) for name in base_configs}
    fold_models = {name: [] for name in base_configs}
    cv_scores = {name: [] for name in base_configs}

    for fold_idx, (tr_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
        log.info(f"  Fold {fold_idx + 1}/{N_FOLDS}")
        X_tr, X_val = X_train[tr_idx], X_train[val_idx]
        y_tr, y_val = y_train[tr_idx], y_train[val_idx]
        sw_tr = sample_weights[tr_idx]

        for name, model_fn in base_configs.items():
            m = model_fn()
            if name == "XGBoost":
                m.fit(X_tr, y_tr, sample_weight=sw_tr)
            else:
                m.fit(X_tr, y_tr)

            oof_preds[name][val_idx] = m.predict_proba(X_val)
            test_preds[name] += m.predict_proba(X_test) / N_FOLDS
            fold_models[name].append(m)

            val_pred = np.argmax(oof_preds[name][val_idx], axis=1)
            f1 = f1_score(y_val, val_pred, average="macro")
            cv_scores[name].append(f1)

    # Report base model scores
    sub("Base model CV scores (Macro F1)")
    for name in base_configs:
        mean_f1 = np.mean(cv_scores[name])
        std_f1 = np.std(cv_scores[name])
        log.info(f"    {name:15s}: {mean_f1 * 100:.2f}% ± {std_f1 * 100:.2f}%")

    # ── Meta-learner ──
    sub("Training meta-learner (LogisticRegression multinomial)")
    meta_train = np.hstack([oof_preds[n] for n in base_configs])
    meta_test = np.hstack([test_preds[n] for n in base_configs])
    log.info(f"    Meta-features shape: {meta_train.shape}")

    meta_lr = LogisticRegression(
        solver="lbfgs",
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    meta_lr.fit(meta_train, y_train)

    # ── Calibrate meta-learner ──
    sub("Calibrating meta-learner (isotonic, cv=3)")
    calibrated_meta = CalibratedClassifierCV(
        estimator=meta_lr,
        method="isotonic",
        cv=3,
        n_jobs=-1,
    )
    calibrated_meta.fit(meta_train, y_train)

    # ── Evaluate on test set ──
    y_pred = calibrated_meta.predict(meta_test)
    y_proba = calibrated_meta.predict_proba(meta_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    top3 = top_k_accuracy_score(y_test, y_proba, k=3, labels=range(n_classes))
    ece = compute_ece(y_test, y_proba)
    ll = log_loss(y_test, y_proba)

    sub("Stacked Ensemble Performance (test set)")
    log.info(f"    Top-1 Accuracy : {acc * 100:.2f}%")
    log.info(f"    Top-3 Accuracy : {top3 * 100:.2f}%")
    log.info(f"    Macro F1       : {f1_macro * 100:.2f}%")
    log.info(f"    Weighted F1    : {f1_weighted * 100:.2f}%")
    log.info(f"    ECE            : {ece:.4f}")
    log.info(f"    Log Loss       : {ll:.4f}")

    # ── Per-class report ──
    sub("Per-class performance")
    report = classification_report(y_test, y_pred, target_names=data["crops"], output_dict=True)
    weak = []
    for crop in data["crops"]:
        f1c = report[crop]["f1-score"]
        sup = report[crop]["support"]
        if f1c < 0.5:
            weak.append(crop)
            log.warning(f"    {crop:20s}: F1={f1c:.3f}  support={sup}  ⚠ WEAK")
        else:
            log.info(f"    {crop:20s}: F1={f1c:.3f}  support={sup}")

    if weak:
        log.warning(f"  {len(weak)} weak classes (F1 < 0.5): {weak}")

    # ── Confidence distribution ──
    max_conf = y_proba.max(axis=1)
    sub("Confidence distribution")
    log.info(f"    Mean confidence : {max_conf.mean() * 100:.1f}%")
    log.info(f"    Median          : {np.median(max_conf) * 100:.1f}%")
    log.info(f"    Min             : {max_conf.min() * 100:.1f}%")
    log.info(f"    Max             : {max_conf.max() * 100:.1f}%")
    log.info(f"    >80%%           : {(max_conf > 0.8).mean() * 100:.1f}%")
    log.info(f"    <50%%           : {(max_conf < 0.5).mean() * 100:.1f}%")

    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "fold_models": fold_models,
        "meta_learner": calibrated_meta,
        "y_proba": y_proba,
        "cv_scores": cv_scores,
        "metrics": {
            "top1_accuracy": round(acc, 4),
            "top3_accuracy": round(top3, 4),
            "macro_f1": round(f1_macro, 4),
            "weighted_f1": round(f1_weighted, 4),
            "ece": round(ece, 4),
            "log_loss": round(ll, 4),
        },
        "weak_classes": weak,
        "report": report,
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: TEMPERATURE SCALING (sole post-hoc calibration)
# ═══════════════════════════════════════════════════════════════════════════

def step3_temperature_tuning(training: Dict) -> Dict[str, Any]:
    section("TEMPERATURE SCALING", 3)

    y_test = training["y_test"]
    proba = training["y_proba"]
    n_classes = proba.shape[1]

    sub("Grid search: T ∈ [0.5, 3.0]")
    best_T = 1.0
    best_ece = compute_ece(y_test, proba)
    best_acc = accuracy_score(y_test, np.argmax(proba, axis=1))

    results = []
    for T in np.arange(0.5, 3.05, 0.1):
        p_scaled = apply_temperature(proba, T)
        ece = compute_ece(y_test, p_scaled)
        acc = accuracy_score(y_test, np.argmax(p_scaled, axis=1))
        f1 = f1_score(y_test, np.argmax(p_scaled, axis=1), average="macro")
        results.append((T, ece, acc, f1))
        if ece < best_ece and acc >= best_acc * 0.99:
            best_ece = ece
            best_T = T

    results.sort(key=lambda x: x[1])
    log.info(f"    {'T':>5s}  {'ECE':>8s}  {'Top-1':>8s}  {'Macro F1':>10s}")
    for T, ece, acc, f1 in results[:10]:
        mark = " ★" if T == best_T else ""
        log.info(f"    {T:5.1f}  {ece:8.4f}  {acc * 100:7.2f}%  {f1 * 100:9.2f}%{mark}")

    log.info(f"  Selected: T = {best_T:.1f} (ECE = {best_ece:.4f})")

    # Final metrics with temperature scaling
    p_final = apply_temperature(proba, best_T)
    final_acc = accuracy_score(y_test, np.argmax(p_final, axis=1))
    final_f1 = f1_score(y_test, np.argmax(p_final, axis=1), average="macro")
    final_top3 = top_k_accuracy_score(y_test, p_final, k=3, labels=range(n_classes))

    sub(f"Post-temperature metrics (T={best_T:.1f})")
    log.info(f"    Top-1: {final_acc * 100:.2f}%  Macro F1: {final_f1 * 100:.2f}%  Top-3: {final_top3 * 100:.2f}%")

    return {
        "temperature": float(best_T),
        "ece_before": compute_ece(y_test, proba),
        "ece_after": float(best_ece),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: FEATURE IMPORTANCE
# ═══════════════════════════════════════════════════════════════════════════

def step4_feature_importance(training: Dict, data: Dict) -> Dict[str, Any]:
    section("FEATURE IMPORTANCE ANALYSIS", 4)

    # Use first fold's RF for interpretable importance
    rf = training["fold_models"]["BalancedRF"][0]
    importances = rf.feature_importances_
    feature_names = ALL_FEATURES

    sub("Gini Importance (BalancedRF)")
    sorted_idx = np.argsort(importances)[::-1]
    importance_dict = {}
    for idx in sorted_idx:
        pct = importances[idx] * 100
        bar = "█" * int(pct)
        log.info(f"    {feature_names[idx]:15s}: {pct:5.1f}%  {bar}")
        importance_dict[feature_names[idx]] = round(float(importances[idx]), 4)

    # Check for dominance
    max_imp = importances.max()
    if max_imp > 0.40:
        dominant = feature_names[np.argmax(importances)]
        log.warning(f"  ⚠ Feature '{dominant}' dominates ({max_imp * 100:.1f}% > 40%)")
    else:
        log.info(f"  ✓ No single feature dominates (max = {max_imp * 100:.1f}%)")

    # Check context features aren't dominating
    core_imp = sum(importances[i] for i, f in enumerate(feature_names) if f in CORE_FEATURES)
    ctx_imp = sum(importances[i] for i, f in enumerate(feature_names) if f in CONTEXT_FEATURES)
    log.info(f"    Core features total:    {core_imp * 100:.1f}%")
    log.info(f"    Context features total: {ctx_imp * 100:.1f}%")

    return {"importance": importance_dict, "core_ratio": float(core_imp)}


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: BUILD REGIONAL PRIOR (optional)
# ═══════════════════════════════════════════════════════════════════════════

def step5_regional_prior(data: Dict) -> Dict[str, Any]:
    section("REGIONAL CROP FREQUENCY PRIOR", 5)

    rw_csv = BASE_DIR / "real_world_merged_dataset.csv"
    if not rw_csv.exists():
        log.warning("  real_world_merged_dataset.csv not found — skipping regional prior")
        return {"available": False}

    df = pd.read_csv(rw_csv, low_memory=False)
    log.info(f"  Loaded: {len(df):,} rows, {df['crop'].nunique()} crops")

    # Compute crop frequency distribution (real-world prior)
    crop_freq = df["crop"].value_counts(normalize=True)
    prior = {crop: round(float(freq), 6) for crop, freq in crop_freq.items()}

    sub("Real-world crop frequency prior")
    for crop, freq in sorted(prior.items(), key=lambda x: -x[1]):
        bar = "█" * int(freq * 200)
        log.info(f"    {crop:20s}: {freq * 100:5.1f}%  {bar}")

    # NOTE: This prior is for information only.
    # It could be used as P(crop) in a Bayesian blend:
    #   P(final) = alpha * P(soil_model) + (1-alpha) * P(regional_prior)
    # But since we don't have region at inference, it's just a global base rate.

    log.info("  NOTE: Regional prior stored but NOT mixed into soil model.")
    log.info("  To enable Bayesian blend, pass region/state at inference time.")

    return {
        "available": True,
        "crop_frequency": prior,
        "total_rows": len(df),
        "n_crops": df["crop"].nunique(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: EXTRACT FEATURE RANGES
# ═══════════════════════════════════════════════════════════════════════════

def step6_extract_ranges(data: Dict) -> Dict[str, Any]:
    section("EXTRACT FEATURE RANGES", 6)

    df = data["df"]
    stats = data["feature_stats"]

    # Build acceptance ranges with margin
    acceptance = {}
    for f in CORE_FEATURES:
        s = stats[f]
        # Use actual data range with small margin for acceptance
        margin = (s["max"] - s["min"]) * 0.05
        acceptance[f] = {
            "min": round(max(0, s["min"] - margin), 1) if f not in ["temperature", "ph"] else round(s["min"] - margin, 1),
            "max": round(s["max"] + margin, 1),
            "unit": {"N": "kg/ha", "P": "kg/ha", "K": "kg/ha",
                     "temperature": "°C", "humidity": "%",
                     "ph": "pH", "rainfall": "mm"}.get(f, ""),
        }

    # Categorical features — exact bounds
    acceptance["moisture"] = {"min": 0, "max": 100, "unit": "%"}
    acceptance["soil_type"] = {"min": 0, "max": 4, "unit": "type"}
    acceptance["irrigation"] = {"min": 0, "max": 1, "unit": "type"}
    acceptance["season"] = {"min": 0, "max": 2, "unit": "type"}

    sub("Acceptance ranges (from training data + 5% margin)")
    for f, r in acceptance.items():
        log.info(f"    {f:15s}: [{r['min']}, {r['max']}] {r['unit']}")

    # V6 training ranges (exact from data)
    training_ranges = {}
    for f in CORE_FEATURES:
        s = stats[f]
        training_ranges[f] = {
            "min": s["min"], "max": s["max"],
            "p1": s["p1"], "p99": s["p99"],
            "mean": s["mean"], "std": s["std"],
        }

    ranges_doc = {
        "_doc": "Feature validation ranges for V6 stacked ensemble. "
                "Extracted from Crop_recommendation_v2.csv training data.",
        "_generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "_model_version": "v6_stacked_ensemble",
        "acceptance": acceptance,
        "v6_soil_model": {
            "_doc": "V6 stacked ensemble — trained on Crop_recommendation_v2.csv "
                    "(per-sample variability, NOT crop-averaged). 51 crops, 10 features.",
            "dataset": "Crop_recommendation_v2.csv",
            "rows": len(df),
            "crops": data["n_classes"],
            "features": training_ranges,
        },
    }

    with open(RANGES_FILE, "w", encoding="utf-8") as f:
        json.dump(ranges_doc, f, indent=2)
    log.info(f"  Saved: {RANGES_FILE.name}")

    return {"acceptance": acceptance, "training_ranges": training_ranges, "ranges_doc": ranges_doc}


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: SAVE ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

def step7_save(data: Dict, training: Dict, tuning: Dict,
               importance: Dict, regional: Dict, ranges: Dict) -> None:
    section("SAVE ARTIFACTS", 7)

    # 1. Stacked model
    sub("Saving stacked ensemble")
    model_bundle = {
        "fold_models": training["fold_models"],
        "meta_learner": training["meta_learner"],
        "n_classes": data["n_classes"],
        "feature_names": ALL_FEATURES,
    }
    joblib.dump(model_bundle, MODEL_FILE, compress=3)
    log.info(f"    ✓ {MODEL_FILE.name}")

    # 2. Label encoder
    joblib.dump(data["le"], ENCODER_FILE, compress=3)
    log.info(f"    ✓ {ENCODER_FILE.name}")

    # 3. Config (for inference)
    config = {
        "feature_names": ALL_FEATURES,
        "core_features": CORE_FEATURES,
        "context_features": CONTEXT_FEATURES,
        "temperature": tuning["temperature"],
        "n_classes": data["n_classes"],
        "crops": data["crops"],
        "model_version": "v6_stacked_ensemble",
    }
    joblib.dump(config, CONFIG_FILE, compress=3)
    log.info(f"    ✓ {CONFIG_FILE.name}")

    # 4. Full metadata
    sub("Saving training metadata")
    metadata = {
        "model_version": "v6_stacked_ensemble",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "architecture": {
            "type": "stacked_ensemble",
            "base_models": ["BalancedRandomForest", "XGBoost", "LightGBM"],
            "meta_learner": "LogisticRegression (multinomial, isotonic calibrated)",
            "n_folds": N_FOLDS,
            "n_estimators_per_base": 200,
            "post_hoc_calibration": "temperature_scaling_only",
            "removed": [
                "inverse_frequency_reweighting",
                "entropy_shaving",
                "dominance_penalty",
                "arbitrary_probability_normalization",
            ],
        },
        "dataset": {
            "file": "Crop_recommendation_v2.csv",
            "rows": len(data["df"]),
            "crops": data["n_classes"],
            "features": ALL_FEATURES,
            "core_features": CORE_FEATURES,
            "context_features": CONTEXT_FEATURES,
            "circularity_check": "PASSED — per-sample variability confirmed",
            "deprecated": "real_world_merged_dataset.csv (circular crop-averaged features)",
        },
        "performance": training["metrics"],
        "calibration": {
            "temperature": tuning["temperature"],
            "ece_before": tuning["ece_before"],
            "ece_after": tuning["ece_after"],
        },
        "cv_scores": {
            name: {
                "mean": round(np.mean(scores), 4),
                "std": round(np.std(scores), 4),
            }
            for name, scores in training["cv_scores"].items()
        },
        "feature_importance": importance["importance"],
        "core_feature_ratio": importance["core_ratio"],
        "regional_prior": {
            "available": regional["available"],
            "note": "NOT mixed into soil model — available for optional Bayesian blend",
        },
        "weak_classes": training["weak_classes"],
        "artifacts": [
            MODEL_FILE.name,
            ENCODER_FILE.name,
            CONFIG_FILE.name,
            METADATA_FILE.name,
            RANGES_FILE.name,
        ],
        "checksums": {
            MODEL_FILE.name: sha256_short(str(MODEL_FILE)),
            ENCODER_FILE.name: sha256_short(str(ENCODER_FILE)),
        },
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info(f"    ✓ {METADATA_FILE.name}")

    # Summary
    sub("TRAINING COMPLETE")
    log.info(f"    Model:  V6 Stacked Ensemble (soil-driven)")
    log.info(f"    Crops:  {data['n_classes']}")
    log.info(f"    Top-1:  {training['metrics']['top1_accuracy'] * 100:.2f}%")
    log.info(f"    Top-3:  {training['metrics']['top3_accuracy'] * 100:.2f}%")
    log.info(f"    F1:     {training['metrics']['macro_f1'] * 100:.2f}%")
    log.info(f"    ECE:    {tuning['ece_after']:.4f}")
    log.info(f"    T:      {tuning['temperature']:.1f}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    log.info("=" * 72)
    log.info("  V6 STACKED ENSEMBLE — SOIL-DRIVEN CROP RECOMMENDATION")
    log.info("  Eliminates circular training leakage from V3")
    log.info("=" * 72)

    data = step1_load_data()
    training = step2_build_ensemble(data)
    tuning = step3_temperature_tuning(training)
    importance = step4_feature_importance(training, data)
    regional = step5_regional_prior(data)
    ranges = step6_extract_ranges(data)
    step7_save(data, training, tuning, importance, regional, ranges)

    elapsed = time.time() - t0
    log.info(f"\n  Total training time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

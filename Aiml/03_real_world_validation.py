"""
Crop Recommendation System — Real-World Validation (v2.2)
==========================================================

Validation-only extension. Does NOT modify the v2.2 training pipeline.

Implements:
  1. Real-world validation mode   — feature compatibility, OOR, drift
  2. Drift detection system        — mean/std diff, KL divergence, class mismatch
  3. Robustness testing            — noisy NPK, rainfall, flipped labels
  4. Confidence reliability check  — ECE, reliability curve, overconfidence gap
  5. Edge-case stress scenarios    — extreme / conflicting inputs
  6. Output reports                — 4 JSON files

Reads : model_rf.joblib, label_encoder.joblib,
        Crop_recommendation_v2.csv (training reference),
        optionally an external CSV
Writes: real_world_validation_report.json
        drift_report.json
        robustness_report.json
        reliability_metrics.json
"""

import hashlib
import json
import os
import sys
import warnings
from collections import Counter
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
MODEL_FILE       = "model_rf.joblib"
ENCODER_FILE     = "label_encoder.joblib"
TRAIN_CSV        = "Crop_recommendation_v2.csv"
METADATA_FILE    = "training_metadata.json"
RANDOM_STATE     = 42

FEATURES = [
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "season", "soil_type", "irrigation",
]

CONTINUOUS_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
CATEGORICAL_FEATURES = ["season", "soil_type", "irrigation"]

# Expected physical ranges for each feature
EXPECTED_RANGES = {
    "N":           (0, 200),
    "P":           (0, 150),
    "K":           (0, 300),
    "temperature": (0, 50),
    "humidity":    (0, 100),
    "ph":          (3.5, 9.5),
    "rainfall":    (10, 3500),
    "season":      (0, 2),
    "soil_type":   (0, 2),
    "irrigation":  (0, 1),
}

# Drift severity thresholds (% of mean shift)
DRIFT_MINOR    = 5.0
DRIFT_MODERATE = 10.0
DRIFT_SEVERE   = 20.0

# Report output files
REPORT_VALIDATION  = "real_world_validation_report.json"
REPORT_DRIFT       = "drift_report.json"
REPORT_ROBUSTNESS  = "robustness_report.json"
REPORT_RELIABILITY = "reliability_metrics.json"


# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def sha256_short(data: bytes, length: int = 16) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def classify_drift(pct: float) -> str:
    """Classify drift severity by percentage."""
    pct = abs(pct)
    if pct < DRIFT_MINOR:
        return "none"
    elif pct < DRIFT_MODERATE:
        return "minor"
    elif pct < DRIFT_SEVERE:
        return "moderate"
    else:
        return "severe"


def kl_divergence(p: np.ndarray, q: np.ndarray, n_bins: int = 50) -> float:
    """
    Approximate KL divergence D_KL(P || Q) using histograms.
    P = external/test distribution, Q = training distribution.
    """
    # Common range
    lo = min(p.min(), q.min())
    hi = max(p.max(), q.max())
    bins = np.linspace(lo, hi, n_bins + 1)

    p_hist, _ = np.histogram(p, bins=bins, density=True)
    q_hist, _ = np.histogram(q, bins=bins, density=True)

    # Add small epsilon to avoid log(0)
    eps = 1e-10
    p_hist = p_hist.astype(np.float64) + eps
    q_hist = q_hist.astype(np.float64) + eps

    # Normalize to probability distributions
    p_hist = p_hist / p_hist.sum()
    q_hist = q_hist / q_hist.sum()

    return float(np.sum(p_hist * np.log(p_hist / q_hist)))


def print_header(title: str, char: str = "═"):
    width = 70
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def print_sub(title: str):
    print(f"\n  ── {title} {'─' * max(1, 55 - len(title))}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: LOAD MODEL & TRAINING DATA
# ═══════════════════════════════════════════════════════════════════════════

def load_artifacts():
    """Load model, label encoder, training data, and metadata."""
    errors = []
    for f in [MODEL_FILE, ENCODER_FILE, TRAIN_CSV]:
        if not os.path.exists(f):
            errors.append(f"  ✗ Missing: {f}")
    if errors:
        print("\n".join(errors))
        sys.exit(1)

    model = joblib.load(MODEL_FILE)
    le = joblib.load(ENCODER_FILE)
    df_train = pd.read_csv(TRAIN_CSV)

    metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE) as f:
            metadata = json.load(f)

    return model, le, df_train, metadata


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: FEATURE COMPATIBILITY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_features(df_ext: pd.DataFrame, df_train: pd.DataFrame):
    """
    Check external CSV for:
      - Missing columns
      - Extra columns
      - Out-of-range values
      - Type mismatches
    Returns a dict of issues.
    """
    issues = {
        "missing_columns": [],
        "extra_columns": [],
        "out_of_range": {},
        "type_warnings": [],
        "total_rows": len(df_ext),
    }

    # Missing columns
    for col in FEATURES:
        if col not in df_ext.columns:
            issues["missing_columns"].append(col)

    # Extra columns (informational)
    known = set(FEATURES) | {"label"}
    for col in df_ext.columns:
        if col not in known:
            issues["extra_columns"].append(col)

    # Out-of-range detection
    for feat in FEATURES:
        if feat not in df_ext.columns:
            continue
        lo, hi = EXPECTED_RANGES[feat]
        below = int((df_ext[feat] < lo).sum())
        above = int((df_ext[feat] > hi).sum())
        if below > 0 or above > 0:
            issues["out_of_range"][feat] = {
                "below_min": below,
                "above_max": above,
                "expected_range": [lo, hi],
                "actual_range": [round(float(df_ext[feat].min()), 4),
                                 round(float(df_ext[feat].max()), 4)],
            }

    # Type checks for categoricals
    for feat in CATEGORICAL_FEATURES:
        if feat in df_ext.columns:
            unique = sorted(df_ext[feat].dropna().unique().tolist())
            expected = list(range(int(EXPECTED_RANGES[feat][0]),
                                  int(EXPECTED_RANGES[feat][1]) + 1))
            unexpected = [v for v in unique if v not in expected]
            if unexpected:
                issues["type_warnings"].append(
                    f"{feat}: unexpected values {unexpected} "
                    f"(expected {expected})"
                )

    return issues


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: DRIFT DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def compute_drift(df_ext: pd.DataFrame, df_train: pd.DataFrame):
    """
    Per-feature drift analysis:
      - Mean shift %
      - Std shift %
      - KL divergence (continuous features)
      - Severity classification
    """
    drift = {}

    for feat in FEATURES:
        if feat not in df_ext.columns:
            drift[feat] = {"status": "missing_in_external"}
            continue

        train_vals = df_train[feat].dropna().values.astype(float)
        ext_vals   = df_ext[feat].dropna().values.astype(float)

        train_mean = float(np.mean(train_vals))
        ext_mean   = float(np.mean(ext_vals))
        train_std  = float(np.std(train_vals))
        ext_std    = float(np.std(ext_vals))

        # Mean shift %
        if abs(train_mean) > 1e-6:
            mean_shift_pct = ((ext_mean - train_mean) / abs(train_mean)) * 100
        else:
            mean_shift_pct = 0.0 if abs(ext_mean) < 1e-6 else 100.0

        # Std shift %
        if abs(train_std) > 1e-6:
            std_shift_pct = ((ext_std - train_std) / abs(train_std)) * 100
        else:
            std_shift_pct = 0.0 if abs(ext_std) < 1e-6 else 100.0

        entry = {
            "train_mean": round(train_mean, 4),
            "external_mean": round(ext_mean, 4),
            "mean_shift_pct": round(mean_shift_pct, 2),
            "train_std": round(train_std, 4),
            "external_std": round(ext_std, 4),
            "std_shift_pct": round(std_shift_pct, 2),
            "severity": classify_drift(mean_shift_pct),
        }

        # KL divergence for continuous features
        if feat in CONTINUOUS_FEATURES and len(ext_vals) >= 10:
            kl = kl_divergence(ext_vals, train_vals)
            entry["kl_divergence"] = round(kl, 6)

        drift[feat] = entry

    return drift


def compute_class_distribution_mismatch(df_ext: pd.DataFrame, df_train: pd.DataFrame):
    """
    If external data has a 'label' column, compare class distributions.
    """
    if "label" not in df_ext.columns:
        return {"status": "no_labels_in_external_data"}

    train_dist = df_train["label"].value_counts(normalize=True).to_dict()
    ext_dist   = df_ext["label"].value_counts(normalize=True).to_dict()

    all_classes = sorted(set(list(train_dist.keys()) + list(ext_dist.keys())))

    mismatch = {}
    for cls in all_classes:
        t_pct = round(train_dist.get(cls, 0.0) * 100, 3)
        e_pct = round(ext_dist.get(cls, 0.0) * 100, 3)
        diff  = round(e_pct - t_pct, 3)
        mismatch[cls] = {
            "train_pct": t_pct,
            "external_pct": e_pct,
            "diff_pct": diff,
        }

    # Count classes only in one set
    train_only = [c for c in all_classes if c in train_dist and c not in ext_dist]
    ext_only   = [c for c in all_classes if c not in train_dist and c in ext_dist]

    return {
        "per_class": mismatch,
        "classes_only_in_train": train_only,
        "classes_only_in_external": ext_only,
        "train_classes": len(train_dist),
        "external_classes": len(ext_dist),
    }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: ROBUSTNESS TESTING
# ═══════════════════════════════════════════════════════════════════════════

def robustness_test(model, le, df_train: pd.DataFrame):
    """
    Evaluate model degradation under simulated measurement errors:
      - 10% noise on N, P, K
      - ±5% rainfall noise
      - 5% irrigation label flips
      - 5% soil_type misclassification
    """
    np.random.seed(RANDOM_STATE)

    X = df_train[FEATURES].copy()
    y = le.transform(df_train["label"].values)

    # Split consistently with training
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y,
    )
    X_test = X_test.copy().reset_index(drop=True)
    n_test = len(X_test)

    # ── Baseline (clean) ────────────────────────────────────────────────
    proba_clean = model.predict_proba(X_test)
    pred_clean  = model.predict(X_test)
    clean_top1  = accuracy_score(y_test, pred_clean)
    clean_top3  = top_k_accuracy_score(y_test, proba_clean, k=3,
                                       labels=range(len(le.classes_)))
    clean_conf  = proba_clean.max(axis=1)

    # ── Perturbed copy ──────────────────────────────────────────────────
    X_noisy = X_test.copy()

    # 1) 10% measurement error on N, P, K
    for col in ["N", "P", "K"]:
        noise = np.random.normal(0, 0.10, n_test) * X_noisy[col].values
        X_noisy[col] = (X_noisy[col] + noise).clip(0, EXPECTED_RANGES[col][1])

    # 2) ±5% rainfall noise
    rain_noise = np.random.uniform(-0.05, 0.05, n_test) * X_noisy["rainfall"].values
    X_noisy["rainfall"] = (X_noisy["rainfall"] + rain_noise).clip(
        EXPECTED_RANGES["rainfall"][0], EXPECTED_RANGES["rainfall"][1]
    )

    # 3) Flip 5% irrigation labels
    n_flip_irrig = int(n_test * 0.05)
    flip_idx_irrig = np.random.choice(n_test, n_flip_irrig, replace=False)
    X_noisy.loc[flip_idx_irrig, "irrigation"] = 1 - X_noisy.loc[flip_idx_irrig, "irrigation"]

    # 4) Misclassify 5% soil types
    n_flip_soil = int(n_test * 0.05)
    flip_idx_soil = np.random.choice(n_test, n_flip_soil, replace=False)
    for idx in flip_idx_soil:
        current = int(X_noisy.loc[idx, "soil_type"])
        alternatives = [s for s in [0, 1, 2] if s != current]
        X_noisy.loc[idx, "soil_type"] = np.random.choice(alternatives)

    # ── Noisy evaluation ────────────────────────────────────────────────
    proba_noisy = model.predict_proba(X_noisy)
    pred_noisy  = model.predict(X_noisy)
    noisy_top1  = accuracy_score(y_test, pred_noisy)
    noisy_top3  = top_k_accuracy_score(y_test, proba_noisy, k=3,
                                       labels=range(len(le.classes_)))
    noisy_conf  = proba_noisy.max(axis=1)

    # ── Degradation ─────────────────────────────────────────────────────
    top1_degrad = (clean_top1 - noisy_top1) / clean_top1 * 100
    top3_degrad = (clean_top3 - noisy_top3) / clean_top3 * 100
    conf_mean_shift = float(noisy_conf.mean() - clean_conf.mean()) * 100
    conf_std_shift  = float(noisy_conf.std() - clean_conf.std()) * 100

    # ── Itemised noise impact ───────────────────────────────────────────
    # Test each noise source individually
    individual_impacts = {}
    for noise_name, apply_fn in [
        ("npk_10pct_noise", _apply_npk_noise),
        ("rainfall_5pct_noise", _apply_rainfall_noise),
        ("irrigation_5pct_flip", _apply_irrigation_flip),
        ("soil_5pct_misclass", _apply_soil_misclass),
    ]:
        X_single = X_test.copy()
        X_single = apply_fn(X_single, n_test)
        p_single = model.predict(X_single)
        acc_single = accuracy_score(y_test, p_single)
        individual_impacts[noise_name] = {
            "top1_accuracy": round(acc_single * 100, 2),
            "degradation_pct": round((clean_top1 - acc_single) / clean_top1 * 100, 2),
        }

    return {
        "test_samples": n_test,
        "clean_metrics": {
            "top1_accuracy": round(clean_top1 * 100, 2),
            "top3_accuracy": round(clean_top3 * 100, 2),
            "confidence_mean": round(float(clean_conf.mean()) * 100, 2),
            "confidence_std": round(float(clean_conf.std()) * 100, 2),
            "confidence_median": round(float(np.median(clean_conf)) * 100, 2),
        },
        "noisy_metrics": {
            "top1_accuracy": round(noisy_top1 * 100, 2),
            "top3_accuracy": round(noisy_top3 * 100, 2),
            "confidence_mean": round(float(noisy_conf.mean()) * 100, 2),
            "confidence_std": round(float(noisy_conf.std()) * 100, 2),
            "confidence_median": round(float(np.median(noisy_conf)) * 100, 2),
        },
        "degradation": {
            "top1_degradation_pct": round(top1_degrad, 2),
            "top3_degradation_pct": round(top3_degrad, 2),
            "confidence_mean_shift": round(conf_mean_shift, 2),
            "confidence_std_shift": round(conf_std_shift, 2),
        },
        "noise_applied": {
            "npk_gaussian_noise_std": "10%",
            "rainfall_uniform_noise": "±5%",
            "irrigation_flip_rate": "5%",
            "soil_misclass_rate": "5%",
        },
        "individual_impacts": individual_impacts,
    }


# ── Individual noise functions (for itemised impact) ─────────────────────

def _apply_npk_noise(X: pd.DataFrame, n: int) -> pd.DataFrame:
    for col in ["N", "P", "K"]:
        noise = np.random.normal(0, 0.10, n) * X[col].values
        X[col] = (X[col] + noise).clip(0, EXPECTED_RANGES[col][1])
    return X


def _apply_rainfall_noise(X: pd.DataFrame, n: int) -> pd.DataFrame:
    noise = np.random.uniform(-0.05, 0.05, n) * X["rainfall"].values
    X["rainfall"] = (X["rainfall"] + noise).clip(
        EXPECTED_RANGES["rainfall"][0], EXPECTED_RANGES["rainfall"][1]
    )
    return X


def _apply_irrigation_flip(X: pd.DataFrame, n: int) -> pd.DataFrame:
    n_flip = int(n * 0.05)
    idx = np.random.choice(n, n_flip, replace=False)
    X.loc[idx, "irrigation"] = 1 - X.loc[idx, "irrigation"]
    return X


def _apply_soil_misclass(X: pd.DataFrame, n: int) -> pd.DataFrame:
    n_flip = int(n * 0.05)
    idx = np.random.choice(n, n_flip, replace=False)
    for i in idx:
        current = int(X.loc[i, "soil_type"])
        alts = [s for s in [0, 1, 2] if s != current]
        X.loc[i, "soil_type"] = np.random.choice(alts)
    return X


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: CONFIDENCE RELIABILITY (ECE + CALIBRATION CURVE)
# ═══════════════════════════════════════════════════════════════════════════

def confidence_reliability(model, le, df_train: pd.DataFrame, n_bins: int = 10):
    """
    Compute Expected Calibration Error (ECE) and per-bin reliability.
    """
    X = df_train[FEATURES].copy()
    y = le.transform(df_train["label"].values)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y,
    )

    proba = model.predict_proba(X_test)
    pred  = model.predict(X_test)
    max_conf = proba.max(axis=1)
    correct  = (pred == y_test).astype(float)

    # Bin edges from 0 to 1
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bins = []
    ece = 0.0
    total = len(y_test)

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (max_conf >= lo) & (max_conf < hi) if i < n_bins - 1 \
            else (max_conf >= lo) & (max_conf <= hi)
        n_bin = int(mask.sum())

        if n_bin == 0:
            bins.append({
                "bin": f"{lo:.1f}-{hi:.1f}",
                "count": 0,
                "avg_confidence": 0.0,
                "avg_accuracy": 0.0,
                "gap": 0.0,
            })
            continue

        avg_conf = float(max_conf[mask].mean())
        avg_acc  = float(correct[mask].mean())
        gap      = avg_conf - avg_acc

        ece += (n_bin / total) * abs(gap)

        bins.append({
            "bin": f"{lo:.1f}-{hi:.1f}",
            "count": n_bin,
            "avg_confidence": round(avg_conf * 100, 2),
            "avg_accuracy": round(avg_acc * 100, 2),
            "gap": round(gap * 100, 2),
        })

    # Overconfidence gap: weighted average of positive gaps only
    overconf_bins = [b for b in bins if b["gap"] > 0 and b["count"] > 0]
    if overconf_bins:
        weighted_oc = sum(b["gap"] * b["count"] for b in overconf_bins) / \
                      sum(b["count"] for b in overconf_bins)
    else:
        weighted_oc = 0.0

    # Underconfidence gap: weighted average of negative gaps
    underconf_bins = [b for b in bins if b["gap"] < 0 and b["count"] > 0]
    if underconf_bins:
        weighted_uc = sum(abs(b["gap"]) * b["count"] for b in underconf_bins) / \
                      sum(b["count"] for b in underconf_bins)
    else:
        weighted_uc = 0.0

    return {
        "expected_calibration_error": round(ece * 100, 4),
        "overconfidence_gap": round(weighted_oc, 2),
        "underconfidence_gap": round(weighted_uc, 2),
        "n_bins": n_bins,
        "test_samples": len(y_test),
        "reliability_bins": bins,
    }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: EDGE CASE STRESS SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

EDGE_CASES = [
    {
        "name": "Very high NPK, very low rainfall, rainfed",
        "description": "Nutrient-rich soil but severe drought, no irrigation",
        "input": {
            "N": 185, "P": 95, "K": 250,
            "temperature": 30, "humidity": 35, "ph": 7.0,
            "rainfall": 50, "season": 0, "soil_type": 0, "irrigation": 0,
        },
    },
    {
        "name": "Very low NPK but irrigated, loamy",
        "description": "Poor soil but irrigation available",
        "input": {
            "N": 5, "P": 5, "K": 5,
            "temperature": 25, "humidity": 70, "ph": 6.5,
            "rainfall": 800, "season": 0, "soil_type": 1, "irrigation": 1,
        },
    },
    {
        "name": "Clay soil + very low rainfall (conflict)",
        "description": "Clay retains moisture but rainfall is extremely low",
        "input": {
            "N": 80, "P": 40, "K": 60,
            "temperature": 35, "humidity": 20, "ph": 7.5,
            "rainfall": 80, "season": 2, "soil_type": 2, "irrigation": 0,
        },
    },
    {
        "name": "Sandy soil + extremely high rainfall (conflict)",
        "description": "Sandy soil cannot hold water, extreme monsoon rainfall",
        "input": {
            "N": 50, "P": 30, "K": 40,
            "temperature": 28, "humidity": 95, "ph": 5.5,
            "rainfall": 3200, "season": 0, "soil_type": 0, "irrigation": 1,
        },
    },
    {
        "name": "Out-of-range temperature (extreme cold)",
        "description": "Below training data range — near-freezing",
        "input": {
            "N": 60, "P": 30, "K": 80,
            "temperature": 2, "humidity": 60, "ph": 6.0,
            "rainfall": 600, "season": 1, "soil_type": 1, "irrigation": 0,
        },
    },
    {
        "name": "Out-of-range temperature (extreme heat)",
        "description": "Above training data range — desert heat",
        "input": {
            "N": 20, "P": 15, "K": 25,
            "temperature": 48, "humidity": 10, "ph": 8.5,
            "rainfall": 100, "season": 2, "soil_type": 0, "irrigation": 0,
        },
    },
    {
        "name": "Extreme pH (very acidic)",
        "description": "pH below training data range",
        "input": {
            "N": 70, "P": 40, "K": 90,
            "temperature": 26, "humidity": 75, "ph": 3.5,
            "rainfall": 1500, "season": 0, "soil_type": 2, "irrigation": 1,
        },
    },
    {
        "name": "Extreme pH (very alkaline)",
        "description": "pH above training data range",
        "input": {
            "N": 70, "P": 40, "K": 90,
            "temperature": 32, "humidity": 40, "ph": 9.5,
            "rainfall": 400, "season": 1, "soil_type": 0, "irrigation": 0,
        },
    },
    {
        "name": "All features at extreme high",
        "description": "Saturated conditions — everything maxed out",
        "input": {
            "N": 200, "P": 145, "K": 295,
            "temperature": 45, "humidity": 99, "ph": 9.0,
            "rainfall": 3400, "season": 0, "soil_type": 2, "irrigation": 1,
        },
    },
    {
        "name": "All features at extreme low",
        "description": "Minimal conditions — everything at lower bound",
        "input": {
            "N": 1, "P": 1, "K": 1,
            "temperature": 5, "humidity": 5, "ph": 4.0,
            "rainfall": 50, "season": 1, "soil_type": 0, "irrigation": 0,
        },
    },
]


def run_edge_case_tests(model, le):
    """Test model behaviour on extreme / conflicting inputs."""
    results = []

    # Get training set class frequency for dominance check
    df_train = pd.read_csv(TRAIN_CSV)
    top3_train = df_train["label"].value_counts().head(3).index.tolist()

    for case in EDGE_CASES:
        X = pd.DataFrame([case["input"]])[FEATURES]
        proba = model.predict_proba(X)[0]
        pred_idx = np.argmax(proba)
        pred_label = le.inverse_transform([pred_idx])[0]
        pred_conf = float(proba[pred_idx]) * 100

        # Top-3
        top3_idx = np.argsort(proba)[-3:][::-1]
        top3 = [
            {"crop": le.inverse_transform([i])[0],
             "confidence": round(float(proba[i]) * 100, 2)}
            for i in top3_idx
        ]

        # Dominance collapse: does prediction fall into most common training class?
        collapses_to_dominant = pred_label in top3_train

        # Confidence assessment
        if pred_conf >= 90:
            conf_flag = "high_confidence"
        elif pred_conf >= 50:
            conf_flag = "moderate_confidence"
        elif pred_conf >= 20:
            conf_flag = "low_confidence"
        else:
            conf_flag = "very_low_confidence"

        # Entropy of full distribution (higher = more uncertain)
        entropy = -float(np.sum(proba * np.log(proba + 1e-10)))
        max_entropy = np.log(len(le.classes_))  # uniform
        norm_entropy = entropy / max_entropy  # 0..1

        results.append({
            "name": case["name"],
            "description": case["description"],
            "input": case["input"],
            "prediction": pred_label,
            "confidence": round(pred_conf, 2),
            "confidence_flag": conf_flag,
            "top3": top3,
            "collapses_to_dominant_crop": collapses_to_dominant,
            "normalized_entropy": round(norm_entropy, 4),
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: PRINTING
# ═══════════════════════════════════════════════════════════════════════════

def print_validation_issues(issues: dict):
    print_sub("Feature Compatibility")

    if issues["missing_columns"]:
        print(f"    ✗ Missing columns: {issues['missing_columns']}")
    else:
        print(f"    ✓ All {len(FEATURES)} required columns present")

    if issues["extra_columns"]:
        print(f"    ℹ Extra columns (ignored): {issues['extra_columns']}")

    if issues["out_of_range"]:
        print(f"    ⚠ Out-of-range values detected:")
        for feat, info in issues["out_of_range"].items():
            print(f"      {feat:14s}: {info['below_min']} below min, "
                  f"{info['above_max']} above max  "
                  f"(expected {info['expected_range']}, "
                  f"actual [{info['actual_range'][0]}, {info['actual_range'][1]}])")
    else:
        print(f"    ✓ All values within expected ranges")

    if issues["type_warnings"]:
        for w in issues["type_warnings"]:
            print(f"    ⚠ {w}")


def print_drift_report(drift: dict, class_mismatch: dict):
    print_sub("Distribution Drift")

    severe_count = sum(1 for v in drift.values()
                       if isinstance(v, dict) and v.get("severity") == "severe")
    moderate_count = sum(1 for v in drift.values()
                         if isinstance(v, dict) and v.get("severity") == "moderate")
    minor_count = sum(1 for v in drift.values()
                      if isinstance(v, dict) and v.get("severity") == "minor")

    print(f"    Drift summary: {severe_count} severe, {moderate_count} moderate, "
          f"{minor_count} minor, "
          f"{len(FEATURES) - severe_count - moderate_count - minor_count} none")

    print(f"\n    {'Feature':14s} {'Train μ':>10s} {'Ext μ':>10s} "
          f"{'Δμ%':>8s} {'ΔΣ%':>8s} {'KL':>8s} {'Severity':>10s}")
    print(f"    {'─'*14} {'─'*10} {'─'*10} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")

    for feat in FEATURES:
        entry = drift.get(feat, {})
        if entry.get("status") == "missing_in_external":
            print(f"    {feat:14s} {'— MISSING —':>50s}")
            continue
        kl_str = f"{entry.get('kl_divergence', 0):.4f}" if "kl_divergence" in entry else "n/a"
        sev = entry.get("severity", "?")
        marker = " ⚠" if sev in ("moderate", "severe") else ""
        print(f"    {feat:14s} {entry['train_mean']:10.2f} {entry['external_mean']:10.2f} "
              f"{entry['mean_shift_pct']:+7.1f}% {entry['std_shift_pct']:+7.1f}% "
              f"{kl_str:>8s} {sev:>10s}{marker}")

    # Class distribution
    if class_mismatch.get("status") != "no_labels_in_external_data":
        print_sub("Class Distribution Mismatch")
        print(f"    Train classes: {class_mismatch['train_classes']}, "
              f"External classes: {class_mismatch['external_classes']}")
        if class_mismatch["classes_only_in_train"]:
            print(f"    Classes only in train: {class_mismatch['classes_only_in_train']}")
        if class_mismatch["classes_only_in_external"]:
            print(f"    Classes only in external: {class_mismatch['classes_only_in_external']}")

        # Show top mismatches
        per_class = class_mismatch["per_class"]
        sorted_cls = sorted(per_class.items(), key=lambda x: abs(x[1]["diff_pct"]),
                            reverse=True)[:10]
        if sorted_cls:
            print(f"\n    Top 10 class distribution differences:")
            for cls, info in sorted_cls:
                print(f"      {cls:20s}: train={info['train_pct']:5.2f}% "
                      f"ext={info['external_pct']:5.2f}% "
                      f"Δ={info['diff_pct']:+5.2f}%")
    else:
        print(f"\n    ℹ No 'label' column in external data — skipping class distribution check")


def print_robustness(rob: dict):
    print_sub("Clean vs Noisy Metrics")

    c = rob["clean_metrics"]
    n = rob["noisy_metrics"]
    d = rob["degradation"]

    print(f"    {'Metric':30s} {'Clean':>10s} {'Noisy':>10s} {'Degrad.':>10s}")
    print(f"    {'─'*30} {'─'*10} {'─'*10} {'─'*10}")
    print(f"    {'Top-1 Accuracy':30s} {c['top1_accuracy']:9.2f}% {n['top1_accuracy']:9.2f}% "
          f"{d['top1_degradation_pct']:+9.2f}%")
    print(f"    {'Top-3 Accuracy':30s} {c['top3_accuracy']:9.2f}% {n['top3_accuracy']:9.2f}% "
          f"{d['top3_degradation_pct']:+9.2f}%")
    print(f"    {'Confidence Mean':30s} {c['confidence_mean']:9.2f}% {n['confidence_mean']:9.2f}% "
          f"{d['confidence_mean_shift']:+9.2f}%")
    print(f"    {'Confidence Std':30s} {c['confidence_std']:9.2f}% {n['confidence_std']:9.2f}% "
          f"{d['confidence_std_shift']:+9.2f}%")
    print(f"    {'Confidence Median':30s} {c['confidence_median']:9.2f}% "
          f"{n['confidence_median']:9.2f}%")

    print_sub("Individual Noise Source Impact")
    for src, impact in rob["individual_impacts"].items():
        print(f"    {src:30s}: Top-1 = {impact['top1_accuracy']:.2f}%  "
              f"(degrad. {impact['degradation_pct']:+.2f}%)")


def print_reliability(rel: dict):
    print_sub("Expected Calibration Error (ECE)")

    print(f"    ECE Score:           {rel['expected_calibration_error']:.4f}%")
    print(f"    Overconfidence Gap:  {rel['overconfidence_gap']:.2f}%")
    print(f"    Underconfidence Gap: {rel['underconfidence_gap']:.2f}%")
    print(f"    Test samples:        {rel['test_samples']}")

    print(f"\n    {'Bin':>12s} {'Count':>8s} {'Avg Conf':>10s} {'Avg Acc':>10s} {'Gap':>8s}")
    print(f"    {'─'*12} {'─'*8} {'─'*10} {'─'*10} {'─'*8}")
    for b in rel["reliability_bins"]:
        if b["count"] == 0:
            print(f"    {b['bin']:>12s} {b['count']:>8d} {'—':>10s} {'—':>10s} {'—':>8s}")
        else:
            gap_marker = ""
            if b["gap"] > 5:
                gap_marker = " ↑"  # overconfident
            elif b["gap"] < -5:
                gap_marker = " ↓"  # underconfident
            print(f"    {b['bin']:>12s} {b['count']:>8d} {b['avg_confidence']:9.1f}% "
                  f"{b['avg_accuracy']:9.1f}% {b['gap']:+7.1f}%{gap_marker}")


def print_edge_cases(results: list):
    for i, res in enumerate(results, 1):
        flag = "⚠" if res["collapses_to_dominant_crop"] else "✓"
        print(f"\n    [{i:2d}] {res['name']}")
        print(f"         {res['description']}")
        top3_str = ", ".join(f"{t['crop']} ({t['confidence']:.1f}%)" for t in res["top3"])
        print(f"         → {res['prediction']} ({res['confidence']:.1f}%) "
              f"[{res['confidence_flag']}]  {flag}")
        print(f"         Top-3: {top3_str}")
        print(f"         Norm. entropy: {res['normalized_entropy']:.4f}  "
              f"Dominant collapse: {res['collapses_to_dominant_crop']}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print_header("CROP RECOMMENDATION v2.2 — REAL-WORLD VALIDATION")

    # Determine external CSV path
    external_csv = None
    if len(sys.argv) > 1:
        external_csv = sys.argv[1]
        if not os.path.exists(external_csv):
            print(f"\n  ✗ External CSV not found: {external_csv}")
            sys.exit(1)
        print(f"  External CSV:  {external_csv}")
    else:
        print(f"  No external CSV provided — using training data as self-validation")
        print(f"  Usage: python {os.path.basename(__file__)} <external.csv>")

    # ── Load ────────────────────────────────────────────────────────────
    print(f"\n  Loading artifacts …")
    model, le, df_train, metadata = load_artifacts()
    model_version = metadata.get("model_version", "unknown")
    dataset_hash  = metadata.get("dataset_hash", "unknown")
    print(f"  ✓ Model version:  {model_version}")
    print(f"  ✓ Dataset hash:   {dataset_hash}")
    print(f"  ✓ Training rows:  {len(df_train)}")
    print(f"  ✓ Classes:        {len(le.classes_)}")

    # ── Load external data or use training data ─────────────────────────
    if external_csv:
        df_ext = pd.read_csv(external_csv)
        print(f"  ✓ External rows:  {len(df_ext)}")
    else:
        df_ext = df_train.copy()

    # ==================================================================
    # 1. FEATURE COMPATIBILITY
    # ==================================================================
    print_header("1. FEATURE COMPATIBILITY VALIDATION", "─")
    issues = validate_features(df_ext, df_train)
    print_validation_issues(issues)

    # Stop if critical features missing
    if issues["missing_columns"]:
        print(f"\n  ✗ Cannot proceed — missing required columns: "
              f"{issues['missing_columns']}")
        print(f"    Add those columns to the external CSV and re-run.")
        # Still produce partial report
        _save_reports(
            validation={"issues": issues, "status": "incomplete"},
            drift={}, robustness={}, reliability={},
            model_version=model_version, dataset_hash=dataset_hash,
        )
        return

    # ==================================================================
    # 2. DRIFT DETECTION
    # ==================================================================
    print_header("2. DISTRIBUTION DRIFT DETECTION", "─")
    drift = compute_drift(df_ext, df_train)
    class_mismatch = compute_class_distribution_mismatch(df_ext, df_train)
    print_drift_report(drift, class_mismatch)

    # ==================================================================
    # 3. ROBUSTNESS TESTING
    # ==================================================================
    print_header("3. ROBUSTNESS TESTING (Simulated Measurement Errors)", "─")
    rob = robustness_test(model, le, df_train)
    print_robustness(rob)

    # ==================================================================
    # 4. CONFIDENCE RELIABILITY
    # ==================================================================
    print_header("4. CONFIDENCE RELIABILITY CHECK", "─")
    rel = confidence_reliability(model, le, df_train)
    print_reliability(rel)

    # ==================================================================
    # 5. EDGE CASE STRESS SCENARIOS
    # ==================================================================
    print_header("5. EDGE CASE STRESS SCENARIOS", "─")
    edge = run_edge_case_tests(model, le)
    print_edge_cases(edge)

    # Summarise edge case findings
    n_collapse = sum(1 for e in edge if e["collapses_to_dominant_crop"])
    n_high_conf = sum(1 for e in edge if e["confidence"] >= 90)
    n_low_conf  = sum(1 for e in edge if e["confidence"] < 20)
    print(f"\n    Summary: {len(edge)} scenarios tested")
    print(f"      Dominant-crop collapses: {n_collapse}/{len(edge)}")
    print(f"      High confidence (≥90%):  {n_high_conf}/{len(edge)}")
    print(f"      Very low confidence (<20%): {n_low_conf}/{len(edge)}")

    # ==================================================================
    # 6. SAVE REPORTS
    # ==================================================================
    print_header("6. OUTPUT REPORTS", "─")

    validation_report = {
        "feature_compatibility": issues,
        "status": "complete",
    }

    drift_report = {
        "per_feature_drift": drift,
        "class_distribution_mismatch": class_mismatch,
        "drift_summary": {
            "severe": sum(1 for v in drift.values()
                          if isinstance(v, dict) and v.get("severity") == "severe"),
            "moderate": sum(1 for v in drift.values()
                           if isinstance(v, dict) and v.get("severity") == "moderate"),
            "minor": sum(1 for v in drift.values()
                         if isinstance(v, dict) and v.get("severity") == "minor"),
            "none": sum(1 for v in drift.values()
                        if isinstance(v, dict) and v.get("severity") == "none"),
        },
    }

    robustness_report = rob

    reliability_report = rel

    _save_reports(
        validation=validation_report,
        drift=drift_report,
        robustness=robustness_report,
        reliability=reliability_report,
        model_version=model_version,
        dataset_hash=dataset_hash,
        edge_cases=edge,
    )

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print_header("VALIDATION SUMMARY")

    # Overall verdict
    verdicts = []
    # Drift
    severe = drift_report["drift_summary"]["severe"]
    if severe > 0:
        verdicts.append(f"⚠ {severe} features with severe drift")
    else:
        verdicts.append("✓ No severe drift detected")

    # Robustness
    if rob["degradation"]["top1_degradation_pct"] < 5:
        verdicts.append(f"✓ Robustness: Top-1 degrades {rob['degradation']['top1_degradation_pct']:.1f}% (< 5%)")
    else:
        verdicts.append(f"⚠ Robustness: Top-1 degrades {rob['degradation']['top1_degradation_pct']:.1f}% (≥ 5%)")

    # ECE
    if rel["expected_calibration_error"] < 5:
        verdicts.append(f"✓ Calibration: ECE = {rel['expected_calibration_error']:.2f}% (< 5%)")
    else:
        verdicts.append(f"⚠ Calibration: ECE = {rel['expected_calibration_error']:.2f}% (≥ 5%)")

    # Edge cases
    if n_collapse <= 2:
        verdicts.append(f"✓ Edge cases: {n_collapse}/{len(edge)} collapse to dominant crop")
    else:
        verdicts.append(f"⚠ Edge cases: {n_collapse}/{len(edge)} collapse to dominant crop")

    for v in verdicts:
        print(f"  {v}")

    print(f"\n  Reports saved:")
    for f in [REPORT_VALIDATION, REPORT_DRIFT, REPORT_ROBUSTNESS, REPORT_RELIABILITY]:
        print(f"    ✓ {f}")

    print()
    print("═" * 70)
    print("  REAL-WORLD VALIDATION COMPLETE")
    print("═" * 70)


def _save_reports(validation, drift, robustness, reliability,
                  model_version, dataset_hash, edge_cases=None):
    """Write all 4 JSON report files."""
    common = {
        "model_version": model_version,
        "dataset_hash": dataset_hash,
        "validation_date": datetime.now(timezone.utc).isoformat(),
        "script": "03_real_world_validation.py",
    }

    # 1. Validation report
    val_out = {**common, **validation}
    if edge_cases:
        val_out["edge_case_results"] = edge_cases
    with open(REPORT_VALIDATION, "w") as f:
        json.dump(val_out, f, indent=2, default=str)
    print(f"    ✓ {REPORT_VALIDATION}")

    # 2. Drift report
    drift_out = {**common, **drift}
    with open(REPORT_DRIFT, "w") as f:
        json.dump(drift_out, f, indent=2, default=str)
    print(f"    ✓ {REPORT_DRIFT}")

    # 3. Robustness report
    rob_out = {**common, **robustness}
    with open(REPORT_ROBUSTNESS, "w") as f:
        json.dump(rob_out, f, indent=2, default=str)
    print(f"    ✓ {REPORT_ROBUSTNESS}")

    # 4. Reliability report
    rel_out = {**common, **reliability}
    with open(REPORT_RELIABILITY, "w") as f:
        json.dump(rel_out, f, indent=2, default=str)
    print(f"    ✓ {REPORT_RELIABILITY}")


if __name__ == "__main__":
    main()

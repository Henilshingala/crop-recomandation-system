"""
Crop Recommendation — Honest Model (No Data Leakage)
=====================================================

Fixes data leakage in the real-world crop model by removing all
post-planting and geography-identity features:
  REMOVED:  yield, area, production, state_encoded, district_encoded,
            seasonal temperature/rainfall columns

KEPT (pre-planting agronomic + environmental only):
  n, p, k, temperature, humidity, ph, rainfall,
  season, soil_type, irrigation, moisture

Pipeline:
  STEP 1 — Load merged dataset & select honest features
  STEP 2 — Retrain model (RF 400, calibrated)
  STEP 3 — Full evaluation
  STEP 4 — Compare with leaky model
  STEP 5 — Save artifacts

Outputs:
  model_real_world_honest.joblib
  label_encoder_real_honest.joblib
  training_metadata_real_honest.json
  confusion_matrix_real_honest.png
"""

import hashlib
import json
import logging
import os
import warnings
from collections import Counter
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    top_k_accuracy_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("honest_model")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

MERGED_CSV     = "real_world_merged_dataset.csv"
LEAKY_META     = "training_metadata_real.json"

MODEL_FILE     = "model_real_world_honest.joblib"
ENCODER_FILE   = "label_encoder_real_honest.joblib"
METADATA_FILE  = "training_metadata_real_honest.json"
CONFMAT_FILE   = "confusion_matrix_real_honest.png"

RANDOM_STATE   = 42

# ── HONEST features: pre-planting agronomic + environmental ONLY ────────
FEATURES = [
    "n",            # Nitrogen content (soil)
    "p",            # Phosphorous content (soil)
    "k",            # Potassium content (soil)
    "temperature",  # Mean annual temperature
    "humidity",     # Mean humidity
    "ph",           # Soil pH
    "rainfall",     # Annual rainfall
    "season",       # Planting season (kharif/rabi/zaid)
    "soil_type",    # Soil category (sandy/loamy/clayey)
    "irrigation",   # Irrigation availability (0/1)
    "moisture",     # Soil moisture
]

# ── REMOVED (leaky) features ────────────────────────────────────────────
REMOVED_FEATURES = [
    "yield",              # Post-harvest — directly identifies crop
    "area",               # Planted area — correlated with crop identity
    "production",         # Output tonnage — post-harvest leakage
    "state_encoded",      # Geography proxy for crop identity
    "district_encoded",   # Geography proxy for crop identity
    "jun-sep",            # Seasonal temp — redundant with 'temperature'
    "oct-dec",            # Seasonal temp — redundant
    "jan-feb",            # Seasonal temp — redundant
    "mar-may",            # Seasonal temp — redundant
    "rain_monsoon",       # Seasonal rain — redundant with 'rainfall'
    "rain_postmonsoon",   # Seasonal rain — redundant
]


def section(title, step=None):
    sep = "═" * 70
    prefix = f"STEP {step} — " if step else ""
    log.info("")
    log.info(sep)
    log.info(f"  {prefix}{title}")
    log.info(sep)


def sub(msg):
    log.info(f"  ── {msg}")


def sha256_short(data: bytes, length: int = 16) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD AND SELECT HONEST FEATURES
# ═══════════════════════════════════════════════════════════════════════════

def step1_load():
    section("LOAD MERGED DATASET & SELECT HONEST FEATURES", 1)

    if not os.path.exists(MERGED_CSV):
        log.error(f"  {MERGED_CSV} not found. Run 09_real_world_pipeline.py first.")
        raise FileNotFoundError(MERGED_CSV)

    df = pd.read_csv(MERGED_CSV, low_memory=False)
    log.info(f"  Loaded {MERGED_CSV}: {len(df):,} rows × {df.shape[1]} cols")

    # ── Show what we're removing and why ────────────────────────────────
    sub("Data leakage audit")
    log.info("")
    log.info("    ┌────────────────────────┬──────────────────────────────────────────┐")
    log.info("    │  REMOVED COLUMN        │  REASON                                  │")
    log.info("    ├────────────────────────┼──────────────────────────────────────────┤")
    log.info("    │  yield                 │  Post-harvest output — encodes crop ID   │")
    log.info("    │  area                  │  Planted hectares — crop-specific         │")
    log.info("    │  production            │  Harvest tonnage — post-planting          │")
    log.info("    │  state_encoded         │  Geography proxy for crop distribution   │")
    log.info("    │  district_encoded      │  Geography proxy for crop distribution   │")
    log.info("    │  seasonal temp columns │  Redundant with annual temperature       │")
    log.info("    │  seasonal rain columns │  Redundant with annual rainfall          │")
    log.info("    └────────────────────────┴──────────────────────────────────────────┘")

    # ── Verify all honest features exist ────────────────────────────────
    sub("Verifying honest features")
    available = [f for f in FEATURES if f in df.columns]
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        log.warning(f"    Missing features (dropped): {missing}")
        available = [f for f in available]  # use what's available

    log.info(f"    Honest features ({len(available)}): {available}")

    # ── Encode target ───────────────────────────────────────────────────
    sub("Encoding crop target")
    le_crop = LabelEncoder()
    df["crop_encoded"] = le_crop.fit_transform(df["crop"])
    log.info(f"    Classes: {len(le_crop.classes_)} — {list(le_crop.classes_)}")

    # ── Handle NaN in features ──────────────────────────────────────────
    sub("Handling NaN values")
    for col in available:
        na_count = df[col].isna().sum()
        if na_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log.info(f"    Filled {na_count:,} NaN in '{col}' with median ({median_val:.2f})")

    na_total = df[available].isna().sum().sum()
    log.info(f"    Remaining NaN: {na_total}")

    # ── Feature statistics ──────────────────────────────────────────────
    sub("Feature statistics (honest features only)")
    log.info(f"    {'Feature':15s} {'min':>10s} {'max':>10s} {'mean':>10s} {'std':>10s}")
    log.info(f"    {'─'*15} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
    for col in available:
        log.info(f"    {col:15s} {df[col].min():10.2f} {df[col].max():10.2f} "
                 f"{df[col].mean():10.2f} {df[col].std():10.2f}")

    # ── Class distribution ──────────────────────────────────────────────
    sub("Class distribution")
    counts = df["crop"].value_counts()
    for crop, cnt in counts.items():
        bar = "█" * max(1, int(cnt / counts.max() * 30))
        log.info(f"    {crop:18s}: {cnt:>6,}  {bar}")
    log.info(f"    Imbalance ratio: {counts.max() / counts.min():.1f}x")

    return df, available, le_crop


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — RETRAIN MODEL
# ═══════════════════════════════════════════════════════════════════════════

def step2_train(df: pd.DataFrame, features: list, le_crop: LabelEncoder):
    section("RETRAIN MODEL (HONEST FEATURES ONLY)", 2)

    X = df[features].values
    y = le_crop.transform(df["crop"].values)

    # ── Train-test split ────────────────────────────────────────────────
    sub("Train-test split (80/20, stratified)")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y,
    )
    log.info(f"    Train: {len(X_train):,}   Test: {len(X_test):,}")
    log.info(f"    Features: {len(features)}")
    log.info(f"    Classes: {len(le_crop.classes_)}")

    # ── Train base Random Forest ────────────────────────────────────────
    sub("Training RandomForestClassifier (n_estimators=400)")
    base_rf = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    base_rf.fit(X_train, y_train)
    log.info("    ✓ Base RF trained")

    # ── Evaluate base ───────────────────────────────────────────────────
    y_pred_base = base_rf.predict(X_test)
    y_proba_base = base_rf.predict_proba(X_test)
    n_classes = len(le_crop.classes_)
    k3 = min(3, n_classes)

    acc_base = accuracy_score(y_test, y_pred_base)
    top3_base = top_k_accuracy_score(y_test, y_proba_base, k=k3, labels=range(n_classes))
    maxc_base = y_proba_base.max(axis=1).max() * 100

    log.info(f"    Base RF → Top-1: {acc_base*100:.2f}%  Top-3: {top3_base*100:.2f}%  "
             f"Max Conf: {maxc_base:.1f}%")

    # ── Calibrate ───────────────────────────────────────────────────────
    sub("Calibrating with CalibratedClassifierCV (sigmoid, cv=3)")
    cal_model = CalibratedClassifierCV(
        estimator=base_rf, method="sigmoid", cv=3, n_jobs=-1,
    )
    cal_model.fit(X_train, y_train)
    log.info("    ✓ Calibrated model trained")

    # ── Evaluate calibrated ─────────────────────────────────────────────
    y_pred = cal_model.predict(X_test)
    y_proba = cal_model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    top3 = top_k_accuracy_score(y_test, y_proba, k=k3, labels=range(n_classes))
    maxc = y_proba.max(axis=1).max() * 100

    log.info("")
    log.info("    ┌──────────────────────────────────────────────────┐")
    log.info(f"    │  BEFORE CALIBRATION                              │")
    log.info(f"    │  Top-1: {acc_base*100:6.2f}%   Top-3: {top3_base*100:6.2f}%   "
             f"Max: {maxc_base:5.1f}%  │")
    log.info("    ├──────────────────────────────────────────────────┤")
    log.info(f"    │  AFTER CALIBRATION                               │")
    log.info(f"    │  Top-1: {accuracy*100:6.2f}%   Top-3: {top3*100:6.2f}%   "
             f"Max: {maxc:5.1f}%  │")
    log.info("    └──────────────────────────────────────────────────┘")

    return {
        "model": cal_model,
        "base_model": base_rf,
        "accuracy": accuracy,
        "top3_accuracy": top3,
        "base_accuracy": acc_base,
        "base_top3": top3_base,
        "max_conf": maxc,
        "max_conf_base": maxc_base,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "y_pred": y_pred,
        "y_proba": y_proba,
        "features": features,
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — FULL EVALUATION
# ═══════════════════════════════════════════════════════════════════════════

def step3_evaluate(results: dict, le_crop: LabelEncoder, df: pd.DataFrame):
    section("FULL EVALUATION — HONEST MODEL", 3)

    y_test = results["y_test"]
    y_pred = results["y_pred"]
    y_proba = results["y_proba"]
    base_rf = results["base_model"]
    features = results["features"]
    n_classes = len(le_crop.classes_)

    # ── Accuracy summary ────────────────────────────────────────────────
    sub("Accuracy Summary")
    log.info(f"    Top-1 Accuracy:  {results['accuracy']*100:.2f}%")
    log.info(f"    Top-3 Accuracy:  {results['top3_accuracy']*100:.2f}%")
    log.info(f"    Max Confidence:  {results['max_conf']:.1f}%")

    # ── Classification report ───────────────────────────────────────────
    sub("Classification Report")
    report_str = classification_report(
        y_test, y_pred, target_names=le_crop.classes_, zero_division=0,
    )
    print(report_str)

    report_dict = classification_report(
        y_test, y_pred, target_names=le_crop.classes_,
        zero_division=0, output_dict=True,
    )

    # ── Feature importances ─────────────────────────────────────────────
    sub("Feature Importances")
    importances = pd.Series(
        base_rf.feature_importances_, index=features,
    ).sort_values(ascending=False)

    for feat, imp in importances.items():
        bar = "█" * max(1, int(imp * 60))
        log.info(f"    {feat:15s}: {imp:.4f}  {bar}")

    # ── Confusion matrix ────────────────────────────────────────────────
    sub("Confusion Matrix")
    cm = confusion_matrix(y_test, y_pred)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(14, 12))
        im = ax.imshow(cm, interpolation="nearest", cmap="YlGn")
        ax.set_title("Confusion Matrix — Honest Real-World Model\n"
                      "(No leakage: yield/area/production/geography removed)",
                      fontsize=13, pad=14)
        ticks = np.arange(n_classes)
        ax.set_xticks(ticks)
        ax.set_xticklabels(le_crop.classes_, rotation=90, fontsize=8)
        ax.set_yticks(ticks)
        ax.set_yticklabels(le_crop.classes_, fontsize=8)
        ax.set_ylabel("True", fontsize=11)
        ax.set_xlabel("Predicted", fontsize=11)
        fig.colorbar(im, ax=ax, shrink=0.6)

        # Annotate cells
        thresh = cm.max() / 2
        for i in range(n_classes):
            for j in range(n_classes):
                if cm[i, j] > 0:
                    ax.text(j, i, str(cm[i, j]),
                            ha="center", va="center", fontsize=5,
                            color="white" if cm[i, j] > thresh else "black")

        fig.tight_layout()
        fig.savefig(CONFMAT_FILE, dpi=150)
        plt.close(fig)
        log.info(f"    ✓ Saved {CONFMAT_FILE}")
    except ImportError:
        log.info("    matplotlib not available — skipping plot")

    # ── 5-fold cross-validation ─────────────────────────────────────────
    sub("5-Fold Stratified Cross-Validation")
    X_all = df[features].values
    y_all = le_crop.transform(df["crop"].values)

    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_rf = RandomForestClassifier(
        n_estimators=400, min_samples_split=5, min_samples_leaf=2,
        random_state=RANDOM_STATE, n_jobs=-1,
    )
    cv_scores = cross_val_score(cv_rf, X_all, y_all, cv=kfold, scoring="accuracy")
    log.info(f"    Fold accuracies: {np.round(cv_scores, 6)}")
    log.info(f"    Mean: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    results["cv_mean"] = float(cv_scores.mean())
    results["cv_std"] = float(cv_scores.std())
    results["importances"] = importances
    results["report_dict"] = report_dict

    return results


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — COMPARE WITH LEAKY MODEL
# ═══════════════════════════════════════════════════════════════════════════

def step4_compare(results: dict):
    section("COMPARE WITH LEAKY MODEL", 4)

    if not os.path.exists(LEAKY_META):
        log.warning(f"  {LEAKY_META} not found — skipping comparison")
        return {}

    with open(LEAKY_META) as f:
        leaky = json.load(f)

    # ── Build comparison table ──────────────────────────────────────────
    sub("Accuracy Comparison")

    lk_top1 = leaky["top1_accuracy"] * 100
    lk_top3 = leaky["top3_accuracy"] * 100
    lk_maxc = leaky["max_confidence_pct"]
    lk_cv   = leaky["cv_mean"] * 100
    lk_feat = len(leaky["features"])

    ho_top1 = results["accuracy"] * 100
    ho_top3 = results["top3_accuracy"] * 100
    ho_maxc = results["max_conf"]
    ho_cv   = results["cv_mean"] * 100
    ho_feat = len(results["features"])

    log.info("")
    log.info("    ┌──────────────────────┬────────────────┬────────────────┬────────────┐")
    log.info("    │  Metric              │  Leaky Model   │  Honest Model  │  Δ         │")
    log.info("    ├──────────────────────┼────────────────┼────────────────┼────────────┤")
    log.info(f"    │  Top-1 Accuracy      │  {lk_top1:11.2f}%  │  {ho_top1:11.2f}%  │  {ho_top1 - lk_top1:+8.2f}%  │")
    log.info(f"    │  Top-3 Accuracy      │  {lk_top3:11.2f}%  │  {ho_top3:11.2f}%  │  {ho_top3 - lk_top3:+8.2f}%  │")
    log.info(f"    │  Max Confidence      │  {lk_maxc:11.1f}%  │  {ho_maxc:11.1f}%  │  {ho_maxc - lk_maxc:+8.1f}%  │")
    log.info(f"    │  CV Mean             │  {lk_cv:11.2f}%  │  {ho_cv:11.2f}%  │  {ho_cv - lk_cv:+8.2f}%  │")
    log.info(f"    │  Features Used       │  {lk_feat:12d}   │  {ho_feat:12d}   │  {ho_feat - lk_feat:+9d}   │")
    log.info("    └──────────────────────┴────────────────┴────────────────┴────────────┘")

    # ── Feature importance comparison (common features) ─────────────────
    sub("Feature Importance Comparison (common features)")
    lk_imp = leaky.get("feature_importances", {})
    ho_imp = results["importances"]

    common = sorted(set(lk_imp.keys()) & set(ho_imp.index))
    log.info(f"    {'Feature':15s} {'Leaky':>10s} {'Honest':>10s} {'Δ':>10s}")
    log.info(f"    {'─'*15} {'─'*10} {'─'*10} {'─'*10}")
    for feat in common:
        lv = lk_imp[feat]
        hv = float(ho_imp.get(feat, 0))
        log.info(f"    {feat:15s} {lv:9.4f} {hv:9.4f} {hv - lv:+9.4f}")

    # ── Removed features and their leaked importance ────────────────────
    sub("Importance of REMOVED (leaky) features in old model")
    removed_in_leaky = {f: lk_imp[f] for f in REMOVED_FEATURES if f in lk_imp}
    total_leaked = sum(removed_in_leaky.values())
    for feat, imp in sorted(removed_in_leaky.items(), key=lambda x: -x[1]):
        bar = "█" * max(1, int(imp * 100))
        log.info(f"    {feat:22s}: {imp:.4f}  {bar}  ← REMOVED")
    log.info(f"    Total leaked importance: {total_leaked:.4f} "
             f"({total_leaked*100:.1f}% of model decisions based on leakage)")

    comparison = {
        "leaky_top1": round(lk_top1, 2),
        "leaky_top3": round(lk_top3, 2),
        "leaky_max_conf": round(lk_maxc, 1),
        "leaky_cv": round(lk_cv, 2),
        "leaky_features": lk_feat,
        "honest_top1": round(ho_top1, 2),
        "honest_top3": round(ho_top3, 2),
        "honest_max_conf": round(ho_maxc, 1),
        "honest_cv": round(ho_cv, 2),
        "honest_features": ho_feat,
        "top1_diff": round(ho_top1 - lk_top1, 2),
        "top3_diff": round(ho_top3 - lk_top3, 2),
        "total_leaked_importance": round(total_leaked, 4),
        "removed_features": REMOVED_FEATURES,
    }

    return comparison


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — SAVE ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

def step5_save(results: dict, le_crop: LabelEncoder, df: pd.DataFrame,
               comparison: dict):
    section("SAVE ARTIFACTS", 5)

    model = results["model"]
    features = results["features"]

    # ── Save model ──────────────────────────────────────────────────────
    joblib.dump(model, MODEL_FILE)
    log.info(f"  ✓ {MODEL_FILE}")

    # ── Save label encoder ──────────────────────────────────────────────
    joblib.dump(le_crop, ENCODER_FILE)
    log.info(f"  ✓ {ENCODER_FILE}")

    # ── Build and save metadata ─────────────────────────────────────────
    ml_subset = df[features + ["crop"]]
    csv_bytes = ml_subset.to_csv(index=False).encode("utf-8")
    dataset_hash = sha256_short(csv_bytes)

    with open(MODEL_FILE, "rb") as f:
        model_hash = sha256_short(f.read())

    metadata = {
        "model_version": "real_world_honest_1.0",
        "model_type": "CalibratedClassifierCV(RandomForestClassifier)",
        "calibration_method": "sigmoid",
        "calibration_cv": 3,
        "n_estimators": 400,
        "honest_model": True,
        "data_leakage_fixed": True,
        "features": features,
        "removed_leaky_features": REMOVED_FEATURES,
        "dataset": MERGED_CSV,
        "dataset_hash": dataset_hash,
        "model_file_hash": model_hash,
        "top1_accuracy": round(results["accuracy"], 6),
        "top3_accuracy": round(results["top3_accuracy"], 6),
        "base_top1_accuracy": round(results["base_accuracy"], 6),
        "base_top3_accuracy": round(results["base_top3"], 6),
        "max_confidence_pct": round(results["max_conf"], 2),
        "cv_mean": round(results["cv_mean"], 6),
        "cv_std": round(results["cv_std"], 6),
        "total_classes": int(len(le_crop.classes_)),
        "classes": list(le_crop.classes_),
        "total_samples": int(len(df)),
        "class_distribution": df["crop"].value_counts().to_dict(),
        "feature_importances": {
            feat: round(float(imp), 6)
            for feat, imp in results["importances"].items()
        },
        "per_class_metrics": {
            crop: {
                "precision": round(results["report_dict"][crop]["precision"], 4),
                "recall": round(results["report_dict"][crop]["recall"], 4),
                "f1-score": round(results["report_dict"][crop]["f1-score"], 4),
                "support": int(results["report_dict"][crop]["support"]),
            }
            for crop in le_crop.classes_
        },
        "comparison_with_leaky_model": comparison,
        "data_sources": [
            "ICRISAT-District_Level_Data.csv",
            "data_core.csv",
            "temperature.csv",
            "rainfall.csv",
            "Crop_recommendation.csv",
        ],
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_state": RANDOM_STATE,
        "note": (
            "Honest crop recommendation model. All post-planting and geography-"
            "identity features removed to eliminate data leakage. Uses only "
            "pre-planting agronomic and environmental features for prediction. "
            "No synthetic data. No shortcuts. No leakage."
        ),
    }

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    log.info(f"  ✓ {METADATA_FILE}")

    return metadata


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    log.info("")
    log.info("╔══════════════════════════════════════════════════════════════════════╗")
    log.info("║  CROP RECOMMENDATION — HONEST MODEL (NO DATA LEAKAGE)              ║")
    log.info("║  Pre-planting features only · No yield/area/production/geography   ║")
    log.info("╚══════════════════════════════════════════════════════════════════════╝")

    # STEP 1
    df, features, le_crop = step1_load()

    # STEP 2
    results = step2_train(df, features, le_crop)

    # STEP 3
    results = step3_evaluate(results, le_crop, df)

    # STEP 4
    comparison = step4_compare(results)

    # STEP 5
    metadata = step5_save(results, le_crop, df, comparison)

    # ── Final summary ──────────────────────────────────────────────────
    log.info("")
    log.info("═" * 70)
    log.info("  HONEST MODEL — FINAL SUMMARY")
    log.info("═" * 70)
    log.info(f"  Features:         {len(features)} (pre-planting only)")
    log.info(f"  Removed:          {len(REMOVED_FEATURES)} leaky features")
    log.info(f"  Samples:          {len(df):,}")
    log.info(f"  Classes:          {len(le_crop.classes_)}")
    log.info(f"  Top-1 Accuracy:   {results['accuracy']*100:.2f}%")
    log.info(f"  Top-3 Accuracy:   {results['top3_accuracy']*100:.2f}%")
    log.info(f"  Max Confidence:   {results['max_conf']:.1f}%")
    log.info(f"  CV Mean:          {results['cv_mean']*100:.2f}% ± {results['cv_std']*100:.2f}%")
    log.info(f"  Model:            {MODEL_FILE}")
    log.info(f"  Encoder:          {ENCODER_FILE}")
    log.info(f"  Metadata:         {METADATA_FILE}")
    log.info(f"  Confusion matrix: {CONFMAT_FILE}")
    log.info("═" * 70)


if __name__ == "__main__":
    main()

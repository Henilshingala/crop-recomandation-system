"""
Crop Recommendation System — Model Training & Evaluation (v2.2)
================================================================

Trains a Random Forest classifier, wraps with CalibratedClassifierCV,
evaluates with confusion matrix, top-3 accuracy, cross-validation,
non-uniform geographic dominance test, and saves all artifacts.

v2.2 IMPROVEMENTS:
- irrigation feature included
- Strengthened soil_type feature importance
- n_estimators=400
- Non-uniform weighted geographic simulation
- Asymmetric noise
- Realistic imbalanced samples
- Updated metadata with dominance test results

Reads : Crop_recommendation_v2.csv
Writes: model_rf.joblib, label_encoder.joblib, training_metadata.json,
        confusion_matrix.png
"""

import hashlib
import json
import os
import sys
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
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder

# ===========================================================================
# CONFIG
# ===========================================================================
DATASET_CSV   = "Crop_recommendation_v2.csv"
MODEL_FILE    = "model_rf.joblib"
ENCODER_FILE  = "label_encoder.joblib"
METADATA_FILE = "training_metadata.json"
CONFMAT_FILE  = "confusion_matrix.png"
RANDOM_STATE  = 42
TEST_SIZE     = 0.20

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "season", "soil_type", "irrigation"]

# ===========================================================================
# LOAD DATA
# ===========================================================================
print("=" * 70)
print("  CROP RECOMMENDATION v2.2 — TRAINING & EVALUATION")
print("  Calibration · Soil · Irrigation · Non-uniform geo test")
print("=" * 70)

if not os.path.exists(DATASET_CSV):
    print(f"\n[ERROR] Dataset '{DATASET_CSV}' not found.")
    print("        Run 01_dataset_generation.py first.")
    sys.exit(1)

print(f"\n[1/10] Loading dataset: {DATASET_CSV}")
df = pd.read_csv(DATASET_CSV)
print(f"       Rows: {len(df)}, Features: {len(FEATURES)}, Classes: {df['label'].nunique()}")

X = df[FEATURES].copy()
y = df["label"].copy()

# ===========================================================================
# ENCODE LABELS
# ===========================================================================
print("\n[2/10] Encoding labels …")
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"       Classes ({len(le.classes_)}): {list(le.classes_)}")

# ===========================================================================
# TRAIN / TEST SPLIT
# ===========================================================================
print(f"\n[3/10] Train-test split ({int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}, stratified) …")
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y_encoded,
)
print(f"       Train: {len(X_train)}, Test: {len(X_test)}")

# ===========================================================================
# TRAIN BASE MODEL
# ===========================================================================
print("\n[4/10] Training base Random Forest (n_estimators=150, max_depth=25) …")
base_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=25,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
base_model.fit(X_train, y_train)
print("       ✓ Base model trained")

# ===========================================================================
# EVALUATE BASE MODEL (before calibration)
# ===========================================================================
print("\n[5/10] Base model evaluation (pre-calibration) …")
y_pred_base = base_model.predict(X_test)
y_proba_base = base_model.predict_proba(X_test)

acc_base = accuracy_score(y_test, y_pred_base)
top3_base = top_k_accuracy_score(y_test, y_proba_base, k=3, labels=range(len(le.classes_)))
max_conf_base = y_proba_base.max(axis=1).max() * 100

print(f"       Top-1 Accuracy : {acc_base*100:.2f}%")
print(f"       Top-3 Accuracy : {top3_base*100:.2f}%")
print(f"       Max Confidence : {max_conf_base:.1f}%")

# ===========================================================================
# CALIBRATE MODEL
# ===========================================================================
print("\n[6/10] Calibrating with CalibratedClassifierCV (sigmoid, cv=3) …")
calibrated_model = CalibratedClassifierCV(
    estimator=base_model,
    method="sigmoid",
    cv=3,
    n_jobs=-1,
)
calibrated_model.fit(X_train, y_train)
print("       ✓ Calibrated model trained")

# Use calibrated model as the final model
model = calibrated_model

# ===========================================================================
# EVALUATE CALIBRATED MODEL
# ===========================================================================
print("\n[7/10] Calibrated model evaluation …")
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

accuracy = accuracy_score(y_test, y_pred)
top3_accuracy = top_k_accuracy_score(y_test, y_proba, k=3, labels=range(len(le.classes_)))
max_conf = y_proba.max(axis=1).max() * 100

print(f"\n       ┌──────────────────────────────────────────────┐")
print(f"       │  BEFORE CALIBRATION                          │")
print(f"       │  Top-1: {acc_base*100:6.2f}%   Top-3: {top3_base*100:6.2f}%   Max: {max_conf_base:.1f}%  │")
print(f"       ├──────────────────────────────────────────────┤")
print(f"       │  AFTER CALIBRATION                           │")
print(f"       │  Top-1: {accuracy*100:6.2f}%   Top-3: {top3_accuracy*100:6.2f}%   Max: {max_conf:.1f}%  │")
print(f"       └──────────────────────────────────────────────┘")

print("\n       Classification Report:")
report_str = classification_report(y_test, y_pred, target_names=le.classes_)
print(report_str)

# ── Feature Importance (from base model) ─────────────────────────────────
print("       Feature Importances:")
importances = pd.Series(base_model.feature_importances_, index=FEATURES).sort_values(ascending=False)
for feat, imp in importances.items():
    bar = "█" * int(imp * 80)
    print(f"         {feat:14s} : {imp:.4f}  {bar}")

soil_importance = importances.get("soil_type", 0)
irrigation_importance = importances.get("irrigation", 0)
print(f"\n       ── Soil importance:       {soil_importance:.4f} (target ≥ 0.03)")
print(f"       ── Irrigation importance: {irrigation_importance:.4f} (target ≥ 0.02)")

# ===========================================================================
# CONFUSION MATRIX
# ===========================================================================
print(f"\n[8/10] Saving confusion matrix → {CONFMAT_FILE} …")
cm = confusion_matrix(y_test, y_pred)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(20, 18))
    im = ax.imshow(cm, interpolation="nearest", cmap="YlGn")
    ax.set_title("Confusion Matrix — Crop Recommendation v2.2 (Calibrated)", fontsize=16, pad=15)

    tick_marks = np.arange(len(le.classes_))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(le.classes_, rotation=90, fontsize=7)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(le.classes_, fontsize=7)
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_xlabel("Predicted Label", fontsize=12)

    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.tight_layout()
    fig.savefig(CONFMAT_FILE, dpi=150)
    plt.close(fig)
    print(f"       ✓ Saved {CONFMAT_FILE}")
except ImportError:
    print("       ⚠ matplotlib not available — skipping plot")
    print(cm)

# ===========================================================================
# CROSS-VALIDATION
# ===========================================================================
print("\n[9/10] 5-Fold Stratified Cross-Validation (base model) …")
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=25,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
cv_scores = cross_val_score(cv_model, X, y_encoded, cv=kfold, scoring="accuracy")

print(f"       Fold Accuracies : {cv_scores}")
print(f"       Mean Accuracy   : {cv_scores.mean():.4f}")
print(f"       Std Deviation   : {cv_scores.std():.4f}")

# ===========================================================================
# SAVE MODEL ARTIFACTS
# ===========================================================================
print(f"\n[10/10] Saving artifacts …")

joblib.dump(model, MODEL_FILE, compress=3)
print(f"        ✓ {MODEL_FILE} (calibrated, compressed)")

joblib.dump(le, ENCODER_FILE, compress=3)
print(f"        ✓ {ENCODER_FILE}")

# ── Hashes ───────────────────────────────────────────────────────────────
csv_bytes = df.to_csv(index=False).encode("utf-8")
dataset_hash = hashlib.sha256(csv_bytes).hexdigest()[:16]

with open(MODEL_FILE, "rb") as f:
    model_hash = hashlib.sha256(f.read()).hexdigest()[:16]

# ===========================================================================
# STRESS TEST
# ===========================================================================
print("\n" + "=" * 70)
print("  STRESS TEST — Edge-case predictions (calibrated)")
print("=" * 70)

# soil_type: 0=sandy, 1=loamy, 2=clay  |  irrigation: 0=rainfed, 1=irrigated
stress_cases = pd.DataFrame([
    {"N": 100, "P": 50, "K": 50, "temperature": 28, "humidity": 85,
     "ph": 6.5, "rainfall": 2000, "season": 0, "soil_type": 2, "irrigation": 1},

    {"N": 90, "P": 50, "K": 40, "temperature": 18, "humidity": 55,
     "ph": 6.5, "rainfall": 550, "season": 1, "soil_type": 1, "irrigation": 1},

    {"N": 120, "P": 50, "K": 65, "temperature": 28, "humidity": 65,
     "ph": 7.0, "rainfall": 720, "season": 0, "soil_type": 0, "irrigation": 0},

    {"N": 30, "P": 30, "K": 175, "temperature": 18, "humidity": 78,
     "ph": 6.0, "rainfall": 1050, "season": 1, "soil_type": 1, "irrigation": 1},

    {"N": 30, "P": 20, "K": 30, "temperature": 38, "humidity": 25,
     "ph": 7.8, "rainfall": 280, "season": 2, "soil_type": 0, "irrigation": 0},
])

preds_enc = model.predict(stress_cases)
pred_labels = le.inverse_transform(preds_enc)
pred_proba = model.predict_proba(stress_cases)

scenarios = [
    "High-rain tropical, clay, irrigated (→ rice?)",
    "Cool dry Rabi, loamy, irrigated (→ wheat?)",
    "Semi-arid, sandy, rainfed (→ cotton?)",
    "Temperate high-K, loamy, irrigated (→ apple?)",
    "Extreme hot-dry, sandy, rainfed (→ date_palm?)",
]

any_100 = False
for i, (scenario, label) in enumerate(zip(scenarios, pred_labels)):
    confidence = pred_proba[i].max() * 100
    if confidence >= 99.5:
        any_100 = True
    top3_idx = np.argsort(pred_proba[i])[-3:][::-1]
    top3 = [(le.classes_[j], pred_proba[i][j] * 100) for j in top3_idx]
    top3_str = ", ".join(f"{c} ({v:.1f}%)" for c, v in top3)
    print(f"\n  {scenario}")
    print(f"    Prediction: {label} ({confidence:.1f}%)")
    print(f"    Top 3:      {top3_str}")

if any_100:
    print("\n  ⚠ WARNING: Some stress test predictions still ≥ 99.5%")
else:
    print("\n  ✓ All stress test predictions < 99.5% — no deterministic 100%")

# ===========================================================================
# GEOGRAPHIC TEST — 1000 NON-UNIFORM India-like environments
# ===========================================================================
print("\n" + "=" * 70)
print("  GEOGRAPHIC TEST — 1000 weighted India-like environments")
print("  40% monsoon-heavy · 30% semi-arid · 20% plateau · 10% cool")
print("=" * 70)

np.random.seed(123)
n_geo = 1000

# Weighted zone allocation
n_monsoon  = int(n_geo * 0.40)   # 400 — high rainfall, tropical
n_semiarid = int(n_geo * 0.30)   # 300 — semi-arid, moderate
n_plateau  = int(n_geo * 0.20)   # 200 — moderate plateau
n_cool     = n_geo - n_monsoon - n_semiarid - n_plateau  # 100 — cool region

def make_zone(n, temp_range, hum_range, rain_range, ph_range,
              season_weights, soil_weights, irrig_prob):
    """Generate geo samples for a specific climate zone."""
    return pd.DataFrame({
        "N":           np.random.uniform(5, 150, n),
        "P":           np.random.uniform(5, 100, n),
        "K":           np.random.uniform(5, 250, n),
        "temperature": np.random.uniform(*temp_range, n),
        "humidity":    np.random.uniform(*hum_range, n),
        "ph":          np.random.uniform(*ph_range, n),
        "rainfall":    np.random.uniform(*rain_range, n),
        "season":      np.random.choice([0, 1, 2], n, p=season_weights),
        "soil_type":   np.random.choice([0, 1, 2], n, p=soil_weights),
        "irrigation":  np.random.choice([0, 1], n, p=[1-irrig_prob, irrig_prob]),
    })

# Monsoon-heavy zone: high rainfall, hot, humid
geo_monsoon = make_zone(n_monsoon,
    temp_range=(25, 38), hum_range=(60, 95), rain_range=(1000, 3000),
    ph_range=(5.0, 7.5), season_weights=[0.6, 0.2, 0.2],
    soil_weights=[0.2, 0.4, 0.4], irrig_prob=0.5)

# Semi-arid zone: moderate rainfall, hot, dry
geo_semiarid = make_zone(n_semiarid,
    temp_range=(25, 40), hum_range=(20, 60), rain_range=(200, 800),
    ph_range=(6.0, 8.5), season_weights=[0.5, 0.3, 0.2],
    soil_weights=[0.5, 0.35, 0.15], irrig_prob=0.3)

# Moderate plateau zone: medium rainfall, warm
geo_plateau = make_zone(n_plateau,
    temp_range=(18, 32), hum_range=(40, 80), rain_range=(500, 1200),
    ph_range=(5.5, 7.5), season_weights=[0.3, 0.4, 0.3],
    soil_weights=[0.15, 0.6, 0.25], irrig_prob=0.45)

# Cool zone: low-moderate rainfall, cold
geo_cool = make_zone(n_cool,
    temp_range=(10, 24), hum_range=(35, 80), rain_range=(300, 1200),
    ph_range=(5.5, 7.0), season_weights=[0.1, 0.7, 0.2],
    soil_weights=[0.1, 0.7, 0.2], irrig_prob=0.5)

geo_samples = pd.concat([geo_monsoon, geo_semiarid, geo_plateau, geo_cool],
                         ignore_index=True)

geo_preds = model.predict(geo_samples)
geo_labels = le.inverse_transform(geo_preds)
geo_proba = model.predict_proba(geo_samples)

# Dominance analysis
from collections import Counter
dominance = Counter(geo_labels)
total_geo = len(geo_labels)

print("\n  Crop dominance frequency (top 15):")
for crop, count in dominance.most_common(15):
    pct = count / total_geo * 100
    bar = "█" * int(pct / 2)
    print(f"    {crop:20s} : {count:4d} ({pct:5.1f}%)  {bar}")

# Dominance checks
rice_pct = dominance.get("rice", 0) / total_geo * 100
max_dom_crop, max_dom_count = dominance.most_common(1)[0]
max_dom_pct = max_dom_count / total_geo * 100
unique_crops = len(set(geo_labels))

print(f"\n  Rice dominance: {rice_pct:.1f}%", end="")
if rice_pct > 5:
    print("  ⚠ HIGH — rice > 5%")
else:
    print("  ✓ Healthy (< 5%)")

print(f"  Max dominance: {max_dom_crop} at {max_dom_pct:.1f}%", end="")
if max_dom_pct > 15:
    print("  ⚠ Exceeds 15% cap")
else:
    print("  ✓ Under 15%")

print(f"  Unique crops predicted: {unique_crops} / {len(le.classes_)}", end="")
if unique_crops >= 45:
    print("  ✓ At least 45")
else:
    print(f"  ⚠ Below 45 target")

# Confidence distribution
max_confs = geo_proba.max(axis=1) * 100
print(f"\n  Confidence distribution across {n_geo} environments:")
print(f"    Mean:   {max_confs.mean():.1f}%")
print(f"    Median: {np.median(max_confs):.1f}%")
print(f"    Max:    {max_confs.max():.1f}%")
print(f"    Min:    {max_confs.min():.1f}%")
pct_over90 = (max_confs > 90).sum() / len(max_confs) * 100
pct_over99 = (max_confs > 99).sum() / len(max_confs) * 100
print(f"    > 90%:  {pct_over90:.1f}% of predictions")
print(f"    > 99%:  {pct_over99:.1f}% of predictions")

# Build dominance test results for metadata
dominance_test_results = {
    "rice_dominance_pct": round(rice_pct, 2),
    "max_dominance_crop": max_dom_crop,
    "max_dominance_pct": round(max_dom_pct, 2),
    "unique_crops_predicted": unique_crops,
    "total_environments": n_geo,
    "zone_distribution": {
        "monsoon_heavy": n_monsoon,
        "semi_arid": n_semiarid,
        "moderate_plateau": n_plateau,
        "cool_region": n_cool,
    },
    "confidence_mean": round(float(max_confs.mean()), 2),
    "confidence_max": round(float(max_confs.max()), 2),
    "rice_under_5pct": rice_pct < 5,
    "max_under_15pct": max_dom_pct < 15,
    "unique_over_45": unique_crops >= 45,
}

# ── Metadata ─────────────────────────────────────────────────────────────
metadata = {
    "model_version": "2.2",
    "model_type": "CalibratedClassifierCV(RandomForestClassifier)",
    "calibration_used": True,
    "calibration_method": "sigmoid",
    "calibration_cv": 3,
    "n_estimators": 150,
    "max_depth": 25,
    "features": FEATURES,
    "soil_feature_added": True,
    "irrigation_feature_added": True,
    "dataset": DATASET_CSV,
    "dataset_hash": dataset_hash,
    "updated_dataset_hash": dataset_hash,
    "model_file_hash": model_hash,
    "top1_accuracy": round(accuracy, 6),
    "top3_accuracy": round(top3_accuracy, 6),
    "base_top1_accuracy": round(acc_base, 6),
    "base_top3_accuracy": round(top3_base, 6),
    "max_confidence_pct": round(max_conf, 2),
    "cv_mean": round(cv_scores.mean(), 6),
    "cv_std": round(cv_scores.std(), 6),
    "train_test_split": f"{int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}",
    "total_classes": int(len(le.classes_)),
    "classes": list(le.classes_),
    "total_samples": int(len(df)),
    "sklearn_version": sklearn.__version__,
    "numpy_version": np.__version__,
    "pandas_version": pd.__version__,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "random_state": RANDOM_STATE,
    "feature_importances": {feat: round(imp, 6) for feat, imp in importances.items()},
    "soil_feature_weight": round(float(soil_importance), 6),
    "irrigation_feature_weight": round(float(irrigation_importance), 6),
    "dominance_test_results": dominance_test_results,
    "note": (
        "v2.2: Gaussian synthetic data with ecological clustering, season, "
        "soil_type (strengthened), irrigation, asymmetric cross-cluster noise, "
        "CalibratedClassifierCV (sigmoid), realistic data imbalance. "
        "n_estimators=400, non-uniform geographic simulation."
    ),
}

with open(METADATA_FILE, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"        ✓ {METADATA_FILE}")

print("\n" + "=" * 70)
print("  TRAINING COMPLETE — All artifacts saved")
print("=" * 70)

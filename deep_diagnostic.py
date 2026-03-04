"""
Deep Model Diagnostic — Answers 10 Hard Questions about TC1 (Rice) Failure
==========================================================================
Loads the actual models and training data locally, traces TC1 input
through every stage, and answers each question with hard numbers.
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from collections import Counter

BASE = os.path.join(os.path.dirname(__file__), "Aiml")

# ── Helper to print section headers ──
def header(n, title):
    print(f"\n{'='*80}")
    print(f"  Q{n}: {title}")
    print(f"{'='*80}")

# ── TC1 Input ──
TC1 = {
    "N": 110, "P": 50, "K": 50,
    "temperature": 28, "humidity": 92,
    "ph": 6.3, "rainfall": 450,
    "season": 0,        # Kharif (inferred: temp>=28)
    "soil_type": 1,
    "irrigation": 0,
}

# ================================================================
# LOAD MODELS + DATA
# ================================================================
print("Loading models and data...")

# V6 Stacked Ensemble (soil model)
stacked = joblib.load(os.path.join(BASE, "stacked_ensemble_v6.joblib"))
le_v6 = joblib.load(os.path.join(BASE, "label_encoder_v6.joblib"))
cfg_v6 = joblib.load(os.path.join(BASE, "stacked_v6_config.joblib"))
features_v6 = cfg_v6["feature_names"]
temp_scaling = cfg_v6.get("temperature", 0.9)
crops_v6 = list(le_v6.classes_)

# Extended RF model
rf_model = joblib.load(os.path.join(BASE, "model_rf.joblib"))
le_rf = joblib.load(os.path.join(BASE, "label_encoder.joblib"))
features_rf = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "season", "soil_type", "irrigation"]
crops_rf = list(le_rf.classes_)

# Training dataset
dataset_file = os.path.join(BASE, "Crop_recommendation_v2.csv")
df = pd.read_csv(dataset_file)

# Metadata
with open(os.path.join(BASE, "training_metadata_v6.json")) as f:
    metadata = json.load(f)

# Agronomic constraints
from Aiml.app import CROP_AGRO_CONSTRAINTS, AGRONOMIC_PENALTY_MILD, AGRONOMIC_PENALTY_EXTREME

print(f"  Soil model: {len(crops_v6)} crops, features={features_v6}")
print(f"  Extended RF: {len(crops_rf)} crops")
print(f"  Dataset: {len(df)} rows, columns={list(df.columns)}")
print(f"  Crops in dataset: {df['label'].nunique()}")

# ================================================================
# Q1: RAW PROBABILITY DISTRIBUTION
# ================================================================
header(1, "RAW PROBABILITY DISTRIBUTION (Before Calibration)")

X_v6 = pd.DataFrame([TC1])[features_v6]

# Get raw base model predictions (before meta-learner)
base_preds = {}
for name in ["BalancedRF", "XGBoost", "LightGBM"]:
    fold_probs = np.mean(
        [m.predict_proba(X_v6)[0] for m in stacked["fold_models"][name]], axis=0
    )
    base_preds[name] = fold_probs

# Meta-learner prediction (before temperature scaling)
meta_features = np.hstack(list(base_preds.values())).reshape(1, -1)
meta_proba = stacked["meta_learner"].predict_proba(meta_features)[0]

# After temperature scaling
log_p = np.log(np.clip(meta_proba, 1e-10, 1.0))
scaled = log_p / temp_scaling
scaled -= scaled.max()
e = np.exp(scaled)
tempcal_proba = e / e.sum()

# Find rice, okra, maize indices
rice_idx = crops_v6.index("rice") if "rice" in crops_v6 else -1
okra_idx = crops_v6.index("okra") if "okra" in crops_v6 else -1
maize_idx = crops_v6.index("maize") if "maize" in crops_v6 else -1
brinjal_idx = crops_v6.index("brinjal") if "brinjal" in crops_v6 else -1

print("\n  --- Per-Base-Model Raw Probabilities ---")
for name in ["BalancedRF", "XGBoost", "LightGBM"]:
    p = base_preds[name]
    print(f"\n  {name}:")
    top10_idx = np.argsort(p)[-10:][::-1]
    for i in top10_idx:
        marker = ""
        if crops_v6[i] == "rice": marker = "  ← RICE"
        elif crops_v6[i] == "okra": marker = "  ← OKRA"
        elif crops_v6[i] == "maize": marker = "  ← MAIZE"
        elif crops_v6[i] == "brinjal": marker = "  ← BRINJAL"
        print(f"    {crops_v6[i]:20s} {p[i]*100:7.3f}%{marker}")

print("\n  --- Meta-Learner Output (BEFORE temperature scaling) ---")
top10_idx = np.argsort(meta_proba)[-10:][::-1]
for i in top10_idx:
    marker = ""
    if crops_v6[i] == "rice": marker = "  ← RICE"
    elif crops_v6[i] == "okra": marker = "  ← OKRA"
    elif crops_v6[i] == "maize": marker = "  ← MAIZE"
    elif crops_v6[i] == "brinjal": marker = "  ← BRINJAL"
    print(f"    {crops_v6[i]:20s} {meta_proba[i]*100:7.3f}%{marker}")

print(f"\n  --- After Temperature Scaling (T={temp_scaling}) ---")
top10_idx = np.argsort(tempcal_proba)[-10:][::-1]
for i in top10_idx:
    marker = ""
    if crops_v6[i] == "rice": marker = "  ← RICE"
    elif crops_v6[i] == "okra": marker = "  ← OKRA"
    elif crops_v6[i] == "maize": marker = "  ← MAIZE"
    elif crops_v6[i] == "brinjal": marker = "  ← BRINJAL"
    print(f"    {crops_v6[i]:20s} {tempcal_proba[i]*100:7.3f}%{marker}")

if rice_idx >= 0:
    print(f"\n  RICE raw probability (meta-learner): {meta_proba[rice_idx]*100:.4f}%")
    print(f"  RICE after temp-scaling: {tempcal_proba[rice_idx]*100:.4f}%")
    print(f"  RICE rank (raw): #{np.argsort(meta_proba)[::-1].tolist().index(rice_idx)+1}")
    print(f"  RICE rank (temp-scaled): #{np.argsort(tempcal_proba)[::-1].tolist().index(rice_idx)+1}")

# Extended RF raw probabilities
X_rf = pd.DataFrame([TC1])[features_rf]
rf_raw = rf_model.predict_proba(X_rf)[0]
rice_rf_idx = crops_rf.index("rice") if "rice" in crops_rf else -1
okra_rf_idx = crops_rf.index("okra") if "okra" in crops_rf else -1

print(f"\n  --- Extended RF Raw Probabilities (Top 10) ---")
top10_rf = np.argsort(rf_raw)[-10:][::-1]
for i in top10_rf:
    marker = ""
    if crops_rf[i] == "rice": marker = "  ← RICE"
    elif crops_rf[i] == "okra": marker = "  ← OKRA"
    elif crops_rf[i] == "maize": marker = "  ← MAIZE"
    elif crops_rf[i] == "brinjal": marker = "  ← BRINJAL"
    print(f"    {crops_rf[i]:20s} {rf_raw[i]*100:7.3f}%{marker}")

if rice_rf_idx >= 0:
    print(f"\n  RICE RF raw: {rf_raw[rice_rf_idx]*100:.4f}%")
    print(f"  RICE RF rank: #{np.argsort(rf_raw)[::-1].tolist().index(rice_rf_idx)+1}")


# ================================================================
# Q2: FEATURE IMPORTANCE RANKING
# ================================================================
header(2, "FEATURE IMPORTANCE RANKING")

fi = metadata.get("feature_importance", {})
sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)
print("\n  Feature Importance (V6 Stacked Ensemble):")
print(f"  {'Rank':>4s}  {'Feature':15s}  {'Importance':>12s}  {'Bar'}")
print(f"  {'----':>4s}  {'-------':15s}  {'----------':>12s}  {'---'}")
for rank, (feat, imp) in enumerate(sorted_fi, 1):
    bar = "█" * int(imp * 200)
    marker = " ← CRITICAL" if feat == "rainfall" else ""
    print(f"  {rank:>4d}  {feat:15s}  {imp:12.4f}      {bar}{marker}")

rainfall_rank = [f for f, _ in sorted_fi].index("rainfall") + 1 if "rainfall" in fi else -1
print(f"\n  Rainfall rank: #{rainfall_rank} out of {len(sorted_fi)} features")
print(f"  Rainfall importance: {fi.get('rainfall', 0):.4f}")
print(f"  Top feature (K): {sorted_fi[0][1]:.4f}")
print(f"  Rainfall / K ratio: {fi.get('rainfall', 0) / sorted_fi[0][1]:.2f}x")

# Also get RF feature importances if available
if hasattr(rf_model, 'feature_importances_'):
    rf_fi = dict(zip(features_rf, rf_model.feature_importances_))
    sorted_rf_fi = sorted(rf_fi.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Extended RF Feature Importance:")
    for rank, (feat, imp) in enumerate(sorted_rf_fi, 1):
        bar = "█" * int(imp * 200)
        marker = " ← CRITICAL" if feat == "rainfall" else ""
        print(f"  {rank:>4d}  {feat:15s}  {imp:12.4f}      {bar}{marker}")


# ================================================================
# Q3: DATASET DISTRIBUTION CHECK
# ================================================================
header(3, "DATASET DISTRIBUTION (Samples per Crop)")

label_col = "label"
crop_counts = df[label_col].value_counts()
print(f"\n  Total samples: {len(df)}")
print(f"  Unique crops: {crop_counts.shape[0]}")
print(f"\n  {'Crop':22s}  {'Count':>6s}  {'%':>6s}  {'Bar'}")
print(f"  {'----':22s}  {'-----':>6s}  {'----':>6s}  {'---'}")
for crop, count in crop_counts.items():
    pct = count / len(df) * 100
    bar = "█" * int(pct * 3)
    marker = ""
    if crop == "rice": marker = " ← RICE"
    elif crop == "okra": marker = " ← OKRA"
    elif crop == "brinjal": marker = " ← BRINJAL"
    elif crop == "maize": marker = " ← MAIZE"
    print(f"  {str(crop):22s}  {count:>6d}  {pct:5.2f}%  {bar}{marker}")

rice_count = crop_counts.get("rice", 0)
okra_count = crop_counts.get("okra", 0)
brinjal_count = crop_counts.get("brinjal", 0)
maize_count = crop_counts.get("maize", 0)

print(f"\n  RICE samples:    {rice_count}")
print(f"  OKRA samples:    {okra_count}")
print(f"  BRINJAL samples: {brinjal_count}")
print(f"  MAIZE samples:   {maize_count}")
print(f"  Okra/Rice ratio: {okra_count/max(rice_count,1):.2f}x")
print(f"  Imbalance ratio (max/min): {crop_counts.max()}/{crop_counts.min()} = {crop_counts.max()/max(crop_counts.min(),1):.2f}x")


# ================================================================
# Q4: RAINFALL DISTRIBUTION FOR RICE
# ================================================================
header(4, "RAINFALL DISTRIBUTION IN TRAINING DATA (Rice)")

rice_data = df[df[label_col] == "rice"]
if len(rice_data) > 0:
    rain_col = "rainfall"
    rice_rain = rice_data[rain_col]
    print(f"\n  Rice training samples: {len(rice_data)}")
    print(f"  Rice rainfall statistics:")
    print(f"    Min:    {rice_rain.min():.1f} mm")
    print(f"    Max:    {rice_rain.max():.1f} mm")
    print(f"    Mean:   {rice_rain.mean():.1f} mm")
    print(f"    Median: {rice_rain.median():.1f} mm")
    print(f"    Std:    {rice_rain.std():.1f} mm")
    print(f"    P25:    {rice_rain.quantile(0.25):.1f} mm")
    print(f"    P75:    {rice_rain.quantile(0.75):.1f} mm")
    print(f"    P90:    {rice_rain.quantile(0.90):.1f} mm")
    
    # What fraction of rice training data has rainfall >= 450?
    frac_above_450 = (rice_rain >= 450).mean()
    frac_above_400 = (rice_rain >= 400).mean()
    frac_below_200 = (rice_rain < 200).mean()
    print(f"\n    Fraction with rainfall >= 450mm: {frac_above_450:.1%}")
    print(f"    Fraction with rainfall >= 400mm: {frac_above_400:.1%}")
    print(f"    Fraction with rainfall < 200mm:  {frac_below_200:.1%}")
    
    # Histogram buckets
    bins = [0, 100, 200, 300, 400, 500, 600, 800, 1000, 1500, 2000, 3000, 5000]
    hist, _ = np.histogram(rice_rain, bins=bins)
    print(f"\n    Rainfall Distribution Histogram:")
    for i in range(len(hist)):
        lo, hi = bins[i], bins[i+1]
        bar = "█" * int(hist[i] / max(1, max(hist)) * 40)
        marker = " ← TC1=450mm" if lo <= 450 < hi else ""
        print(f"    [{lo:5.0f}-{hi:5.0f}mm): {hist[i]:4d}  {bar}{marker}")
    
    # Contrast with okra
    okra_data = df[df[label_col] == "okra"]
    if len(okra_data) > 0:
        okra_rain = okra_data[rain_col]
        print(f"\n  Okra rainfall statistics (for comparison):")
        print(f"    Mean:   {okra_rain.mean():.1f} mm")
        print(f"    Median: {okra_rain.median():.1f} mm")
        print(f"    Std:    {okra_rain.std():.1f} mm")
        print(f"    Fraction with rainfall around 400-500mm: {((okra_rain>=400)&(okra_rain<=500)).mean():.1%}")
else:
    print("\n  WARNING: No rice samples found!")


# ================================================================
# Q5: CORRELATION MATRIX
# ================================================================
header(5, "CORRELATION — RAINFALL vs CROP (Rice)")

# Create binary rice indicator
df_copy = df.copy()
df_copy["is_rice"] = (df_copy[label_col] == "rice").astype(int)
df_copy["is_okra"] = (df_copy[label_col] == "okra").astype(int)
df_copy["is_maize"] = (df_copy[label_col] == "maize").astype(int)
df_copy["is_brinjal"] = (df_copy[label_col] == "brinjal").astype(int)

features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
target_cols = ["is_rice", "is_okra", "is_maize", "is_brinjal"]

print("\n  Point-Biserial Correlation (feature vs crop indicator):")
print(f"\n  {'Feature':15s}  {'vs Rice':>10s}  {'vs Okra':>10s}  {'vs Maize':>10s}  {'vs Brinjal':>10s}")
print(f"  {'-------':15s}  {'-------':>10s}  {'-------':>10s}  {'--------':>10s}  {'----------':>10s}")
for feat in features:
    corrs = []
    for tc in target_cols:
        c = df_copy[[feat, tc]].corr().iloc[0, 1]
        corrs.append(c)
    bars = ["█"*int(abs(c)*50) if c > 0 else "" for c in corrs]
    print(f"  {feat:15s}  {corrs[0]:+10.4f}  {corrs[1]:+10.4f}  {corrs[2]:+10.4f}  {corrs[3]:+10.4f}")

# Full correlation of rainfall with each crop
print(f"\n  Rainfall correlation with ALL crops (top 10 + bottom 5):")
crop_rain_corrs = {}
for crop in df[label_col].unique():
    df_copy[f"is_{crop}"] = (df_copy[label_col] == crop).astype(int)
    c = df_copy[["rainfall", f"is_{crop}"]].corr().iloc[0, 1]
    crop_rain_corrs[crop] = c

sorted_crc = sorted(crop_rain_corrs.items(), key=lambda x: x[1], reverse=True)
print(f"\n  Top 10 (rainfall lovers):")
for i, (crop, c) in enumerate(sorted_crc[:10]):
    marker = " ← RICE" if crop == "rice" else ""
    print(f"    {i+1:3d}. {crop:22s}  r = {c:+.4f}{marker}")
print(f"\n  Bottom 5 (rainfall haters):")
for i, (crop, c) in enumerate(sorted_crc[-5:]):
    print(f"    {len(sorted_crc)-4+i:3d}. {crop:22s}  r = {c:+.4f}")


# ================================================================
# Q6: STRESS PENALTY INTERACTION
# ================================================================
header(6, "STRESS PENALTY — TC1 Input")

from Aiml.app import compute_stress_index, _compute_crop_stress_factor

canonical = {k: v for k, v in TC1.items() if k in features}
stress_idx, stress_per = compute_stress_index(canonical)
print(f"\n  Overall Stress Index: {stress_idx:.4f}")
print(f"  Threshold for high stress: 0.60")
print(f"  Stress active? {'YES — penalty applied' if stress_idx > 0.60 else 'NO — below threshold'}")
print(f"\n  Per-feature stress:")
for feat, val in sorted(stress_per.items(), key=lambda x: x[1], reverse=True):
    bar = "█" * int(val * 40)
    print(f"    {feat:15s}  {val:.4f}  {bar}")

# Per-crop stress for rice, okra, maize
for crop in ["rice", "okra", "maize", "brinjal"]:
    sf, sc = _compute_crop_stress_factor(crop, TC1)
    print(f"\n  {crop:12s} crop stress: factor={sf:.4f}, severe_count={sc}")


# ================================================================
# Q7: CALIBRATION CAP EFFECT
# ================================================================
header(7, "CALIBRATION CAP — Probability Compression")

# Show the effect of agronomic constraints + OOD + stress + caps
from Aiml.app import (
    apply_agronomic_constraints, compute_ood_dampening,
    validate_distribution, flatten_distribution,
    apply_stress_reduction, HARD_CONFIDENCE_CAP,
    OOD_DAMPEN_FACTOR, OOD_CAP_THRESHOLD, OOD_MAX_CONFIDENCE,
)

# Raw proba
raw = tempcal_proba.copy()

# Step 1: Agronomic constraints
constrained, violations = apply_agronomic_constraints(raw, crops_v6, TC1, le_v6)
# Step 2: OOD
ood_warnings = validate_distribution(canonical, "soil")
ood_mult, ood_cap, ood_reason = compute_ood_dampening(ood_warnings)
# Step 3: Stress flattening
flattened = flatten_distribution(constrained, stress_idx)

print(f"\n  OOD warnings: {len(ood_warnings)}")
for w in ood_warnings:
    print(f"    {w['field']}: {w['value']} outside [{w['training_range'][0]}, {w['training_range'][1]}]")
print(f"  OOD multiplier: {ood_mult:.3f}")
print(f"  OOD cap: {ood_cap:.2f}")
print(f"  HARD_CONFIDENCE_CAP: {HARD_CONFIDENCE_CAP}")

# Show rice through the pipeline
if rice_idx >= 0:
    print(f"\n  RICE probability at each stage:")
    print(f"    Raw (temp-scaled):          {raw[rice_idx]*100:.4f}%")
    print(f"    After agronomic penalty:    {constrained[rice_idx]*100:.4f}%")
    print(f"    After stress flattening:    {flattened[rice_idx]*100:.4f}%")
    
    top_adj = float(flattened[rice_idx])
    dampened = top_adj * ood_mult
    dampened = min(dampened, ood_cap)
    dampened_stress, _ = apply_stress_reduction(dampened, stress_idx)
    final = min(dampened_stress, HARD_CONFIDENCE_CAP)
    print(f"    After OOD dampening:        {dampened*100:.4f}%")
    print(f"    After stress reduction:     {dampened_stress*100:.4f}%")
    print(f"    After HARD CAP (85%):       {final*100:.4f}%")

# Show same for okra
if okra_idx >= 0:
    print(f"\n  OKRA probability at each stage:")
    print(f"    Raw (temp-scaled):          {raw[okra_idx]*100:.4f}%")
    print(f"    After agronomic penalty:    {constrained[okra_idx]*100:.4f}%")
    print(f"    After stress flattening:    {flattened[okra_idx]*100:.4f}%")

# Agronomic violations
print(f"\n  Agronomic violations for TC1 input ({len(violations)} crops violated):")
for crop in ["rice", "okra", "maize", "brinjal"]:
    if crop in violations:
        print(f"    {crop}: {violations[crop]}")
    else:
        print(f"    {crop}: NO VIOLATIONS ✓")


# ================================================================
# Q8: ENSEMBLE WEIGHTING
# ================================================================
header(8, "ENSEMBLE WEIGHTING — Hybrid Model")

# Hybrid weighting logic
soil_max = float(np.max(tempcal_proba))
rf_max = float(np.max(rf_raw))

CONFIDENCE_TH = 0.3
V6_W = 0.7
RF_W = 0.3

if soil_max > CONFIDENCE_TH and rf_max > CONFIDENCE_TH:
    sw, ew = V6_W, RF_W
    logic = "both confident → default weights"
elif soil_max > CONFIDENCE_TH:
    sw, ew = 0.85, 0.15
    logic = "only soil confident"
elif rf_max > CONFIDENCE_TH:
    sw, ew = 0.15, 0.85
    logic = "only RF confident"
else:
    sw, ew = 0.5, 0.5
    logic = "neither confident"

print(f"\n  Soil model max confidence: {soil_max*100:.2f}%")
print(f"  Extended RF max confidence: {rf_max*100:.2f}%")
print(f"  Confidence threshold: {CONFIDENCE_TH*100:.0f}%")
print(f"  Logic: {logic}")
print(f"  Soil weight: {sw:.2f}")
print(f"  RF weight:   {ew:.2f}")

# Soil top-3 crops
soil_top3 = np.argsort(tempcal_proba)[-3:][::-1]
rf_top3 = np.argsort(rf_raw)[-3:][::-1]

print(f"\n  Soil Model Top-3:")
for i in soil_top3:
    print(f"    {crops_v6[i]:22s} {tempcal_proba[i]*100:.3f}%")
print(f"\n  RF Model Top-3:")
for i in rf_top3:
    print(f"    {crops_rf[i]:22s} {rf_raw[i]*100:.3f}%")

# Show where rice ranks in each
print(f"\n  Rice rank in Soil: #{np.argsort(tempcal_proba)[::-1].tolist().index(rice_idx)+1}")
print(f"  Rice rank in RF:   #{np.argsort(rf_raw)[::-1].tolist().index(rice_rf_idx)+1}")


# ================================================================
# Q9: FEASIBILITY FILTER — Did Rice Pass?
# ================================================================
header(9, "FEASIBILITY FILTER — Rice Check")

rice_constraints = CROP_AGRO_CONSTRAINTS.get("rice", {})
print(f"\n  Rice agronomic constraints:")
for key, val in rice_constraints.items():
    print(f"    {key}: {val}")

print(f"\n  TC1 Input values:")
print(f"    Temperature: {TC1['temperature']}°C")
print(f"    pH: {TC1['ph']}")
print(f"    Rainfall: {TC1['rainfall']}mm")
print(f"    Humidity: {TC1['humidity']}%")

# Check each gate
t_min, t_max = rice_constraints["temp_range"]
ph_min, ph_max = rice_constraints["ph_range"]
r_min, r_max = rice_constraints["rainfall_range"]
h_min, h_max = rice_constraints["humidity_range"]

checks = []
# Temp: ±3°C margin
if TC1["temperature"] < t_min - 3:
    checks.append(f"FAIL: temp {TC1['temperature']} < {t_min}-3 = {t_min-3}")
elif TC1["temperature"] > t_max + 3:
    checks.append(f"FAIL: temp {TC1['temperature']} > {t_max}+3 = {t_max+3}")
else:
    checks.append(f"PASS: temp {TC1['temperature']} in [{t_min-3}, {t_max+3}]")

# pH: ±0.5 margin
if TC1["ph"] < ph_min - 0.5 or TC1["ph"] > ph_max + 0.5:
    checks.append(f"FAIL: pH {TC1['ph']} outside [{ph_min-0.5}, {ph_max+0.5}]")
else:
    checks.append(f"PASS: pH {TC1['ph']} in [{ph_min-0.5}, {ph_max+0.5}]")

# Rainfall: < 30% of min
if r_min > 0 and TC1["rainfall"] < r_min * 0.3:
    checks.append(f"FAIL: rainfall {TC1['rainfall']} < {r_min*0.3:.0f} (30% of min {r_min})")
else:
    checks.append(f"PASS: rainfall {TC1['rainfall']} >= {r_min*0.3:.0f} (30% of min {r_min})")

# Also check soft constraints
print(f"\n  Hard Feasibility Gate:")
for c in checks:
    status = "✓" if c.startswith("PASS") else "✗"
    print(f"    {status} {c}")

print(f"\n  Soft Constraint Check (agronomic penalty):")
if TC1["rainfall"] < r_min:
    print(f"    ⚠ Rainfall {TC1['rainfall']}mm < min {r_min}mm → MILD penalty ({AGRONOMIC_PENALTY_MILD}x)")
    print(f"      Rice needs [{r_min}-{r_max}]mm, input is {r_min - TC1['rainfall']}mm below minimum!")
elif TC1["rainfall"] > r_max:
    print(f"    ⚠ Rainfall {TC1['rainfall']}mm > max {r_max}mm → MILD penalty")
else:
    print(f"    ✓ Rainfall {TC1['rainfall']}mm in [{r_min}, {r_max}]mm — no penalty")

if TC1["humidity"] < h_min or TC1["humidity"] > h_max:
    print(f"    ⚠ Humidity {TC1['humidity']}% outside [{h_min}, {h_max}]% → MILD penalty")
else:
    print(f"    ✓ Humidity {TC1['humidity']}% in [{h_min}, {h_max}]% — no penalty")


# ================================================================
# Q10: TRAINING OBJECTIVE
# ================================================================
header(10, "TRAINING OBJECTIVE & HYPERPARAMETERS")

perf = metadata.get("performance", {})
arch = metadata.get("architecture", {})
cal = metadata.get("calibration", {})

print(f"\n  Architecture: {arch.get('type')}")
print(f"  Base models: {', '.join(arch.get('base_models', []))}")
print(f"  Meta-learner: {arch.get('meta_learner')}")
print(f"  N folds: {arch.get('n_folds')}")
print(f"  N estimators per base: {arch.get('n_estimators_per_base')}")
print(f"\n  Training Metrics (what was optimized):")
print(f"    Top-1 Accuracy:     {perf.get('top1_accuracy', 'N/A')}")
print(f"    Top-3 Accuracy:     {perf.get('top3_accuracy', 'N/A')}")
print(f"    Macro F1:           {perf.get('macro_f1', 'N/A')}")
print(f"    Weighted F1:        {perf.get('weighted_f1', 'N/A')}")
print(f"    ECE:                {perf.get('ece', 'N/A')}")
print(f"    Log Loss:           {perf.get('log_loss', 'N/A')}")
print(f"\n  Calibration:")
print(f"    Temperature: {cal.get('temperature', 'N/A')}")
print(f"    ECE before:  {cal.get('ece_before', 'N/A')}")
print(f"    ECE after:   {cal.get('ece_after', 'N/A')}")
print(f"\n  Removed (good):")
for r in arch.get("removed", []):
    print(f"    ✓ {r}")

# Check if BalancedRF was actually balanced
print(f"\n  CV Scores per base model:")
cv = metadata.get("cv_scores", {})
for model, scores in cv.items():
    print(f"    {model}: mean={scores['mean']:.4f} ± {scores['std']:.4f}")


# ================================================================
# COMPREHENSIVE SUMMARY & ROOT CAUSE
# ================================================================
print(f"\n\n{'='*80}")
print(f"  COMPREHENSIVE ROOT CAUSE ANALYSIS")
print(f"{'='*80}")

print(f"""
  ┌─────────────────────────────────────────────────────────────────────┐
  │  TC1 INPUT: N=110, P=50, K=50, T=28°C, H=92%, pH=6.3, R=450mm   │
  │  EXPECTED: Rice #1   |   ACTUAL: Okra #1                         │
  └─────────────────────────────────────────────────────────────────────┘

  ROOT CAUSE CHAIN:
""")

# Determine the key issue
if rice_idx >= 0:
    rice_raw_rank = np.argsort(tempcal_proba)[::-1].tolist().index(rice_idx) + 1
    rice_raw_pct = tempcal_proba[rice_idx] * 100
    okra_raw_pct = tempcal_proba[okra_idx] * 100 if okra_idx >= 0 else 0
    
    if rice_raw_rank > 3:
        print(f"  1. TRAINING ISSUE: Rice raw prob = {rice_raw_pct:.2f}% (rank #{rice_raw_rank})")
        print(f"     → Rice was NEVER in the model's top candidates for this input")
        print(f"     → No amount of calibration/filtering can fix this")
    else:
        print(f"  1. Rice raw prob = {rice_raw_pct:.2f}% (rank #{rice_raw_rank})")
        print(f"     → Rice WAS in top candidates but lost during processing")
    
    if rice_count > 0:
        rice_rain_mean = rice_data["rainfall"].mean()
        if rice_rain_mean < 300 or TC1["rainfall"] > rice_data["rainfall"].quantile(0.9):
            print(f"\n  2. DATASET ISSUE: Rice training rainfall mean={rice_rain_mean:.0f}mm")
            print(f"     → TC1 input (450mm) may be {'typical' if frac_above_450 > 0.3 else 'unusual'} for rice in training data")
        else:
            print(f"\n  2. Rice training rainfall mean={rice_rain_mean:.0f}mm — dataset looks OK")
    
    print(f"\n  3. RAINFALL IMPORTANCE: Rank #{rainfall_rank}, weight={fi.get('rainfall',0):.4f}")
    if rainfall_rank > 3:
        print(f"     → Rainfall is NOT in top 3 features!")
        print(f"     → Model relies more on K ({sorted_fi[0][1]:.4f}), N ({sorted_fi[1][1]:.4f}), P ({sorted_fi[2][1]:.4f})")
    
    rice_rain_constraint = CROP_AGRO_CONSTRAINTS["rice"]["rainfall_range"]
    if TC1["rainfall"] < rice_rain_constraint[0]:
        print(f"\n  4. CONSTRAINT MISMATCH: Rice needs {rice_rain_constraint[0]}-{rice_rain_constraint[1]}mm")
        print(f"     → TC1 input 450mm < min {rice_rain_constraint[0]}mm!")
        print(f"     → Rice gets AGRONOMIC PENALTY (×{AGRONOMIC_PENALTY_MILD})")
        print(f"     → THIS IS THE CRITICAL ISSUE")
    else:
        print(f"\n  4. Rice rainfall constraint [{rice_rain_constraint[0]}-{rice_rain_constraint[1]}mm] — 450mm {'IN RANGE' if rice_rain_constraint[0] <= 450 <= rice_rain_constraint[1] else 'outside'}")

print(f"\n{'='*80}")
print(f"  Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}")

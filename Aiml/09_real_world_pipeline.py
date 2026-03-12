"""
Crop Recommendation System — Real-World Data Pipeline
======================================================

Replaces synthetic v2.2 dataset with real district-level agricultural data.

Sources:
  1. ICRISAT-District_Level_Data.csv   (district × year × crop yield/area/production)
  2. data_core.csv                     (crop × soil × NPK × temperature × humidity)
  3. temperature.csv                   (year × annual/seasonal temperature)
  4. rainfall.csv                      (year × annual/seasonal/monthly rainfall)
  5. Crop_recommendation.csv           (crop × NPK × temp × humidity × ph × rainfall)

Pipeline:
  STEP 1 — Analyze all CSV files
  STEP 2 — Clean datasets
  STEP 3 — Merge datasets
  STEP 4 — Convert to ML-ready format
  STEP 5 — Train RandomForestClassifier
  STEP 6 — Compare with synthetic v2.2
  STEP 7 — Save artifacts

Outputs:
  real_world_merged_dataset.csv
  real_world_ml_dataset.csv
  model_real_world.joblib
  label_encoder_real.joblib
  training_metadata_real.json
"""

import hashlib
import json
import logging
import os
import sys
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
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("real_world_pipeline")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

ICRISAT_CSV       = "ICRISAT-District_Level_Data.csv"
DATA_CORE_CSV     = "data_core.csv"
TEMPERATURE_CSV   = "temperature.csv"
RAINFALL_CSV      = "rainfall.csv"
CROP_REC_CSV      = "Crop_recommendation.csv"

MERGED_CSV        = "real_world_merged_dataset.csv"
ML_CSV            = "real_world_ml_dataset.csv"
MODEL_FILE        = "model_real_world.joblib"
ENCODER_FILE      = "label_encoder_real.joblib"
METADATA_FILE     = "training_metadata_real.json"
CONFMAT_FILE      = "confusion_matrix_real.png"

SYNTHETIC_META    = "training_metadata.json"

RANDOM_STATE      = 42

# ── Crop mapping: ICRISAT column prefix → standardised crop name ─────────
ICRISAT_CROP_MAP = {
    "RICE":                     "rice",
    "WHEAT":                    "wheat",
    "MAIZE":                    "maize",
    "BARLEY":                   "barley",
    "SORGHUM":                  "sorghum",
    "PEARL MILLET":             "pearl_millet",
    "FINGER MILLET":            "finger_millet",
    "CHICKPEA":                 "chickpea",
    "PIGEONPEA":                "pigeonpea",
    "GROUNDNUT":                "groundnut",
    "SESAMUM":                  "sesamum",
    "RAPESEED AND MUSTARD":     "mustard",
    "SAFFLOWER":                "safflower",
    "CASTOR":                   "castor",
    "LINSEED":                  "linseed",
    "SUNFLOWER":                "sunflower",
    "SOYABEAN":                 "soybean",
    "SUGARCANE":                "sugarcane",
    "COTTON":                   "cotton",
    "POTATOES":                 "potato",
    "ONION":                    "onion",
}

# ── Map ICRISAT crops → data_core "Crop Type" for NPK lookup ────────────
CROP_TO_DATACORE = {
    "rice":           "Paddy",
    "wheat":          "Wheat",
    "maize":          "Maize",
    "barley":         "Barley",
    "sorghum":        "Millets",
    "pearl_millet":   "Millets",
    "finger_millet":  "Millets",
    "chickpea":       "Pulses",
    "pigeonpea":      "Pulses",
    "groundnut":      "Ground Nuts",
    "sesamum":        "Oil seeds",
    "mustard":        "Oil seeds",
    "safflower":      "Oil seeds",
    "castor":         "Oil seeds",
    "linseed":        "Oil seeds",
    "sunflower":      "Oil seeds",
    "soybean":        "Oil seeds",
    "sugarcane":      "Sugarcane",
    "cotton":         "Cotton",
    "potato":         "Paddy",      # approximate — root crop, use paddy's NPK
    "onion":          "Paddy",      # approximate
}

# ── Map ICRISAT crops → Crop_recommendation "label" for pH/humidity ──────
CROP_TO_CROPREC = {
    "rice":       "rice",
    "maize":      "maize",
    "chickpea":   "chickpea",
    "pigeonpea":  "pigeonpeas",
    "cotton":     "cotton",
    "lentil":     "lentil",
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def sha256_short(data: bytes, length: int = 16) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def section(title, step=None):
    sep = "═" * 70
    prefix = f"STEP {step} — " if step else ""
    log.info("")
    log.info(sep)
    log.info(f"  {prefix}{title}")
    log.info(sep)


def sub(msg):
    log.info(f"  ── {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: ANALYZE ALL CSV FILES
# ═══════════════════════════════════════════════════════════════════════════

def step1_analyze():
    section("ANALYZE ALL CSV FILES", 1)

    files = {
        "ICRISAT":           ICRISAT_CSV,
        "data_core":         DATA_CORE_CSV,
        "temperature":       TEMPERATURE_CSV,
        "rainfall":          RAINFALL_CSV,
        "Crop_recommendation": CROP_REC_CSV,
    }

    loaded = {}
    for name, path in files.items():
        if not os.path.exists(path):
            log.warning(f"  {name:25s}: FILE NOT FOUND — {path}")
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
        except Exception:
            df = pd.read_csv(path, encoding="latin-1", low_memory=False)
        loaded[name] = df
        log.info(f"  {name:25s}: {df.shape[0]:>7,} rows × {df.shape[1]:>3} cols")

    # Identify contents
    sub("Content identification:")
    if "ICRISAT" in loaded:
        log.info("    ICRISAT  → Crop production/yield/area (wide format), State, District, Year")
    if "data_core" in loaded:
        log.info("    data_core → NPK, Soil Type, Temperature, Humidity, Moisture, Crop Type")
    if "temperature" in loaded:
        log.info("    temperature → Annual/seasonal temperature by year (national level)")
    if "rainfall" in loaded:
        log.info("    rainfall → Monthly/annual rainfall by year (national level)")
    if "Crop_recommendation" in loaded:
        log.info("    Crop_recommendation → NPK, temp, humidity, ph, rainfall, crop label")

    # Common keys
    sub("Common keys detected:")
    log.info("    ICRISAT ↔ temperature/rainfall:  YEAR")
    log.info("    ICRISAT ↔ data_core:             Crop name mapping (no direct key)")
    log.info("    ICRISAT ↔ Crop_recommendation:   Crop name mapping (partial)")
    log.info("    data_core ↔ Crop_recommendation: Crop name mapping (partial)")

    return loaded


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: CLEAN DATASETS
# ═══════════════════════════════════════════════════════════════════════════

def step2_clean(loaded: dict):
    section("CLEAN DATASETS", 2)
    cleaned = {}

    # ── 2.1 ICRISAT: Melt wide → long ───────────────────────────────────
    sub("Cleaning ICRISAT (wide → long melt)")
    if "ICRISAT" in loaded:
        df = loaded["ICRISAT"].copy()
        before = len(df)
        df = df.drop_duplicates()
        log.info(f"    Duplicates removed: {before - len(df)}")

        # Melt: for each crop, extract AREA, PRODUCTION, YIELD (vectorised)
        frames = []
        for icrisat_name, std_name in ICRISAT_CROP_MAP.items():
            area_col = f"{icrisat_name} AREA (1000 ha)"
            prod_col = f"{icrisat_name} PRODUCTION (1000 tons)"
            yield_col = f"{icrisat_name} YIELD (Kg per ha)"

            missing_cols = [c for c in [area_col, prod_col, yield_col]
                           if c not in df.columns]
            if missing_cols:
                log.warning(f"    Missing columns for {icrisat_name}: {missing_cols}")
                if area_col not in df.columns and yield_col not in df.columns:
                    continue

            sub_df = pd.DataFrame({
                "state":      df["State Name"].str.strip().str.lower(),
                "district":   df["Dist Name"].str.strip().str.lower(),
                "year":       df["Year"].astype(int),
                "crop":       std_name,
                "area":       df[area_col].values if area_col in df.columns else np.nan,
                "production": df[prod_col].values if prod_col in df.columns else np.nan,
                "yield":      df[yield_col].values if yield_col in df.columns else np.nan,
            })

            # Replace -1 sentinel with NaN
            for col in ["area", "production", "yield"]:
                sub_df.loc[sub_df[col] == -1, col] = np.nan

            # Drop rows where all crop metrics are NaN
            sub_df = sub_df.dropna(subset=["area", "production", "yield"], how="all")
            # Drop rows where area and production are both 0 or NaN
            mask_skip = (
                (sub_df["area"].fillna(0) == 0) &
                (sub_df["production"].fillna(0) == 0)
            )
            sub_df = sub_df[~mask_skip]

            frames.append(sub_df)

        icrisat_long = pd.concat(frames, ignore_index=True)
        before = len(icrisat_long)
        # Drop rows with NaN yield (critical field)
        before = len(icrisat_long)
        icrisat_long = icrisat_long.dropna(subset=["yield"])
        log.info(f"    Melted: {before:,} rows → {len(icrisat_long):,} after dropping NaN yield")

        # Remove unrealistic yields
        icrisat_long = icrisat_long[icrisat_long["yield"] > 0]
        log.info(f"    After removing yield ≤ 0: {len(icrisat_long):,} rows")

        # Stats
        log.info(f"    States: {icrisat_long['state'].nunique()}")
        log.info(f"    Districts: {icrisat_long['district'].nunique()}")
        log.info(f"    Crops: {icrisat_long['crop'].nunique()} — {sorted(icrisat_long['crop'].unique())}")
        log.info(f"    Years: {icrisat_long['year'].min()}–{icrisat_long['year'].max()}")

        cleaned["icrisat"] = icrisat_long
    else:
        log.warning("    ICRISAT not loaded — skipping")

    # ── 2.2 Temperature ─────────────────────────────────────────────────
    sub("Cleaning temperature.csv")
    if "temperature" in loaded:
        df = loaded["temperature"].copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={"annual": "temperature"})
        df = df.drop_duplicates(subset=["year"])
        df = df.dropna(subset=["year", "temperature"])
        log.info(f"    Rows: {len(df)}, Years: {df['year'].min()}–{df['year'].max()}")
        log.info(f"    Temp range: {df['temperature'].min():.1f}–{df['temperature'].max():.1f} °C")
        # Keep seasonal columns for potential enrichment
        cleaned["temperature"] = df
    else:
        log.warning("    temperature.csv not loaded")

    # ── 2.3 Rainfall ────────────────────────────────────────────────────
    sub("Cleaning rainfall.csv")
    if "rainfall" in loaded:
        df = loaded["rainfall"].copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={"ann": "rainfall"})
        df = df.drop_duplicates(subset=["year"])
        df = df.dropna(subset=["year", "rainfall"])
        log.info(f"    Rows: {len(df)}, Years: {df['year'].min()}–{df['year'].max()}")
        log.info(f"    Rainfall range: {df['rainfall'].min():.1f}–{df['rainfall'].max():.1f} mm")
        # Keep seasonal columns
        cleaned["rainfall"] = df
    else:
        log.warning("    rainfall.csv not loaded")

    # ── 2.4 data_core ───────────────────────────────────────────────────
    sub("Cleaning data_core.csv")
    if "data_core" in loaded:
        df = loaded["data_core"].copy()
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df = df.rename(columns={
            "temparature": "temperature",
            "nitrogen":    "n",
            "phosphorous": "p",
            "potassium":   "k",
            "soil_type":   "soil_type",
            "crop_type":   "crop_type",
        })
        before = len(df)
        df = df.drop_duplicates()
        df = df.dropna(subset=["crop_type", "n", "p", "k"])
        log.info(f"    Rows: {before} → {len(df)} after cleaning")
        log.info(f"    Crop types: {sorted(df['crop_type'].unique())}")
        log.info(f"    Soil types: {sorted(df['soil_type'].unique())}")

        # Build NPK + humidity lookup per crop type
        crop_npk = df.groupby("crop_type").agg({
            "n": "mean", "p": "mean", "k": "mean",
            "temperature": "mean", "humidity": "mean",
            "moisture": "mean",
        }).round(2)
        log.info(f"    NPK lookup (per crop type):")
        for ct, row in crop_npk.iterrows():
            log.info(f"      {ct:15s}: N={row['n']:5.1f}  P={row['p']:5.1f}  K={row['k']:5.1f}  "
                     f"Temp={row['temperature']:5.1f}  Hum={row['humidity']:5.1f}")

        # Build soil distribution per crop type
        soil_dist = {}
        for ct, group in df.groupby("crop_type"):
            vc = group["soil_type"].value_counts(normalize=True)
            soil_dist[ct] = dict(zip(vc.index.tolist(), vc.values.tolist()))
        log.info(f"    Soil distribution per crop type computed")

        cleaned["data_core"] = df
        cleaned["npk_lookup"] = crop_npk
        cleaned["soil_lookup"] = soil_dist
    else:
        log.warning("    data_core.csv not loaded")

    # ── 2.5 Crop_recommendation ─────────────────────────────────────────
    sub("Cleaning Crop_recommendation.csv")
    if "Crop_recommendation" in loaded:
        df = loaded["Crop_recommendation"].copy()
        df.columns = [c.strip().lower() for c in df.columns]
        before = len(df)
        df = df.drop_duplicates()
        df = df.dropna()
        log.info(f"    Rows: {before} → {len(df)} after cleaning")
        log.info(f"    Labels: {df['label'].nunique()} — {sorted(df['label'].unique())}")

        # Build feature lookup per crop label
        crop_feat = df.groupby("label").agg({
            "n": "mean", "p": "mean", "k": "mean",
            "temperature": "mean", "humidity": "mean",
            "ph": "mean", "rainfall": "mean",
        }).round(2)

        cleaned["crop_rec"] = df
        cleaned["crop_rec_lookup"] = crop_feat
    else:
        log.warning("    Crop_recommendation.csv not loaded")

    return cleaned


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: MERGE DATASETS
# ═══════════════════════════════════════════════════════════════════════════

def step3_merge(cleaned: dict):
    section("MERGE DATASETS", 3)

    if "icrisat" not in cleaned:
        log.error("  ICRISAT data required for merge — aborting")
        sys.exit(1)

    merged = cleaned["icrisat"].copy()
    log.info(f"  Base dataset (ICRISAT long): {len(merged):,} rows")

    # ── 3.1 Join temperature by year ────────────────────────────────────
    sub("Joining temperature by year")
    if "temperature" in cleaned:
        temp_df = cleaned["temperature"][["year", "temperature"]].copy()
        before = len(merged)
        merged = merged.merge(temp_df, on="year", how="left")
        n_matched = merged["temperature"].notna().sum()
        log.info(f"    Matched: {n_matched:,} / {len(merged):,} rows")

        # Also join seasonal temps for enrichment
        temp_full = cleaned["temperature"].copy()
        if "jun-sep" in temp_full.columns:
            merged = merged.merge(
                temp_full[["year", "jun-sep", "oct-dec", "jan-feb", "mar-may"]],
                on="year", how="left"
            )
            log.info(f"    Seasonal temperature columns added")
    else:
        log.warning("    No temperature data available")
        merged["temperature"] = np.nan

    # ── 3.2 Join rainfall by year ───────────────────────────────────────
    sub("Joining rainfall by year")
    if "rainfall" in cleaned:
        rain_df = cleaned["rainfall"][["year", "rainfall"]].copy()
        merged = merged.merge(rain_df, on="year", how="left")
        n_matched = merged["rainfall"].notna().sum()
        log.info(f"    Matched: {n_matched:,} / {len(merged):,} rows")

        # Seasonal rainfall
        rain_full = cleaned["rainfall"].copy()
        if "jun-sep" in rain_full.columns:
            merged = merged.merge(
                rain_full[["year", "jun-sep", "oct-dec"]].rename(
                    columns={"jun-sep": "rain_monsoon", "oct-dec": "rain_postmonsoon"}
                ),
                on="year", how="left"
            )
            log.info(f"    Seasonal rainfall columns added")
    else:
        log.warning("    No rainfall data available")
        merged["rainfall"] = np.nan

    # ── 3.3 Join NPK from data_core (by crop mapping) ──────────────────
    sub("Joining NPK from data_core (crop-type averages)")
    if "npk_lookup" in cleaned:
        npk = cleaned["npk_lookup"]

        # Vectorised: map crop → data_core type, then lookup NPK
        merged["_dc_type"] = merged["crop"].map(CROP_TO_DATACORE)

        for col in ["n", "p", "k", "humidity", "moisture"]:
            lookup = npk[col].to_dict()   # {crop_type: value}
            merged[col] = merged["_dc_type"].map(lookup)

        merged = merged.drop(columns=["_dc_type"])
        n_with_npk = merged["n"].notna().sum()
        log.info(f"    Rows with NPK data: {n_with_npk:,} / {len(merged):,}")
    else:
        log.warning("    No NPK lookup available")
        for col in ["n", "p", "k", "humidity", "moisture"]:
            merged[col] = np.nan

    # ── 3.4 Join pH from Crop_recommendation (by crop mapping) ──────────
    sub("Joining pH from Crop_recommendation (crop-label averages)")
    if "crop_rec_lookup" in cleaned:
        cr = cleaned["crop_rec_lookup"]
        # Vectorised: map crop → Crop_recommendation label → pH
        ph_lookup = {std: cr.loc[label, "ph"]
                     for std, label in CROP_TO_CROPREC.items()
                     if label in cr.index}
        merged["ph"] = merged["crop"].map(ph_lookup)
        n_with_ph = merged["ph"].notna().sum()
        log.info(f"    Rows with pH: {n_with_ph:,} / {len(merged):,}")

        # Fill missing pH with global median from Crop_recommendation
        if "crop_rec" in cleaned:
            global_ph = cleaned["crop_rec"]["ph"].median()
            before_na = merged["ph"].isna().sum()
            merged["ph"] = merged["ph"].fillna(global_ph)
            log.info(f"    Filled {before_na:,} missing pH with global median ({global_ph:.2f})")
    else:
        log.warning("    No pH lookup available")
        merged["ph"] = 6.5  # reasonable default

    # ── 3.5 Assign soil_type from data_core distribution ────────────────
    sub("Assigning soil_type from data_core distribution")
    if "soil_lookup" in cleaned:
        np.random.seed(RANDOM_STATE)
        soil_map_encode = {"Sandy": 0, "Loamy": 1, "Clayey": 2, "Black": 2, "Red": 0}

        # Pre-compute soil choice per crop (vectorised via numpy)
        dc_types = merged["crop"].map(CROP_TO_DATACORE)
        soil_vals = np.ones(len(merged), dtype=int)  # default loamy

        for dc_type in dc_types.dropna().unique():
            if dc_type in cleaned["soil_lookup"]:
                dist = cleaned["soil_lookup"][dc_type]
                soil_names = list(dist.keys())
                soil_probs = list(dist.values())
                mask = dc_types == dc_type
                n = mask.sum()
                chosen = np.random.choice(soil_names, size=n, p=soil_probs)
                encoded = np.array([soil_map_encode.get(s, 1) for s in chosen])
                soil_vals[mask.values] = encoded

        merged["soil_type"] = soil_vals
        log.info(f"    Soil distribution: {Counter(soil_vals.tolist())}")
    else:
        merged["soil_type"] = 1

    # ── 3.6 Assign irrigation (heuristic from crop type) ────────────────
    sub("Assigning irrigation (crop-based heuristic)")
    np.random.seed(RANDOM_STATE + 1)
    irrig_probs = {
        "rice": 0.85, "wheat": 0.80, "sugarcane": 0.90, "potato": 0.75,
        "onion": 0.70, "cotton": 0.60, "maize": 0.40, "barley": 0.30,
        "soybean": 0.20, "groundnut": 0.15, "mustard": 0.20,
        "chickpea": 0.15, "pigeonpea": 0.10, "linseed": 0.10,
        "sesamum": 0.08, "castor": 0.10, "safflower": 0.10,
        "sunflower": 0.15, "sorghum": 0.10, "pearl_millet": 0.05,
        "finger_millet": 0.08,
    }
    # Vectorised
    crop_probs = merged["crop"].map(irrig_probs).fillna(0.3).values
    merged["irrigation"] = (np.random.random(len(merged)) < crop_probs).astype(int)
    log.info(f"    Irrigation distribution: {Counter(merged['irrigation'].tolist())}")

    # ── 3.7 Assign season (from crop knowledge) ────────────────────────
    sub("Assigning season (crop-based)")
    season_map = {
        "rice": 0, "maize": 0, "sorghum": 0, "pearl_millet": 0,
        "finger_millet": 0, "cotton": 0, "groundnut": 0, "sesamum": 0,
        "soybean": 0, "sugarcane": 0, "castor": 0, "pigeonpea": 0,
        "wheat": 1, "barley": 1, "chickpea": 1, "mustard": 1,
        "safflower": 1, "linseed": 1, "sunflower": 1,
        "potato": 1, "onion": 2,
    }
    merged["season"] = merged["crop"].map(season_map).fillna(0).astype(int)
    log.info(f"    Season distribution: {Counter(merged['season'].tolist())}")

    # ── 3.8 Remove rows with missing critical values ───────────────────
    sub("Removing rows with missing critical values")
    critical = ["crop", "yield", "temperature", "rainfall", "n", "p", "k"]
    before = len(merged)
    for col in critical:
        if col in merged.columns:
            na_count = merged[col].isna().sum()
            if na_count > 0:
                log.info(f"    Dropping {na_count:,} rows with NaN {col}")
                merged = merged.dropna(subset=[col])
    log.info(f"    Rows: {before:,} → {len(merged):,}")

    # ── 3.9 Remove unrealistic values ──────────────────────────────────
    sub("Removing unrealistic values")
    before = len(merged)

    # Temperature: plausible range 5–50
    merged = merged[(merged["temperature"] >= 5) & (merged["temperature"] <= 50)]
    # Rainfall: > 0
    merged = merged[merged["rainfall"] > 0]
    # Yield: > 0 and not absurdly high
    merged = merged[(merged["yield"] > 0) & (merged["yield"] < 100000)]
    # NPK: >= 0
    merged = merged[(merged["n"] >= 0) & (merged["p"] >= 0) & (merged["k"] >= 0)]
    # pH: 3.5 – 9.5
    merged = merged[(merged["ph"] >= 3.5) & (merged["ph"] <= 9.5)]

    log.info(f"    Rows: {before:,} → {len(merged):,} after removing unrealistic values")

    # ── 3.10 Final dataset stats ───────────────────────────────────────
    sub("Merged dataset statistics")
    log.info(f"    Total rows:    {len(merged):,}")
    log.info(f"    Crops:         {merged['crop'].nunique()} — {sorted(merged['crop'].unique())}")
    log.info(f"    States:        {merged['state'].nunique()}")
    log.info(f"    Districts:     {merged['district'].nunique()}")
    log.info(f"    Year range:    {merged['year'].min()}–{merged['year'].max()}")
    log.info(f"    Columns:       {list(merged.columns)}")

    for col in ["temperature", "rainfall", "n", "p", "k", "ph", "humidity",
                "yield", "area", "production"]:
        if col in merged.columns:
            log.info(f"    {col:15s}: min={merged[col].min():10.2f}  "
                     f"max={merged[col].max():10.2f}  "
                     f"mean={merged[col].mean():10.2f}  "
                     f"std={merged[col].std():10.2f}")

    # Save
    merged.to_csv(MERGED_CSV, index=False)
    log.info(f"    ✓ Saved: {MERGED_CSV} ({len(merged):,} rows)")

    return merged


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: CONVERT TO ML-READY FORMAT
# ═══════════════════════════════════════════════════════════════════════════

def step4_ml_format(merged: pd.DataFrame):
    section("CONVERT TO ML-READY FORMAT", 4)

    df = merged.copy()

    # ── 4.1 Drop year (not useful for crop prediction) ──────────────────
    sub("Dropping year column")
    if "year" in df.columns:
        df = df.drop(columns=["year"])
        log.info("    Dropped 'year'")

    # ── 4.2 Encode state and district ───────────────────────────────────
    sub("Encoding categorical variables")

    le_state = LabelEncoder()
    df["state_encoded"] = le_state.fit_transform(df["state"])
    log.info(f"    state:    {len(le_state.classes_)} classes encoded")

    le_district = LabelEncoder()
    df["district_encoded"] = le_district.fit_transform(df["district"])
    log.info(f"    district: {len(le_district.classes_)} classes encoded")

    # Crop is the target — encode separately
    le_crop = LabelEncoder()
    df["crop_encoded"] = le_crop.fit_transform(df["crop"])
    log.info(f"    crop (target): {len(le_crop.classes_)} classes — {list(le_crop.classes_)}")

    # ── 4.3 Select ML features ──────────────────────────────────────────
    sub("Selecting ML features")

    # Core features that align with v2.2 model
    feature_cols = [
        "n", "p", "k", "temperature", "humidity", "ph", "rainfall",
        "season", "soil_type", "irrigation",
    ]

    # Additional real-world features
    extra_cols = [
        "yield", "area", "production",
        "state_encoded", "district_encoded",
    ]

    # Check for seasonal columns
    seasonal_cols = []
    for c in ["jun-sep", "oct-dec", "jan-feb", "mar-may",
              "rain_monsoon", "rain_postmonsoon", "moisture"]:
        if c in df.columns and df[c].notna().sum() > 0:
            seasonal_cols.append(c)

    all_features = feature_cols + extra_cols + seasonal_cols
    available = [c for c in all_features if c in df.columns]
    missing = [c for c in all_features if c not in df.columns]

    if missing:
        log.warning(f"    Missing features (skipped): {missing}")

    log.info(f"    Selected {len(available)} features: {available}")

    # ── 4.4 Handle remaining NaN ────────────────────────────────────────
    sub("Handling remaining NaN values")
    for col in available:
        na_count = df[col].isna().sum()
        if na_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log.info(f"    Filled {na_count:,} NaN in '{col}' with median ({median_val:.2f})")

    # ── 4.5 Normalize continuous features ───────────────────────────────
    sub("Normalizing continuous features")
    continuous = [c for c in available if c not in
                  ["season", "soil_type", "irrigation", "state_encoded", "district_encoded"]]

    scaler = StandardScaler()
    df_norm = df.copy()
    df_norm[continuous] = scaler.fit_transform(df[continuous])

    log.info(f"    Normalized {len(continuous)} continuous features")
    log.info(f"    (Keeping unscaled copy for interpretability)")

    # ── 4.6 Save ────────────────────────────────────────────────────────
    sub("Saving ML dataset")

    ml_df = df[available + ["crop"]].copy()
    ml_df.to_csv(ML_CSV, index=False)
    log.info(f"    ✓ Saved: {ML_CSV} ({len(ml_df):,} rows × {len(ml_df.columns)} cols)")

    # Print class distribution
    sub("Class distribution")
    counts = ml_df["crop"].value_counts()
    for crop, cnt in counts.items():
        bar = "█" * max(1, int(cnt / counts.max() * 30))
        log.info(f"    {crop:18s}: {cnt:>6,}  {bar}")

    return ml_df, available, le_crop, scaler


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: TRAIN MODEL
# ═══════════════════════════════════════════════════════════════════════════

def step5_train(ml_df: pd.DataFrame, feature_cols: list, le_crop: LabelEncoder):
    section("TRAIN RANDOM FOREST MODEL", 5)

    X = ml_df[feature_cols].copy()
    y = le_crop.transform(ml_df["crop"].values)

    # ── 5.1 Train-test split ────────────────────────────────────────────
    sub("Train-test split (80/20, stratified)")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y,
    )
    log.info(f"    Train: {len(X_train):,}, Test: {len(X_test):,}")

    # ── 5.2 Train base model ───────────────────────────────────────────
    sub("Training Random Forest (n_estimators=400)")
    base_model = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    base_model.fit(X_train, y_train)
    log.info("    ✓ Base model trained")

    # ── 5.3 Evaluate base model ─────────────────────────────────────────
    sub("Base model evaluation")
    y_pred_base = base_model.predict(X_test)
    y_proba_base = base_model.predict_proba(X_test)

    acc_base = accuracy_score(y_test, y_pred_base)
    n_classes = len(le_crop.classes_)
    k_top3 = min(3, n_classes)
    top3_base = top_k_accuracy_score(y_test, y_proba_base, k=k_top3,
                                     labels=range(n_classes))
    max_conf_base = y_proba_base.max(axis=1).max() * 100
    log.info(f"    Top-1 Accuracy:  {acc_base*100:.2f}%")
    log.info(f"    Top-3 Accuracy:  {top3_base*100:.2f}%")
    log.info(f"    Max Confidence:  {max_conf_base:.1f}%")

    # ── 5.4 Calibrate ──────────────────────────────────────────────────
    sub("Calibrating with CalibratedClassifierCV (sigmoid, cv=3)")
    cal_cv = min(3, min(Counter(y_train).values()))
    if cal_cv < 2:
        log.warning(f"    Some classes have < 2 training samples — using base model without calibration")
        model = base_model
        calibrated = False
    else:
        calibrated_model = CalibratedClassifierCV(
            estimator=base_model,
            method="sigmoid",
            cv=3,
            n_jobs=-1,
        )
        try:
            calibrated_model.fit(X_train, y_train)
            model = calibrated_model
            calibrated = True
            log.info("    ✓ Calibrated model trained")
        except Exception as e:
            log.warning(f"    Calibration failed ({e}) — using base model")
            model = base_model
            calibrated = False

    # ── 5.5 Evaluate final model ────────────────────────────────────────
    sub("Final model evaluation")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    top3_accuracy = top_k_accuracy_score(y_test, y_proba, k=k_top3,
                                         labels=range(n_classes))
    max_conf = y_proba.max(axis=1).max() * 100

    log.info(f"")
    log.info(f"    ┌──────────────────────────────────────────────┐")
    log.info(f"    │  BEFORE CALIBRATION                          │")
    log.info(f"    │  Top-1: {acc_base*100:6.2f}%   Top-3: {top3_base*100:6.2f}%   Max: {max_conf_base:.1f}%  │")
    log.info(f"    ├──────────────────────────────────────────────┤")
    log.info(f"    │  AFTER CALIBRATION                           │")
    log.info(f"    │  Top-1: {accuracy*100:6.2f}%   Top-3: {top3_accuracy*100:6.2f}%   Max: {max_conf:.1f}%  │")
    log.info(f"    └──────────────────────────────────────────────┘")

    # ── 5.6 Classification report ───────────────────────────────────────
    sub("Classification Report")
    report = classification_report(y_test, y_pred, target_names=le_crop.classes_,
                                   zero_division=0)
    print(report)

    # ── 5.7 Feature importance ──────────────────────────────────────────
    sub("Feature Importances")
    importances = pd.Series(base_model.feature_importances_,
                            index=feature_cols).sort_values(ascending=False)
    for feat, imp in importances.items():
        bar = "█" * int(imp * 60)
        log.info(f"    {feat:22s}: {imp:.4f}  {bar}")

    # ── 5.8 Confusion matrix ───────────────────────────────────────────
    sub("Confusion Matrix")
    cm = confusion_matrix(y_test, y_pred)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(16, 14))
        im = ax.imshow(cm, interpolation="nearest", cmap="YlGn")
        ax.set_title("Confusion Matrix — Real-World Model", fontsize=14, pad=12)
        ticks = np.arange(n_classes)
        ax.set_xticks(ticks)
        ax.set_xticklabels(le_crop.classes_, rotation=90, fontsize=7)
        ax.set_yticks(ticks)
        ax.set_yticklabels(le_crop.classes_, fontsize=7)
        ax.set_ylabel("True", fontsize=11)
        ax.set_xlabel("Predicted", fontsize=11)
        fig.colorbar(im, ax=ax, shrink=0.6)
        fig.tight_layout()
        fig.savefig(CONFMAT_FILE, dpi=150)
        plt.close(fig)
        log.info(f"    ✓ Saved {CONFMAT_FILE}")
    except ImportError:
        log.info("    matplotlib not available — skipping plot")

    # ── 5.9 Cross-validation ───────────────────────────────────────────
    sub("5-Fold Stratified Cross-Validation")
    # Check minimum class count
    min_class = min(Counter(y).values())
    if min_class >= 5:
        kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        cv_model = RandomForestClassifier(
            n_estimators=400, min_samples_split=5, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=-1,
        )
        cv_scores = cross_val_score(cv_model, X, y, cv=kfold, scoring="accuracy")
        log.info(f"    Fold Accuracies: {cv_scores}")
        log.info(f"    Mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    else:
        log.warning(f"    Min class size = {min_class} — using 3-fold CV instead")
        n_folds = min(3, min_class)
        if n_folds >= 2:
            kfold = StratifiedKFold(n_splits=n_folds, shuffle=True,
                                    random_state=RANDOM_STATE)
            cv_model = RandomForestClassifier(
                n_estimators=400, min_samples_split=5, min_samples_leaf=2,
                random_state=RANDOM_STATE, n_jobs=-1,
            )
            cv_scores = cross_val_score(cv_model, X, y, cv=kfold, scoring="accuracy")
            log.info(f"    Fold Accuracies: {cv_scores}")
            log.info(f"    Mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        else:
            cv_scores = np.array([accuracy])
            log.warning(f"    Cannot run CV — using train accuracy")

    return {
        "model": model,
        "base_model": base_model,
        "calibrated": calibrated,
        "accuracy": accuracy,
        "top3_accuracy": top3_accuracy,
        "base_accuracy": acc_base,
        "base_top3": top3_base,
        "max_conf": max_conf,
        "max_conf_base": max_conf_base,
        "importances": importances,
        "cv_mean": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "X_train": X_train,
        "X_test": X_test,
        "y_test": y_test,
        "feature_cols": feature_cols,
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: COMPARE WITH SYNTHETIC v2.2
# ═══════════════════════════════════════════════════════════════════════════

def step6_compare(results: dict, le_crop: LabelEncoder, ml_df: pd.DataFrame):
    section("COMPARE WITH SYNTHETIC v2.2", 6)

    if not os.path.exists(SYNTHETIC_META):
        log.warning(f"  {SYNTHETIC_META} not found — skipping comparison")
        return {}

    with open(SYNTHETIC_META) as f:
        syn = json.load(f)

    # ── 6.1 Accuracy comparison ─────────────────────────────────────────
    sub("Accuracy Comparison")
    syn_top1 = syn.get("top1_accuracy", 0) * 100
    syn_top3 = syn.get("top3_accuracy", 0) * 100
    real_top1 = results["accuracy"] * 100
    real_top3 = results["top3_accuracy"] * 100

    log.info(f"    {'Metric':25s} {'Synthetic v2.2':>15s} {'Real-World':>15s} {'Δ':>10s}")
    log.info(f"    {'─'*25} {'─'*15} {'─'*15} {'─'*10}")
    log.info(f"    {'Top-1 Accuracy':25s} {syn_top1:14.2f}% {real_top1:14.2f}% "
             f"{real_top1 - syn_top1:+9.2f}%")
    log.info(f"    {'Top-3 Accuracy':25s} {syn_top3:14.2f}% {real_top3:14.2f}% "
             f"{real_top3 - syn_top3:+9.2f}%")
    log.info(f"    {'Max Confidence':25s} {syn.get('max_confidence_pct', 0):14.1f}% "
             f"{results['max_conf']:14.1f}%")
    log.info(f"    {'CV Mean':25s} {syn.get('cv_mean', 0)*100:14.2f}% "
             f"{results['cv_mean']*100:14.2f}%")

    # ── 6.2 Feature importance comparison ───────────────────────────────
    sub("Feature Importance Comparison")
    syn_imp = syn.get("feature_importances", {})
    real_imp = results["importances"]

    # Common features
    common_feats = sorted(set(syn_imp.keys()) & set(real_imp.index))
    log.info(f"    {'Feature':22s} {'Synthetic':>12s} {'Real-World':>12s} {'Δ':>10s}")
    log.info(f"    {'─'*22} {'─'*12} {'─'*12} {'─'*10}")
    for feat in common_feats:
        s = syn_imp[feat]
        r = float(real_imp.get(feat, 0))
        log.info(f"    {feat:22s} {s:11.4f} {r:11.4f} {r - s:+9.4f}")

    # Features only in real model
    real_only = [f for f in real_imp.index if f not in syn_imp]
    if real_only:
        log.info(f"    Features only in real model: {real_only}")
        for feat in real_only:
            log.info(f"    {feat:22s} {'n/a':>12s} {float(real_imp[feat]):11.4f}")

    # ── 6.3 Class imbalance comparison ─────────────────────────────────
    sub("Class Imbalance Comparison")
    real_counts = ml_df["crop"].value_counts()
    syn_classes = syn.get("total_classes", 0)
    real_classes = len(le_crop.classes_)

    log.info(f"    Synthetic classes: {syn_classes}")
    log.info(f"    Real classes:      {real_classes}")
    log.info(f"    Synthetic samples: {syn.get('total_samples', 0):,}")
    log.info(f"    Real samples:      {len(ml_df):,}")
    log.info(f"    Real max class:    {real_counts.max():,} ({real_counts.idxmax()})")
    log.info(f"    Real min class:    {real_counts.min():,} ({real_counts.idxmin()})")
    log.info(f"    Real imbalance ratio: {real_counts.max() / real_counts.min():.1f}x")

    return {
        "accuracy_diff": round(real_top1 - syn_top1, 2),
        "top3_diff": round(real_top3 - syn_top3, 2),
        "feature_importance_comparison": {
            feat: {"synthetic": syn_imp.get(feat, None),
                   "real": round(float(real_imp.get(feat, 0)), 6)}
            for feat in sorted(set(list(syn_imp.keys()) + list(real_imp.index)))
        },
        "class_comparison": {
            "synthetic_classes": syn_classes,
            "real_classes": real_classes,
            "synthetic_samples": syn.get("total_samples", 0),
            "real_samples": len(ml_df),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: SAVE ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

def step7_save(results: dict, le_crop: LabelEncoder, ml_df: pd.DataFrame,
               comparison: dict):
    section("SAVE ARTIFACTS", 7)

    model = results["model"]

    # ── 7.1 Save model ──────────────────────────────────────────────────
    joblib.dump(model, MODEL_FILE)
    log.info(f"  ✓ {MODEL_FILE}")

    # ── 7.2 Save label encoder ──────────────────────────────────────────
    joblib.dump(le_crop, ENCODER_FILE)
    log.info(f"  ✓ {ENCODER_FILE}")

    # ── 7.3 Build metadata ──────────────────────────────────────────────
    csv_bytes = ml_df.to_csv(index=False).encode("utf-8")
    dataset_hash = sha256_short(csv_bytes)

    with open(MODEL_FILE, "rb") as f:
        model_hash = sha256_short(f.read())

    metadata = {
        "model_version": "real_world_1.0",
        "model_type": ("CalibratedClassifierCV(RandomForestClassifier)"
                       if results["calibrated"]
                       else "RandomForestClassifier"),
        "calibration_used": results["calibrated"],
        "n_estimators": 400,
        "features": results["feature_cols"],
        "dataset": ML_CSV,
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
        "total_samples": int(len(ml_df)),
        "class_distribution": ml_df["crop"].value_counts().to_dict(),
        "feature_importances": {
            feat: round(float(imp), 6)
            for feat, imp in results["importances"].items()
        },
        "data_sources": [
            "ICRISAT-District_Level_Data.csv",
            "data_core.csv",
            "temperature.csv",
            "rainfall.csv",
            "Crop_recommendation.csv",
        ],
        "comparison_with_synthetic_v2_2": comparison,
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_state": RANDOM_STATE,
        "note": (
            "Real-world model trained on merged district-level agricultural data. "
            "ICRISAT crop yield/area/production + national temperature/rainfall + "
            "data_core NPK/soil/humidity + Crop_recommendation pH. "
            "No synthetic generation used."
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
    log.info("║  CROP RECOMMENDATION — REAL-WORLD DATA PIPELINE                    ║")
    log.info("║  No synthetic generation · District-level agricultural data only    ║")
    log.info("╚══════════════════════════════════════════════════════════════════════╝")

    # STEP 1
    loaded = step1_analyze()

    # STEP 2
    cleaned = step2_clean(loaded)

    # STEP 3
    merged = step3_merge(cleaned)

    # STEP 4
    ml_df, feature_cols, le_crop, scaler = step4_ml_format(merged)

    # STEP 5
    results = step5_train(ml_df, feature_cols, le_crop)

    # STEP 6
    comparison = step6_compare(results, le_crop, ml_df)

    # STEP 7
    metadata = step7_save(results, le_crop, ml_df, comparison)

    # ── Final summary ──────────────────────────────────────────────────
    log.info("")
    log.info("═" * 70)
    log.info("  PIPELINE COMPLETE — SUMMARY")
    log.info("═" * 70)
    log.info(f"  Merged dataset:   {MERGED_CSV}  ({len(merged):,} rows)")
    log.info(f"  ML dataset:       {ML_CSV}  ({len(ml_df):,} rows)")
    log.info(f"  Model:            {MODEL_FILE}")
    log.info(f"  Label encoder:    {ENCODER_FILE}")
    log.info(f"  Metadata:         {METADATA_FILE}")
    log.info(f"  Top-1 Accuracy:   {results['accuracy']*100:.2f}%")
    log.info(f"  Top-3 Accuracy:   {results['top3_accuracy']*100:.2f}%")
    log.info(f"  Max Confidence:   {results['max_conf']:.1f}%")
    log.info(f"  CV Mean:          {results['cv_mean']*100:.2f}%")
    log.info(f"  Classes:          {len(le_crop.classes_)}")
    log.info(f"  Samples:          {len(ml_df):,}")
    log.info("═" * 70)


if __name__ == "__main__":
    main()

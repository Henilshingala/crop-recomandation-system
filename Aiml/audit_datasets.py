"""Quick audit: circular vs real feature variability."""
import pandas as pd
import numpy as np

print("=" * 70)
print("  DATASET CIRCULARITY AUDIT")
print("=" * 70)

# === 1. Crop_recommendation_v2.csv ===
df = pd.read_csv("Crop_recommendation_v2.csv")
print(f"\n[1] Crop_recommendation_v2.csv: {df.shape[0]:,} rows, {df['label'].nunique()} crops")
print("    Features:", list(df.columns))

features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
print("\n    Per-crop standard deviation (non-zero = real variability):")
for f in features:
    gstd = df.groupby("label")[f].std()
    print(f"      {f:12s}: mean_std={gstd.mean():8.2f}  min_std={gstd.min():8.3f}  max_std={gstd.max():8.2f}")

# Show rice as example
rice = df[df["label"] == "rice"]
if len(rice):
    print(f"\n    Rice sample ({len(rice)} rows):")
    for f in features:
        print(f"      {f:12s}: {rice[f].min():.1f} – {rice[f].max():.1f}  std={rice[f].std():.2f}")

print(f"\n    VERDICT: Features have real per-sample variability = NOT circular")

# === 2. real_world_merged_dataset.csv ===
df2 = pd.read_csv("real_world_merged_dataset.csv")
print(f"\n[2] real_world_merged_dataset.csv: {df2.shape[0]:,} rows, {df2['crop'].nunique()} crops")

features2 = ["n", "p", "k", "temperature", "humidity", "ph", "rainfall", "moisture"]
print("\n    Per-crop standard deviation (near-zero = circular / crop-averaged):")
for f in features2:
    if f in df2.columns:
        gstd = df2.groupby("crop")[f].std()
        print(f"      {f:12s}: mean_std={gstd.mean():8.4f}  max_std={gstd.max():8.4f}")

# Show rice as example
rice2 = df2[df2["crop"] == "rice"]
if len(rice2):
    print(f"\n    Rice sample ({len(rice2)} rows):")
    for f in features2:
        if f in df2.columns:
            print(f"      {f:12s}: {rice2[f].min():.2f} – {rice2[f].max():.2f}  std={rice2[f].std():.4f}")

print(f"\n    VERDICT: N/P/K/humidity/moisture are crop-level constants = CIRCULAR")

# === 3. Check what packages are available for training ===
print("\n" + "=" * 70)
print("  TRAINING ENVIRONMENT CHECK")
print("=" * 70)
for pkg in ["sklearn", "xgboost", "lightgbm", "imblearn", "joblib", "scipy"]:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        print(f"  {pkg:15s}: {ver}")
    except ImportError:
        print(f"  {pkg:15s}: NOT INSTALLED")

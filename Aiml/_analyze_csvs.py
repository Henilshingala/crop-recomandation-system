"""Quick analysis of all CSV files in the Aiml directory."""
import pandas as pd
import os

files = [
    "ICRISAT-District_Level_Data.csv",
    "data_core.csv",
    "temperature.csv",
    "rainfall.csv",
    "Crop_recommendation.csv",
]

for f in files:
    sep = "=" * 70
    if not os.path.exists(f):
        print(f"\n{sep}\n  FILE: {f} — NOT FOUND\n{sep}")
        continue
    print(f"\n{sep}")
    print(f"  FILE: {f}")
    print(sep)
    try:
        full = pd.read_csv(f, encoding="utf-8", low_memory=False)
    except Exception:
        try:
            full = pd.read_csv(f, encoding="latin-1", low_memory=False)
        except Exception as e:
            print(f"  ERROR reading: {e}")
            continue
    print(f"  Shape: {full.shape}")
    print(f"  Columns ({len(full.columns)}):")
    for c in full.columns:
        print(f"    - {c:40s} dtype={str(full[c].dtype):10s} nulls={full[c].isnull().sum():>7d}  unique={full[c].nunique():>7d}")
    print(f"\n  First 3 rows:")
    print(full.head(3).to_string(index=False))
    print()

import pandas as pd
import numpy as np

# =========================
# CONFIG
# =========================
INPUT_CSV = "Crop_recommendation_synthetic_v1.csv"
OUTPUT_CSV = "Crop_recommendation_synthetic_AplusB.csv"

NOISE_LEVEL = 0.05  # 5% noise
np.random.seed(42)

NUMERIC_COLS = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']

# Label merge rules (B)
LABEL_MAP = {
    'bottle_gourd': 'gourd',
    'bitter_gourd': 'gourd',
    'ridge_gourd': 'gourd',

    'cabbage': 'cole_crop',
    'cauliflower': 'cole_crop',

    'lemon': 'citrus',
    'mosambi': 'citrus',
    'orange': 'citrus'
}

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(INPUT_CSV)

# =========================
# A) NOISE INJECTION
# =========================
for col in NUMERIC_COLS:
    noise = np.random.normal(0, NOISE_LEVEL, size=len(df))
    df[col] = df[col] * (1 + noise)

# Keep physical limits sane
df['humidity'] = df['humidity'].clip(0, 100)
df['ph'] = df['ph'].clip(3.5, 9.0)

# =========================
# B) LABEL MERGING
# =========================
df['label'] = df['label'].replace(LABEL_MAP)

# =========================
# SAVE OUTPUT
# =========================
df.to_csv(OUTPUT_CSV, index=False)

# =========================
# REPORT
# =========================
print("=" * 60)
print("A + B PIPELINE COMPLETED")
print("=" * 60)
print(f"Input file : {INPUT_CSV}")
print(f"Output file: {OUTPUT_CSV}")
print()
print("Noise Injection:")
print(f"  • Applied ±{int(NOISE_LEVEL*100)}% Gaussian noise")
print()
print("Label Merging:")
for k, v in LABEL_MAP.items():
    print(f"  • {k} → {v}")
print()
print("Final class count:", df['label'].nunique())
print("=" * 60)
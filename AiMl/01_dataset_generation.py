import pandas as pd
import numpy as np

ROWS_PER_CROP = 200
RANDOM_STATE = 42

crop_params = {
    # Cereals
    'rice': {'N': (80, 120), 'P': (40, 60), 'K': (40, 60), 'temp': (22, 28), 'hum': (80, 90), 'ph': (6.0, 7.0), 'rain': (200, 300)},
    'wheat': {'N': (80, 120), 'P': (40, 60), 'K': (30, 50), 'temp': (15, 25), 'hum': (50, 70), 'ph': (6.0, 7.0), 'rain': (45, 80)},
    'maize': {'N': (80, 120), 'P': (40, 60), 'K': (20, 40), 'temp': (20, 28), 'hum': (55, 70), 'ph': (5.5, 7.0), 'rain': (60, 110)},
    'barley': {'N': (60, 90), 'P': (20, 45), 'K': (20, 45), 'temp': (12, 23), 'hum': (40, 60), 'ph': (6.0, 7.5), 'rain': (35, 60)},
    'jowar': {'N': (80, 120), 'P': (40, 60), 'K': (40, 60), 'temp': (26, 34), 'hum': (40, 60), 'ph': (6.0, 7.5), 'rain': (50, 85)},
    'bajra': {'N': (40, 80), 'P': (30, 50), 'K': (30, 50), 'temp': (28, 36), 'hum': (30, 50), 'ph': (6.5, 8.0), 'rain': (30, 65)},
    'ragi': {'N': (50, 80), 'P': (20, 40), 'K': (20, 40), 'temp': (26, 35), 'hum': (40, 70), 'ph': (5.0, 7.5), 'rain': (60, 100)},

    # Pulses
    'chickpea': {'N': (20, 40), 'P': (55, 80), 'K': (75, 85), 'temp': (17, 22), 'hum': (15, 20), 'ph': (6.0, 7.5), 'rain': (65, 90)},
    'kidneybeans': {'N': (15, 35), 'P': (55, 80), 'K': (15, 25), 'temp': (18, 27), 'hum': (18, 25), 'ph': (5.5, 6.2), 'rain': (90, 150)},
    'pigeonpeas': {'N': (15, 35), 'P': (55, 80), 'K': (15, 25), 'temp': (26, 32), 'hum': (35, 65), 'ph': (5.0, 7.0), 'rain': (90, 160)},
    'mothbeans': {'N': (10, 35), 'P': (35, 60), 'K': (15, 25), 'temp': (25, 32), 'hum': (30, 60), 'ph': (5.0, 7.5), 'rain': (30, 70)},
    'mungbean': {'N': (10, 35), 'P': (35, 60), 'K': (15, 25), 'temp': (27, 32), 'hum': (60, 70), 'ph': (6.2, 7.2), 'rain': (35, 60)},
    'blackgram': {'N': (30, 40), 'P': (55, 80), 'K': (15, 25), 'temp': (25, 32), 'hum': (60, 70), 'ph': (6.5, 7.5), 'rain': (60, 80)},
    'lentil': {'N': (10, 35), 'P': (55, 80), 'K': (15, 25), 'temp': (18, 27), 'hum': (60, 70), 'ph': (6.0, 7.5), 'rain': (35, 55)},
    'soybean': {'N': (20, 50), 'P': (55, 80), 'K': (30, 60), 'temp': (20, 32), 'hum': (40, 70), 'ph': (6.0, 7.5), 'rain': (60, 100)},

    # Fruits
    'apple': {'N': (20, 40), 'P': (20, 40), 'K': (150, 200), 'temp': (15, 24), 'hum': (70, 90), 'ph': (5.5, 6.5), 'rain': (100, 130)},
    'banana': {'N': (100, 150), 'P': (60, 80), 'K': (150, 250), 'temp': (25, 30), 'hum': (80, 95), 'ph': (5.5, 7.0), 'rain': (150, 250)},
    'grapes': {'N': (20, 50), 'P': (30, 50), 'K': (150, 200), 'temp': (20, 35), 'hum': (50, 70), 'ph': (5.5, 7.0), 'rain': (40, 70)},
    'mango': {'N': (15, 40), 'P': (20, 40), 'K': (25, 35), 'temp': (27, 35), 'hum': (45, 60), 'ph': (4.5, 7.0), 'rain': (85, 110)},
    'orange': {'N': (40, 80), 'P': (20, 40), 'K': (20, 50), 'temp': (15, 30), 'hum': (60, 80), 'ph': (6.0, 7.5), 'rain': (80, 120)},
    'papaya': {'N': (50, 80), 'P': (40, 60), 'K': (50, 80), 'temp': (25, 35), 'hum': (75, 90), 'ph': (6.0, 7.0), 'rain': (150, 250)},
    'pomegranate': {'N': (30, 60), 'P': (20, 40), 'K': (30, 60), 'temp': (28, 40), 'hum': (30, 50), 'ph': (6.0, 7.5), 'rain': (35, 65)},
    'watermelon': {'N': (80, 100), 'P': (10, 30), 'K': (45, 55), 'temp': (25, 32), 'hum': (40, 55), 'ph': (6.0, 7.0), 'rain': (40, 60)},
    'muskmelon': {'N': (90, 110), 'P': (10, 30), 'K': (45, 55), 'temp': (27, 32), 'hum': (40, 55), 'ph': (6.0, 7.0), 'rain': (30, 50)},
    'coconut': {'N': (20, 40), 'P': (10, 30), 'K': (25, 35), 'temp': (25, 29), 'hum': (70, 90), 'ph': (5.0, 6.0), 'rain': (150, 220)},
    'guava': {'N': (20, 40), 'P': (20, 40), 'K': (20, 40), 'temp': (23, 30), 'hum': (50, 70), 'ph': (6.0, 7.5), 'rain': (80, 140)},
    'sapota': {'N': (30, 50), 'P': (20, 30), 'K': (30, 50), 'temp': (25, 35), 'hum': (70, 85), 'ph': (6.0, 8.0), 'rain': (130, 180)},
    'lemon': {'N': (40, 80), 'P': (20, 40), 'K': (20, 50), 'temp': (20, 30), 'hum': (50, 70), 'ph': (5.5, 7.0), 'rain': (65, 95)},
    'mosambi': {'N': (40, 80), 'P': (20, 40), 'K': (20, 50), 'temp': (22, 32), 'hum': (50, 75), 'ph': (6.0, 7.5), 'rain': (65, 95)},
    'custard_apple': {'N': (15, 35), 'P': (15, 35), 'K': (15, 35), 'temp': (25, 35), 'hum': (40, 65), 'ph': (6.5, 7.5), 'rain': (50, 85)},
    'date_palm': {'N': (20, 40), 'P': (10, 30), 'K': (20, 40), 'temp': (30, 42), 'hum': (20, 40), 'ph': (7.0, 8.5), 'rain': (15, 35)},
    'ber': {'N': (10, 30), 'P': (10, 30), 'K': (10, 30), 'temp': (25, 40), 'hum': (25, 50), 'ph': (7.0, 8.5), 'rain': (20, 50)},

    # Vegetables
    'tomato': {'N': (50, 70), 'P': (40, 60), 'K': (50, 70), 'temp': (20, 30), 'hum': (60, 80), 'ph': (6.0, 7.0), 'rain': (60, 100)},
    'potato': {'N': (60, 90), 'P': (40, 60), 'K': (50, 80), 'temp': (15, 25), 'hum': (50, 70), 'ph': (5.0, 6.0), 'rain': (50, 80)},
    'onion': {'N': (60, 90), 'P': (40, 60), 'K': (50, 80), 'temp': (15, 30), 'hum': (50, 70), 'ph': (6.0, 7.0), 'rain': (50, 80)},
    'brinjal': {'N': (80, 100), 'P': (60, 80), 'K': (40, 60), 'temp': (20, 30), 'hum': (60, 80), 'ph': (5.5, 6.8), 'rain': (80, 120)},
    'okra': {'N': (60, 80), 'P': (40, 60), 'K': (30, 50), 'temp': (25, 35), 'hum': (60, 80), 'ph': (6.0, 7.0), 'rain': (80, 120)},
    'cabbage': {'N': (80, 120), 'P': (60, 90), 'K': (80, 120), 'temp': (15, 22), 'hum': (60, 85), 'ph': (6.0, 7.5), 'rain': (60, 100)},
    'cauliflower': {'N': (80, 120), 'P': (60, 90), 'K': (80, 120), 'temp': (15, 25), 'hum': (60, 85), 'ph': (6.0, 7.5), 'rain': (60, 100)},
    'carrot': {'N': (50, 80), 'P': (40, 60), 'K': (80, 100), 'temp': (15, 22), 'hum': (50, 70), 'ph': (6.0, 7.0), 'rain': (40, 80)},
    'radish': {'N': (50, 80), 'P': (40, 60), 'K': (80, 100), 'temp': (12, 25), 'hum': (50, 70), 'ph': (6.0, 7.0), 'rain': (40, 80)},
    'spinach': {'N': (20, 50), 'P': (20, 40), 'K': (20, 40), 'temp': (12, 25), 'hum': (50, 70), 'ph': (6.0, 7.5), 'rain': (50, 80)},
    'bottle_gourd': {'N': (50, 70), 'P': (40, 60), 'K': (40, 60), 'temp': (25, 35), 'hum': (60, 80), 'ph': (6.0, 7.5), 'rain': (60, 100)},
    'bitter_gourd': {'N': (50, 70), 'P': (40, 60), 'K': (40, 60), 'temp': (25, 35), 'hum': (60, 80), 'ph': (6.0, 7.5), 'rain': (60, 100)},
    'ridge_gourd': {'N': (50, 70), 'P': (40, 60), 'K': (40, 60), 'temp': (25, 35), 'hum': (60, 80), 'ph': (6.0, 7.5), 'rain': (60, 100)},
    'cucumber': {'N': (60, 80), 'P': (40, 60), 'K': (50, 70), 'temp': (20, 30), 'hum': (70, 90), 'ph': (5.5, 7.0), 'rain': (80, 120)},
    'green_chilli': {'N': (60, 90), 'P': (40, 60), 'K': (50, 70), 'temp': (20, 30), 'hum': (60, 80), 'ph': (6.0, 7.0), 'rain': (60, 100)},

    # Commercial/Others
    'cotton': {'N': (110, 130), 'P': (40, 60), 'K': (50, 80), 'temp': (22, 28), 'hum': (60, 80), 'ph': (6.0, 8.0), 'rain': (60, 100)},
    'jute': {'N': (60, 90), 'P': (35, 55), 'K': (35, 45), 'temp': (23, 28), 'hum': (75, 90), 'ph': (6.0, 7.5), 'rain': (140, 200)},
    'coffee': {'N': (90, 110), 'P': (20, 40), 'K': (25, 35), 'temp': (23, 27), 'hum': (50, 70), 'ph': (6.0, 7.0), 'rain': (110, 190)},
    'sugarcane': {'N': (120, 150), 'P': (50, 70), 'K': (60, 120), 'temp': (24, 32), 'hum': (70, 85), 'ph': (6.0, 7.5), 'rain': (180, 240)},
    'tobacco': {'N': (40, 70), 'P': (35, 55), 'K': (80, 120), 'temp': (22, 30), 'hum': (55, 70), 'ph': (5.5, 7.0), 'rain': (40, 70)},
    'castor': {'N': (30, 50), 'P': (25, 40), 'K': (25, 40), 'temp': (22, 30), 'hum': (40, 60), 'ph': (5.5, 7.5), 'rain': (50, 70)},
    'sesame': {'N': (25, 45), 'P': (20, 35), 'K': (20, 35), 'temp': (25, 33), 'hum': (50, 70), 'ph': (5.5, 7.5), 'rain': (40, 70)},
    'groundnut': {'N': (20, 40), 'P': (40, 60), 'K': (30, 50), 'temp': (25, 32), 'hum': (45, 65), 'ph': (5.5, 7.0), 'rain': (50, 95)},
    'mustard': {'N': (60, 95), 'P': (40, 60), 'K': (20, 35), 'temp': (12, 24), 'hum': (40, 60), 'ph': (6.0, 7.5), 'rain': (40, 60)}
}

def linspace_clip(min_val, max_val, n, decimals):
    vals = np.linspace(min_val, max_val, n)
    vals = np.round(vals, decimals)
    return np.clip(vals, min_val, max_val)

data = []

for crop, p in crop_params.items():
    N = linspace_clip(*p['N'], ROWS_PER_CROP, 1)
    P = linspace_clip(*p['P'], ROWS_PER_CROP, 1)
    K = linspace_clip(*p['K'], ROWS_PER_CROP, 1)
    T = linspace_clip(*p['temp'], ROWS_PER_CROP, 2)
    H = linspace_clip(*p['hum'], ROWS_PER_CROP, 2)
    PH = linspace_clip(*p['ph'], ROWS_PER_CROP, 2)
    R = linspace_clip(*p['rain'], ROWS_PER_CROP, 1)

    for i in range(ROWS_PER_CROP):
        row = {
            'N': N[i],
            'P': P[(i + 37) % ROWS_PER_CROP],
            'K': K[(i + 73) % ROWS_PER_CROP],
            'temperature': T[(i + 11) % ROWS_PER_CROP],
            'humidity': H[(i + 59) % ROWS_PER_CROP],
            'ph': PH[(i + 101) % ROWS_PER_CROP],
            'rainfall': R[(i + 149) % ROWS_PER_CROP],
            'label': crop
        }
        data.append(row)

df = pd.DataFrame(data)

# Shuffle once to avoid ordering bias
df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

# Save clean CSV
df.to_csv("Crop_recommendation_synthetic_V1.csv", index=False)

print("CSV GENERATED SUCCESSFULLY")
print(f"Total crops: {len(crop_params)}")
print(f"Rows per crop: {ROWS_PER_CROP}")
print(f"Total rows: {len(df)}")
print("Columns:", list(df.columns))

# ====================================================================
# B - MODEL TRAINING AND EVALUATION
# ====================================================================

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# 1. Load dataset
df = pd.read_csv("crop_recommendation_synthetic_v1.csv")

# 2. Define features and target
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

# 3. Train-test split (80:20, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 4. Train Random Forest (baseline, no tuning)
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# 5. Predictions
y_pred = model.predict(X_test)

# 6. Evaluation
accuracy = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print("Accuracy:", accuracy)
print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# 7. Feature importance
importances = pd.Series(
    model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

print("\nFeature Importances:")
print(importances)

# ====================================================================
# C - CROSS-VALIDATION
# ====================================================================

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

# Load dataset
df = pd.read_csv("Crop_recommendation_synthetic_v1.csv", comment="#")

# Split features and label
X = df.drop(columns=["label"])
y = df["label"]

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Model (same as before)
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

# Stratified K-Fold
kfold = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

# Cross-validation accuracy
cv_scores = cross_val_score(
    model,
    X,
    y_encoded,
    cv=kfold,
    scoring="accuracy"
)

# Results
print("=" * 50)
print("CROSS-VALIDATION RESULTS (STEP 3)")
print("=" * 50)
print(f"Fold Accuracies: {cv_scores}")
print(f"Mean Accuracy : {cv_scores.mean():.4f}")
print(f"Std Deviation : {cv_scores.std():.4f}")
print("=" * 50)

# ====================================================================
# D - NOISE INJECTION AND LABEL MERGING
# ====================================================================

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

# ====================================================================
# E - MODEL EVALUATION (A + B DATASET)
# ====================================================================

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("Crop_recommendation_synthetic_AplusB.csv")

X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

# =========================
# ENCODE LABELS
# =========================
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# =========================
# TRAIN / TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# =========================
# MODEL
# =========================
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================
y_pred = model.predict(X_test)

print("=" * 60)
print("STEP 4 – MODEL EVALUATION (A + B DATASET)")
print("=" * 60)

print("\nAccuracy:")
print(accuracy_score(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=le.classes_
))

print("\nFeature Importances:")
for name, val in sorted(
    zip(X.columns, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{name:12s} : {val:.4f}")

print("=" * 60)

# ====================================================================
# F - STRESS TEST
# ====================================================================

# =========================
# LOAD TRAINED DATA
# =========================
df = pd.read_csv("Crop_recommendation_synthetic_AplusB.csv")

X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

le = LabelEncoder()
y_enc = le.fit_transform(y)

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)
model.fit(X, y_enc)

# =========================
# STRESS TEST CASES
# =========================
stress_cases = pd.DataFrame([
    # Dry & cool (Rabi-like)
    {'N': 90, 'P': 40, 'K': 40, 'temperature': 18, 'humidity': 45, 'ph': 6.8, 'rainfall': 45},

    # Extreme wet & hot
    {'N': 80, 'P': 30, 'K': 40, 'temperature': 28, 'humidity': 90, 'ph': 6.5, 'rainfall': 280},

    # Acidic + high rain
    {'N': 30, 'P': 20, 'K': 25, 'temperature': 26, 'humidity': 85, 'ph': 5.2, 'rainfall': 200},

    # High nutrients but dry
    {'N': 130, 'P': 70, 'K': 90, 'temperature': 30, 'humidity': 35, 'ph': 7.5, 'rainfall': 40},

    # Cool + high K (fruit-like)
    {'N': 25, 'P': 30, 'K': 180, 'temperature': 17, 'humidity': 75, 'ph': 6.2, 'rainfall': 110},
])

# =========================
# PREDICTIONS
# =========================
preds = model.predict(stress_cases)
pred_labels = le.inverse_transform(preds)

stress_cases['predicted_crop'] = pred_labels

print("=" * 60)
print("STEP 5 — STRESS TEST RESULTS")
print("=" * 60)
print(stress_cases)
print("=" * 60)

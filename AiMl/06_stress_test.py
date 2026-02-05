import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

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
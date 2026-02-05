import pandas as pd
import numpy as np

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
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
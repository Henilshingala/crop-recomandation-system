import pandas as pd
import numpy as np
import joblib
import sys
import os

sys.path.insert(0, 'D:/downloads/CRS/Backend/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()

from apps.ml_inference import get_predictor, apply_temperature, apply_inv_freq, apply_entropy_penalty

df = pd.read_csv('D:/downloads/CRS/Aiml/real_world_merged_dataset.csv')

pred = get_predictor()
pred._ensure_loaded()
crops = pred._honest_crops

print(f"T={pred._temperature}, binary_clfs={len(pred._binary_clfs)}, scaling={pred._feature_scaling}")
print()

test_crops = ['rice','wheat','maize','chickpea','cotton','sugarcane','mustard','groundnut','soybean','barley']
print('V2 predictions using TRAINING DATA MEDIANS (full pipeline):')

v1 = joblib.load('D:/downloads/CRS/Aiml/model_real_world_honest.joblib')

correct_v1 = 0
correct_v2 = 0

for crop in test_crops:
    sub = df[df['crop']==crop]
    m = sub[['n','p','k','temperature','humidity','ph','rainfall','season','soil_type','irrigation','moisture']].median()
    X = m.values.reshape(1,-1)

    # V1
    p1 = v1.predict_proba(X)[0]
    top1_v1 = crops[np.argmax(p1)]
    c1 = p1.max()*100

    # V2 with full pipeline
    raw = pred._honest_model.predict_proba(X)[0]
    p = apply_temperature(raw, pred._temperature)
    if pred._inv_freq_weights is not None:
        p = apply_inv_freq(p, pred._inv_freq_weights)
    dom = np.array([pred._dominance_rates.get(c, 0) > 0.25 for c in crops], dtype=bool)
    p = apply_entropy_penalty(p, dom)
    p /= p.sum()
    top1_v2 = crops[np.argmax(p)]
    c2 = p.max()*100

    ok1 = 'OK' if top1_v1 == crop else f'WRONG({top1_v1})'
    ok2 = 'OK' if top1_v2 == crop else f'WRONG({top1_v2})'
    if top1_v1 == crop: correct_v1 += 1
    if top1_v2 == crop: correct_v2 += 1

    print(f'  {crop:15s}: V1={top1_v1:12s}({c1:.0f}%) {ok1:20s}  V2={top1_v2:12s}({c2:.0f}%) {ok2}')

print()
print(f'  V1 accuracy: {correct_v1}/{len(test_crops)} = {correct_v1/len(test_crops)*100:.0f}%')
print(f'  V2 accuracy: {correct_v2}/{len(test_crops)} = {correct_v2/len(test_crops)*100:.0f}%')

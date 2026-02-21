import pandas as pd
import numpy as np
import joblib

df = pd.read_csv('D:/downloads/CRS/Aiml/real_world_ml_dataset.csv')
crops_of_interest = ['rice', 'wheat', 'maize', 'chickpea', 'cotton', 'sugarcane', 'mustard', 'groundnut', 'soybean', 'barley']
cols = ['n','p','k','temperature','humidity','ph','rainfall','season','soil_type','irrigation','moisture']

print("Crop median feature values (real-world dataset):")
print(f"  {'Crop':15s} N    P    K    Temp  Hum   pH   Rain  Season Moist")
for crop in crops_of_interest:
    sub = df[df['crop']==crop]
    if len(sub) > 0:
        m = sub[cols].median()
        print(f"  {crop:15s} {m.n:.0f}  {m.p:.0f}  {m.k:.0f}  {m.temperature:.1f}  {m.humidity:.1f}  {m.ph:.1f}  {m.rainfall:.0f}  {int(m.season)}  {m.moisture:.1f}")

# Now compare v1 vs v2 predictions on actual crop feature medians
print()
print("V1 vs V2 predictions using REAL median features:")
v1 = joblib.load('D:/downloads/CRS/Aiml/model_real_world_honest.joblib')
v2 = joblib.load('D:/downloads/CRS/Aiml/model_real_world_honest_v2.joblib')
le = joblib.load('D:/downloads/CRS/Aiml/label_encoder_real_honest.joblib')
crop_list = list(le.classes_)

for crop in crops_of_interest:
    sub = df[df['crop']==crop]
    if len(sub) == 0:
        continue
    m = sub[cols].median()
    X = np.array([[m.n, m.p, m.k, m.temperature, m.humidity, m.ph, m.rainfall, m.season, m.soil_type, m.irrigation, m.moisture]])
    
    p1 = v1.predict_proba(X)[0]
    top1_v1 = crop_list[np.argmax(p1)]
    conf1 = p1[np.argmax(p1)] * 100
    
    p2 = v2.predict_proba(X)[0]
    top1_v2 = crop_list[np.argmax(p2)]
    conf2 = p2[np.argmax(p2)] * 100
    
    correct_v1 = "CORRECT" if top1_v1 == crop else f"WRONG({top1_v1})"
    correct_v2 = "CORRECT" if top1_v2 == crop else f"WRONG({top1_v2})"
    
    print(f"  {crop:12s}: V1={top1_v1:12s}({conf1:.0f}%) {correct_v1:20s}  V2={top1_v2:12s}({conf2:.0f}%) {correct_v2}")

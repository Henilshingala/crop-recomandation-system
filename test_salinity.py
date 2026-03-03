import requests, json

URL = "https://shingala-crs.hf.space/recommend"

def show(label, payload):
    r = requests.post(URL, json=payload, timeout=30).json()
    print(f"=== {label} ===")
    for i, rec in enumerate(r.get("top_recommendations", [])):
        crop = rec["crop"]
        conf = rec["confidence"]
        tier = rec["advisory_tier"]
        cons = rec.get("model_consensus", "?")
        print(f"  #{i+1} {crop:15s}  conf={conf:6.2f}%  tier={tier}  consensus={cons}")
    warn = r.get("warning", "")
    if warn:
        print(f"  WARNING: {warn[:120]}")
    print()

# Saline: pH=9.2, rain=2500, warm (crops viable by temp)
show("SALINE (pH=9.2, rain=2500, temp=28)",
     dict(N=80, P=40, K=60, temperature=28, humidity=80, ph=9.2, rainfall=2500))

# Control: same but pH=6.5 (no salinity trigger)
show("CONTROL (pH=6.5, rain=2500, temp=28)",
     dict(N=80, P=40, K=60, temperature=28, humidity=80, ph=6.5, rainfall=2500))

# Cold+Saline (original hard mode test 1)
show("COLD+SALINE (pH=9.2, rain=2500, temp=5)",
     dict(N=120, P=80, K=120, temperature=5, humidity=90, ph=9.2, rainfall=2500))

"""V7.1 Hard Mode Test Set (Level 2) — 12 requests against /recommend"""
import requests
import json

URL = "https://shingala-crs.hf.space/recommend"

tests = [
    ("1  Cold+TropicalRain+HighAlkaline",
     dict(N=120, P=80, K=120, temperature=5, humidity=90, ph=9.2, rainfall=2500, moisture=50, soil_type=1, irrigation=0)),
    ("2  PerfectSoil+ExtremeHeat",
     dict(N=100, P=50, K=60, temperature=48, humidity=65, ph=6.5, rainfall=600, moisture=50, soil_type=1, irrigation=0)),
    ("3  NeutralWeather+AcidSoil pH3.2",
     dict(N=90, P=40, K=40, temperature=25, humidity=70, ph=3.2, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("4  Moderate+UltraLowHumidity 12%",
     dict(N=100, P=60, K=60, temperature=25, humidity=12, ph=6.5, rainfall=700, moisture=50, soil_type=1, irrigation=0)),
    ("5  Flood+Cold+LowNutrients",
     dict(N=10, P=5, K=5, temperature=6, humidity=95, ph=6.2, rainfall=2800, moisture=50, soil_type=1, irrigation=0)),
    ("6  ExtremeNutrients+IdealClimate",
     dict(N=210, P=115, K=315, temperature=28, humidity=75, ph=6.8, rainfall=800, moisture=50, soil_type=1, irrigation=0)),
    ("7a TempSweep 18C",
     dict(N=90, P=40, K=40, temperature=18, humidity=70, ph=6.5, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("7b TempSweep 22C",
     dict(N=90, P=40, K=40, temperature=22, humidity=70, ph=6.5, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("7c TempSweep 26C",
     dict(N=90, P=40, K=40, temperature=26, humidity=70, ph=6.5, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("7d TempSweep 30C",
     dict(N=90, P=40, K=40, temperature=30, humidity=70, ph=6.5, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("7e TempSweep 34C",
     dict(N=90, P=40, K=40, temperature=34, humidity=70, ph=6.5, rainfall=500, moisture=50, soil_type=1, irrigation=0)),
    ("8  TrueChaos",
     dict(N=160, P=15, K=280, temperature=12, humidity=30, ph=8.9, rainfall=120, moisture=50, soil_type=1, irrigation=0)),
]

results = []

for name, payload in tests:
    try:
        r = requests.post(URL, json=payload, timeout=30)
        d = r.json()
        recs = d.get("top_recommendations", [])
        si = d.get("stress_index", "N/A")
        warn = d.get("warning", "")
        line = f"=== {name} ==="
        print(line)
        results.append(line)

        s = f"  Stress Index: {si}"
        print(s); results.append(s)

        if warn:
            s = f"  WARNING: {warn}"
            print(s); results.append(s)

        for i, rec in enumerate(recs[:3]):
            crop = rec.get("crop", "?")
            conf = rec.get("confidence", 0)
            tier = rec.get("advisory_tier", "?")
            cons = rec.get("model_consensus", "?")
            expl = rec.get("explanation", "")
            s = f"  #{i+1} {crop:15s}  conf={conf:6.2f}%  tier={tier}  consensus={cons}"
            print(s); results.append(s)
            if expl:
                s = f"     -> {expl[:140]}"
                print(s); results.append(s)

        print(); results.append("")
    except Exception as e:
        s = f"=== {name} === ERROR: {e}"
        print(s); results.append(s)
        results.append("")

# ── Fail-condition checks ─────────────────────────────────────────
print("=" * 70)
print("FAIL-CONDITION AUDIT")
print("=" * 70)
results.append("=" * 70)
results.append("FAIL-CONDITION AUDIT")
results.append("=" * 70)

fails = 0

# Re-run to collect structured data
all_data = {}
for name, payload in tests:
    try:
        r = requests.post(URL, json=payload, timeout=30)
        all_data[name] = r.json()
    except:
        all_data[name] = {}

# Check 1: Any extreme test > 85%
for name in [t[0] for t in tests if "TempSweep" not in t[0]]:
    recs = all_data.get(name, {}).get("top_recommendations", [])
    if recs and recs[0].get("confidence", 0) > 85:
        s = f"  FAIL: {name} top conf = {recs[0]['confidence']}% (>85%)"
        print(s); results.append(s); fails += 1

# Check 2: Tropical crops in cold test (test 1, temp=5)
cold_recs = all_data.get("1  Cold+TropicalRain+HighAlkaline", {}).get("top_recommendations", [])
tropical = {"coconut", "papaya", "mango", "banana", "pineapple", "cashew", "coffee", "cocoa"}
for rec in cold_recs[:3]:
    if rec.get("crop", "").lower() in tropical:
        s = f"  FAIL: Tropical crop '{rec['crop']}' in cold test"
        print(s); results.append(s); fails += 1

# Check 3: Confidence spike > 32% between adjacent 4C steps in sweep
sweep_confs = []
for tag in ["7a", "7b", "7c", "7d", "7e"]:
    key = [n for n in all_data if n.startswith(tag)][0]
    recs = all_data[key].get("top_recommendations", [])
    sweep_confs.append(recs[0].get("confidence", 0) if recs else 0)

for i in range(1, len(sweep_confs)):
    delta = abs(sweep_confs[i] - sweep_confs[i-1])
    if delta > 32:
        s = f"  FAIL: Sweep spike {sweep_confs[i-1]:.1f}% -> {sweep_confs[i]:.1f}% (delta {delta:.1f}%)"
        print(s); results.append(s); fails += 1

# Check 4: Chaos test > 90%
chaos_recs = all_data.get("8  TrueChaos", {}).get("top_recommendations", [])
if chaos_recs and chaos_recs[0].get("confidence", 0) > 90:
    s = f"  FAIL: Chaos test conf = {chaos_recs[0]['confidence']}% (>90%)"
    print(s); results.append(s); fails += 1

if fails == 0:
    s = "  ALL FAIL-CONDITIONS PASSED"
    print(s); results.append(s)
else:
    s = f"  {fails} FAIL(S) DETECTED"
    print(s); results.append(s)

# Sweep summary
print("\nSWEEP CURVE (Test 7):")
results.append("\nSWEEP CURVE (Test 7):")
for i, tag in enumerate(["18C", "22C", "26C", "30C", "34C"]):
    key = [n for n in all_data if tag in n][0]
    recs = all_data[key].get("top_recommendations", [])
    crop = recs[0]["crop"] if recs else "?"
    conf = recs[0]["confidence"] if recs else 0
    s = f"  {tag}: {crop:15s} {conf:.2f}%"
    print(s); results.append(s)

# Save
with open("hard_mode_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
print("\nSaved to hard_mode_results.txt")

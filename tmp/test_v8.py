import requests, json

payload = {
    "N": 90, "P": 42, "K": 43,
    "temperature": 25, "humidity": 80, "ph": 6.5, "rainfall": 200
}
r = requests.post("https://shingala-crs.hf.space/recommend", json=payload, timeout=20)
d = r.json()
print("Version:", d.get("version"))
print("Disclaimer:", d.get("disclaimer", "")[:80])
for c in d.get("top_recommendations", []):
    crop = c["crop"]
    conf = c["confidence"]
    tier = c.get("advisory_tier", "?")
    stress = c.get("stress_index", "?")
    print(f"  {crop:15s} conf={conf:.1f}% tier={tier} stress={stress}")

# Edge case: extreme cold
print("\n--- Extreme cold test (temp=2) ---")
payload2 = {"N": 50, "P": 30, "K": 30, "temperature": 2, "humidity": 50, "ph": 7.0, "rainfall": 100}
r2 = requests.post("https://shingala-crs.hf.space/recommend", json=payload2, timeout=20)
d2 = r2.json()
for c in d2.get("top_recommendations", []):
    print(f"  {c['crop']:15s} conf={c['confidence']:.1f}% tier={c.get('advisory_tier','?')}")

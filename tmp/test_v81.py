"""V8.1 validation tests — verify fallback, caps, and flags."""
import requests, json

API = "https://shingala-crs.hf.space"

def test(name, payload):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    r = requests.post(f"{API}/recommend", json=payload, timeout=20)
    d = r.json()
    print(f"  Version:            {d.get('version')}")
    print(f"  Fallback mode:      {d.get('fallback_mode')}")
    print(f"  All not recommended: {d.get('all_not_recommended')}")
    print(f"  Disclaimer:         {d.get('disclaimer','')[:60]}...")
    recs = d.get("top_recommendations", [])
    print(f"  Crops returned:     {len(recs)}")
    for c in recs:
        print(f"    {c['crop']:20s} conf={c['confidence']:.1f}% tier={c.get('advisory_tier','?')}")
    if d.get("warning"):
        print(f"  Warning: {d['warning'][:100]}")
    return d

# Test 1: Normal conditions — should get good results
test("Normal conditions",
     {"N": 90, "P": 42, "K": 43, "temperature": 25, "humidity": 80, "ph": 6.5, "rainfall": 200})

# Test 2: Extreme cold — previously returned empty, now should fallback
test("Extreme cold (2C) — FALLBACK expected",
     {"N": 50, "P": 30, "K": 30, "temperature": 5, "humidity": 50, "ph": 7.0, "rainfall": 100})

# Test 3: Extreme pH — previously returned empty
test("Extreme pH (3.0) — FALLBACK expected",
     {"N": 50, "P": 30, "K": 30, "temperature": 25, "humidity": 60, "ph": 3.0, "rainfall": 100})

# Test 4: Desert — hot, dry, alkaline
test("Desert (48C, pH 8.5, rain 10mm)",
     {"N": 20, "P": 10, "K": 15, "temperature": 48, "humidity": 15, "ph": 8.5, "rainfall": 10})

# Test 5: Perfect conditions — should NOT be fallback
test("Perfect rice conditions",
     {"N": 80, "P": 48, "K": 40, "temperature": 24, "humidity": 82, "ph": 6.0, "rainfall": 1200})

# Test 6: Health check
print(f"\n{'='*60}")
print("HEALTH CHECK")
r = requests.get(f"{API}/", timeout=10)
d = r.json()
print(f"  Version: {d.get('version')}")
print(f"  Status:  {d.get('status')}")

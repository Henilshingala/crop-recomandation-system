"""
Batch-test all rows in final.csv against the deployed V8 /recommend endpoint
and fill Crop1, Crop2, Crop3 columns.
Values outside API acceptance range are clipped to the boundary.
"""
import csv, requests, time, sys

API = "https://shingala-crs.hf.space/recommend"
INPUT_CSV  = r"d:\downloads\CRS\final.csv"
OUTPUT_CSV = r"d:\downloads\CRS\final_results_v81.csv"

# Acceptance ranges from feature_ranges.json
LIMITS = {
    "N":           (0, 210),
    "P":           (0, 115),
    "K":           (0, 315),
    "temperature": (5, 50),
    "humidity":    (0, 100),
    "ph":          (3.0, 10.0),
    "rainfall":    (0, 3200),
}

def clip(val, lo, hi):
    return max(lo, min(hi, val))

rows = []
with open(INPUT_CSV, newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

print(f"Loaded {len(rows)} rows. Calling API...\n")

results = []
for i, row in enumerate(rows, 1):
    raw = {
        "N":           float(row["N"]),
        "P":           float(row["P"]),
        "K":           float(row["K"]),
        "temperature": float(row["Temperature"]),
        "humidity":    float(row["Humidity"]),
        "ph":          float(row["pH"]),
        "rainfall":    float(row["Rainfall"]),
    }
    # Clip to accepted ranges
    payload = {k: clip(v, *LIMITS[k]) for k, v in raw.items()}
    clipped = [k for k in raw if raw[k] != payload[k]]
    if clipped:
        print(f"  Row {i}: clipped {clipped}")

    for attempt in range(3):
        try:
            resp = requests.post(API, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"  Row {i}: FAILED after 3 attempts – {e}")
                data = None

    if data and "top_recommendations" in data:
        crops = [c["crop"] for c in data["top_recommendations"]]
        # Pad to 3 if fewer returned
        while len(crops) < 3:
            crops.append("")
        row["Crop1"] = crops[0]
        row["crop2"] = crops[1]
        row["Crop3"] = crops[2]

        pcts = []
        for c in data["top_recommendations"]:
            pct = c.get("confidence") or c.get("probability") or c.get("score", "")
            pcts.append(f"{pct}")
        print(f"  Row {i:>3}: {crops[0]:>20} | {crops[1]:>20} | {crops[2]:>20}  ({', '.join(pcts)})")
    else:
        row["Crop1"] = "ERROR"
        row["crop2"] = "ERROR"
        row["Crop3"] = "ERROR"
        print(f"  Row {i:>3}: ERROR – no valid response")

    results.append(row)
    # small delay to be nice to the server
    time.sleep(0.3)

# Write output
fieldnames = ["N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall", "Crop1", "crop2", "Crop3"]
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"\nDone! Results written to {OUTPUT_CSV}")

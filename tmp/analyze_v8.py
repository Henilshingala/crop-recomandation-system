"""Quick analysis of V8 batch results."""
import csv

with open(r"d:\downloads\CRS\final_results_v8.csv") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
empty = sum(1 for r in rows if not r.get("Crop1","").strip())
partial = sum(1 for r in rows if r.get("Crop1","").strip() and not r.get("Crop3","").strip())
full = sum(1 for r in rows if r.get("Crop3","").strip())

print(f"Total rows:               {total}")
print(f"Empty (all filtered):     {empty}")
print(f"Partial (1-2 crops):      {partial}")
print(f"Full (3 crops):           {full}")
print(f"\nFiltered %: {empty/total*100:.1f}%")

# Check max confidence
max_conf = 0
for r in rows:
    for k in ["Crop1"]:  # no confidence column, let's skip
        pass

# Crop frequency
from collections import Counter
crops = Counter()
for r in rows:
    for col in ["Crop1", "crop2", "Crop3"]:
        c = r.get(col, "").strip()
        if c:
            crops[c] += 1

print(f"\nUnique crops recommended: {len(crops)}")
print("Top 10 crops:")
for crop, count in crops.most_common(10):
    print(f"  {crop:20s}  {count}")

"""V8.1 batch results analysis."""
import csv

with open(r"d:\downloads\CRS\final_results_v81.csv") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
empty = sum(1 for r in rows if not r.get("Crop1", "").strip())
one_only = sum(1 for r in rows if r.get("Crop1", "").strip() and not r.get("crop2", "").strip())
two = sum(1 for r in rows if r.get("crop2", "").strip() and not r.get("Crop3", "").strip())
full = sum(1 for r in rows if r.get("Crop3", "").strip())

print(f"Total rows:          {total}")
print(f"Empty (ZERO crops):  {empty}  {'OK - should be 0' if empty == 0 else 'FAIL'}")
print(f"1 crop only:         {one_only}")
print(f"2 crops:             {two}")
print(f"Full 3 crops:        {full}")
print(f"\nV8.0 had {33} blank rows — V8.1 has {empty}")

# Max confidence check
from collections import Counter
crops = Counter()
max_conf = 0
for r in rows:
    for col in ["Crop1", "crop2", "Crop3"]:
        c = r.get(col, "").strip()
        if c:
            crops[c] += 1

print(f"\nUnique crops: {len(crops)}")
print("Top 10:")
for crop, count in crops.most_common(10):
    print(f"  {crop:20s}  {count}")

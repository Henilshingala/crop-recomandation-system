
import os
import re

directory = r"Backend/app/media/crops"
files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

# Define the full set of crops (from crop_sync.py)
all_crops = sorted([
    "apple", "bajra", "banana", "barley", "ber", "blackgram",
    "brinjal", "carrot", "castor", "chickpea", "citrus", "coconut",
    "coffee", "cole_crop", "cotton", "cucumber", "custard_apple",
    "date_palm", "gourd", "grapes", "green_chilli", "groundnut",
    "guava", "jowar", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "mustard", "okra",
    "onion", "papaya", "pigeonpeas", "pomegranate", "potato", "radish",
    "ragi", "rice", "sapota", "sesame", "soybean", "spinach",
    "sugarcane", "tobacco", "tomato", "watermelon", "wheat",
    # Name variants
    "sesamum", "pigeonpea", "kindneybeans"
])

# Mapping: crop -> [slot1, slot2, slot3]
mapping = {crop: [None, None, None] for crop in all_crops}

# Manual overrides for tricky names or priority
overrides = {
    "apple": ["apple2.jpg", "apple3.jpg", "apple1.jpeg"],
    "banana": ["banana1.webp", "banana2.jpg", "banana3.webp"],
    "barley": ["c1.webp", "c2.jpg", "c3.jpg"],
    "mustard": ["mustard1.avif", "mustard4.jpg", None],
    "pomegranate": ["pomegranate.png", "pomegranate2.jpg", "pomegranate3.jpg"],
}

for crop in all_crops:
    if crop in overrides:
        mapping[crop] = (overrides[crop] + [None]*3)[:3]
        continue

    # Look for files like {crop}1.ext, {crop}2.ext, etc.
    for i in range(1, 4):
        p = re.compile(rf"^{re.escape(crop)}{i}\.(jpg|jpeg|png|webp|avif)$", re.IGNORECASE)
        match = [f for f in files if p.match(f)]
        if match:
            mapping[crop][i-1] = match[0]

# Add variants mapping
mapping["sesamum"] = mapping.get("sesamum", [None]*3)
if any(mapping["sesame"]):
     mapping["sesamum"] = mapping["sesame"]
if any(mapping["pigeonpeas"]):
     mapping["pigeonpea"] = mapping["pigeonpeas"]
if any(mapping["pigeonpea"]):
     mapping["pigeonpeas"] = mapping["pigeonpea"]
if any(mapping["kidneybeans"]):
     mapping["kindneybeans"] = mapping["kidneybeans"]
if any(mapping["kindneybeans"]):
     mapping["kidneybeans"] = mapping["kindneybeans"]

# Sort alphabetically for the output
print("_CROP_IMAGES: Dict[str, List[str | None]] = {")
for crop in sorted(mapping.keys()):
    vals = mapping[crop]
    val_str = f"[{repr(vals[0])}, {repr(vals[1])}, {repr(vals[2])}]"
    print(f'    "{crop}": {val_str},')
print("}")

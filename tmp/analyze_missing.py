
hf_crops = sorted([
    "barley", "castor", "chickpea", "cotton", "finger_millet",
    "groundnut", "linseed", "maize", "mustard", "pearl_millet",
    "pigeonpea", "rice", "safflower", "sesamum", "sorghum",
    "soybean", "sugarcane", "sunflower", "wheat",
])

synthetic_crops = sorted([
    "apple", "bajra", "banana", "barley", "ber", "blackgram",
    "brinjal", "carrot", "castor", "chickpea", "citrus", "coconut",
    "coffee", "cole_crop", "cotton", "cucumber", "custard_apple",
    "date_palm", "gourd", "grapes", "green_chilli", "groundnut",
    "guava", "jowar", "jute", "kidneybeans", "lentil", "maize",
    "mango", "mothbeans", "mungbean", "muskmelon", "mustard", "okra",
    "onion", "papaya", "pigeonpeas", "pomegranate", "potato", "radish",
    "ragi", "rice", "sapota", "sesame", "soybean", "spinach",
    "sugarcane", "tobacco", "tomato", "watermelon", "wheat",
])

crop_images = {
    "apple":        ["apple2.jpg", "apple3.jpg", None],
    "banana":       ["b1.webp", "b2.jpg", None],
    "barley":       ["c1.webp", "c2.jpg", "c3.jpg"],
    "blackgram":    ["blackgram2.webp", None, None],
    "brinjal":      ["brinjal1.avif", "brinjal2.jpg", "brinjal3.webp"],
    "carrot":       ["carrot1.webp", "carrot2.webp", "carrot3.jpg"],
    "castor":       ["castor3.jpg", None, None],
    "chickpea":     [None, None, None],
    "citrus":       ["citrus3.jpg", None, None],
    "coconut":      ["coconut1.jpg", "coconut2.webp", "coconut3.jpg"],
    "coffee":       ["coffee1.jpg", "coffee2.avif", "coffee3.jpg"],
    "cole_crop":    ["cole_crop2.jpg", "cole_crop3.jpg", None],
    "cotton":       [None, None, None],
    "date_palm":    ["date_palm1.webp", None, None],
    "gourd":        ["gourd1.webp", "gourd2.jpg", None],
    "grapes":       ["grapes1.webp", "grapes3.jpg", None],
    "green_chilli": ["green_chilli1.jpg", "green_chilli2.webp", "green_chilli3.jpg"],
    "groundnut":    ["groundnut3.jpg", None, None],
    "guava":        ["guava1.jpg", None, None],
    "jute":         ["jute1.webp", None, None],
    "maize":        ["maize2.webp", "maize3.jpg", None],
    "mango":        ["mango2.jpg", "mango3.webp", None],
    "mungbean":     ["mungbean1.webp", "mungbean3.webp", None],
    "muskmelon":    ["muskmelon1.jpg", None, None],
    "mustard":      ["mustard1.avif", "mustard4.jpg", None],
    "okra":         ["okra3.jpg", None, None],
    "onion":        ["onion1.jpg", "onion2.webp", "onion3.webp"],
    "papaya":       ["papaya1.jpg", "papaya3.webp", None],
    "pigeonpeas":   ["pigeonpeas1.jpg", "pigeonpeas2.jpg", None],
    "pomegranate":  ["pomegranate.png", "pomegranate2.jpg", "pomegranate3.jpg"],
    "potato":       ["potato1.jpeg", "potato2.jpg", None],
    "radish":       ["radish3.jpg", None, None],
    "rice":         ["rice1.jpeg", "rice2.jpg", "rice3.avif"],
    "sapota":       ["sapota1.webp", "sapota3.webp", None],
    "sesame":       ["sesame1.jpg", "sesame2.webp", None],
    "soybean":      ["soybean1.webp", "soybean3.webp", None],
    "spinach":      ["spinach2.jpg", "spinach3.jpg", None],
    "sugarcane":    ["sugarcane1.webp", "sugarcane2.jpg", "sugarcane3.avif"],
    "tobacco":      ["tobacco1.webp", "tobacco.jpg", None],
    "tomato":       ["tomato1.jpg", "tomato3.jpg", None],
    "watermelon":   ["watermelon1.jpg", "watermelon3.webp", None],
    "wheat":        ["wheat2.jpg", "wheat3.png", None],
}

all_named_crops = sorted(list(set(hf_crops) | set(synthetic_crops)))

missing_completely = []
missing_partially = []

print("--- ANALYSIS OF MISSING IMAGES ---\n")

for crop in all_named_crops:
    if crop not in crop_images:
        missing_completely.append(crop)
    else:
        imgs = crop_images[crop]
        if all(x is None for x in imgs):
            missing_completely.append(crop)
        elif any(x is None for x in imgs):
            missing_partially.append(crop)

print(f"Total Unique Crops in System: {len(all_named_crops)}")
print(f"Crops with NO mapping at all: {len(missing_completely)}")
for c in missing_completely:
    print(f" [!] {c}")

print(f"\nCrops with partial mapping (e.g. missing 2nd/3rd image): {len(missing_partially)}")
for c in missing_partially:
    imgs = crop_images[c]
    counts = sum(1 for x in imgs if x is not None)
    print(f" [?] {c} ({counts}/3 slots filled)")

# Check for extra files in media/crops
# (I'll do this in a separate command but list the used files here)
used_files = set()
for list_of_imgs in crop_images.values():
    for img in list_of_imgs:
        if img:
            used_files.add(img)

print(f"\nTotal image files used in mapping: {len(used_files)}")

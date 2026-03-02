
import os

crop_images = {
    "apple":        ["apple2.jpg", "apple3.jpg", "apple1.jpeg"],
    "banana":       ["b1.webp", "b2.jpg", "banana3.webp"],
    "barley":       ["c1.webp", "c2.jpg", "c3.jpg"],
    "bajra":        ["bajra1.jpg", "bajra2.webp", "bajra3.avif"],
    "ber":          ["ber1.webp", "ber2.jpg", "ber3.webp"],
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
    "pigeonpea":    ["pigeonpeas1.jpg", "pigeonpeas2.jpg", None],
    "pigeonpeas":   ["pigeonpeas1.jpg", "pigeonpeas2.jpg", None],
    "pomegranate":  ["pomegranate.png", "pomegranate2.jpg", "pomegranate3.jpg"],
    "potato":       ["potato1.jpeg", "potato2.jpg", None],
    "radish":       ["radish3.jpg", None, None],
    "rice":         ["rice1.jpeg", "rice2.jpg", "rice3.avif"],
    "sapota":       ["sapota1.webp", "sapota3.webp", None],
    "sesamum":      ["sesame1.jpg", "sesame2.webp", None],
    "sesame":       ["sesame1.jpg", "sesame2.webp", None],
    "soybean":      ["soybean1.webp", "soybean3.webp", None],
    "spinach":      ["spinach2.jpg", "spinach3.jpg", None],
    "sugarcane":    ["sugarcane1.webp", "sugarcane2.jpg", "sugarcane3.avif"],
    "tobacco":      ["tobacco1.webp", "tobacco.jpg", None],
    "tomato":       ["tomato1.jpg", "tomato3.jpg", None],
    "watermelon":   ["watermelon1.jpg", "watermelon3.webp", None],
    "wheat":        ["wheat2.jpg", "wheat3.png", None],
}

used_files = set()
for list_of_imgs in crop_images.values():
    for img in list_of_imgs:
        if img:
            used_files.add(img)

directory = r"Backend/app/media/crops"
all_files = set([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])

unused_files = all_files - used_files

print("--- UNUSED IMAGE FILES FOUND ---")
if not unused_files:
    print("None! All files are mapped.")
else:
    for f in sorted(list(unused_files)):
        print(f" [-] {f}")

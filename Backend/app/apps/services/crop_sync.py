"""
Crop Sync Service
=================
Fetches crop lists from HuggingFace Space (original/real) and maintains
a hardcoded synthetic crop list.  Provides idempotent DB sync.
"""

import logging
from typing import Dict, List, Set, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_HF_TIMEOUT = 15  # seconds


# ═════════════════════════════════════════════════════════════════════════
# 1) Fetch original (HF v3) crops from /health endpoint
# ═════════════════════════════════════════════════════════════════════════

# Static fallback — mirrors the HF v3 label_encoder.classes_ (19 crops)
_HF_FALLBACK_CROPS = sorted([
    "barley", "castor", "chickpea", "cotton", "finger_millet",
    "groundnut", "linseed", "maize", "mustard", "pearl_millet",
    "pigeonpea", "rice", "safflower", "sesamum", "sorghum",
    "soybean", "sugarcane", "sunflower", "wheat",
])


def fetch_hf_crops(use_fallback: bool = True) -> List[str]:
    """
    Try to fetch crops from the HuggingFace Space.

    Attempts ``/crops`` then ``/`` endpoints.  Falls back to a static
    19-crop list when *use_fallback* is True (default).

    Returns
    -------
    list[str]  – crop names (lowercase)
    """
    base = getattr(settings, "HF_MODEL_URL", "") or ""
    base = base.rstrip("/")
    if not base:
        logger.warning("HF_MODEL_URL not configured — using fallback crop list")
        return list(_HF_FALLBACK_CROPS) if use_fallback else []

    # Try /crops first (lightweight), then / (health)
    for path in ("/crops", "/"):
        url = f"{base}{path}"
        try:
            resp = requests.get(url, timeout=_HF_TIMEOUT, headers={
                "Accept": "application/json",
                "User-Agent": "CRS-Backend/1.0",
            })
            resp.raise_for_status()
            data = resp.json()
            crops = data.get("crops") or data.get("available_crops") or []
            if crops:
                logger.info("Fetched %d HF crops from %s", len(crops), url)
                return [c.strip().lower() for c in crops if c and c.strip()]
        except Exception as exc:
            logger.warning("HF %s failed: %s", url, exc)

    # All endpoints failed — use static fallback
    if use_fallback:
        logger.info("HF unreachable — using static fallback (%d crops)", len(_HF_FALLBACK_CROPS))
        return list(_HF_FALLBACK_CROPS)
    return []


# ═════════════════════════════════════════════════════════════════════════
# 2) Synthetic crops (from Crop_recommendation_v2.csv / model_rf)
# ═════════════════════════════════════════════════════════════════════════

# 51 crops from the synthetic v2 dataset used to train model_rf
_SYNTHETIC_CROPS = sorted([
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


def get_synthetic_crops() -> List[str]:
    """Return the hardcoded list of synthetic-model crops."""
    return list(_SYNTHETIC_CROPS)


# ═════════════════════════════════════════════════════════════════════════
# 3) Merge & sync to DB
# ═════════════════════════════════════════════════════════════════════════

# Default metadata for crops (season + yield).
# Anything not listed here gets "Unknown" / "Varies".
_CROP_METADATA: Dict[str, Dict[str, str]] = {
    # Cereals
    "rice":       {"season": "Kharif",      "yield": "3-6 tons/hectare"},
    "wheat":      {"season": "Rabi",        "yield": "2-4 tons/hectare"},
    "maize":      {"season": "Kharif/Rabi", "yield": "5-8 tons/hectare"},
    "barley":     {"season": "Rabi",        "yield": "2-3 tons/hectare"},
    "jowar":      {"season": "Kharif",      "yield": "1.5-3 tons/hectare"},
    "bajra":      {"season": "Kharif",      "yield": "1-2 tons/hectare"},
    "ragi":       {"season": "Kharif",      "yield": "1-2 tons/hectare"},
    # Pulses
    "chickpea":   {"season": "Rabi",            "yield": "0.8-1.5 tons/hectare"},
    "kidneybeans":{"season": "Kharif",          "yield": "1-1.5 tons/hectare"},
    "pigeonpeas": {"season": "Kharif",          "yield": "0.8-1.2 tons/hectare"},
    "mothbeans":  {"season": "Kharif",          "yield": "0.3-0.5 tons/hectare"},
    "mungbean":   {"season": "Kharif/Summer",   "yield": "0.5-1 tons/hectare"},
    "blackgram":  {"season": "Kharif",          "yield": "0.5-1 tons/hectare"},
    "lentil":     {"season": "Rabi",            "yield": "0.8-1.2 tons/hectare"},
    "soybean":    {"season": "Kharif",          "yield": "1.5-2.5 tons/hectare"},
    # Fruits
    "apple":          {"season": "Year-round", "yield": "10-15 tons/hectare"},
    "banana":         {"season": "Year-round", "yield": "30-50 tons/hectare"},
    "grapes":         {"season": "Year-round", "yield": "20-25 tons/hectare"},
    "mango":          {"season": "Summer",     "yield": "8-12 tons/hectare"},
    "orange":         {"season": "Winter",     "yield": "15-20 tons/hectare"},
    "papaya":         {"season": "Year-round", "yield": "40-60 tons/hectare"},
    "pomegranate":    {"season": "Year-round", "yield": "12-18 tons/hectare"},
    "watermelon":     {"season": "Summer",     "yield": "25-35 tons/hectare"},
    "muskmelon":      {"season": "Summer",     "yield": "15-20 tons/hectare"},
    "coconut":        {"season": "Year-round", "yield": "10000-15000 nuts/ha"},
    "guava":          {"season": "Year-round", "yield": "15-25 tons/hectare"},
    "sapota":         {"season": "Year-round", "yield": "15-20 tons/hectare"},
    "custard_apple":  {"season": "Monsoon",    "yield": "6-10 tons/hectare"},
    "date_palm":      {"season": "Summer",     "yield": "8-10 tons/hectare"},
    "ber":            {"season": "Winter",     "yield": "8-12 tons/hectare"},
    # Vegetables
    "tomato":     {"season": "Year-round",      "yield": "25-40 tons/hectare"},
    "potato":     {"season": "Rabi",            "yield": "20-30 tons/hectare"},
    "onion":      {"season": "Rabi/Kharif",     "yield": "25-35 tons/hectare"},
    "brinjal":    {"season": "Year-round",      "yield": "30-40 tons/hectare"},
    "carrot":     {"season": "Rabi",            "yield": "25-35 tons/hectare"},
    "radish":     {"season": "Rabi",            "yield": "20-30 tons/hectare"},
    "spinach":    {"season": "Rabi",            "yield": "10-15 tons/hectare"},
    "okra":       {"season": "Summer/Kharif",   "yield": "10-15 tons/hectare"},
    "cucumber":   {"season": "Summer",          "yield": "20-30 tons/hectare"},
    # Spices
    "green_chilli": {"season": "Kharif",  "yield": "1.5-2.5 tons/hectare"},
    # Cash / Industrial
    "cotton":     {"season": "Kharif",      "yield": "1.5-2.5 tons/hectare"},
    "jute":       {"season": "Kharif",      "yield": "2-3 tons/hectare"},
    "sugarcane":  {"season": "Kharif",      "yield": "70-100 tons/hectare"},
    "coffee":     {"season": "Year-round",  "yield": "0.5-1 tons/hectare"},
    "groundnut":  {"season": "Kharif",      "yield": "1.5-2 tons/hectare"},
    "mustard":    {"season": "Rabi",        "yield": "1-1.5 tons/hectare"},
    "sesame":     {"season": "Kharif",      "yield": "0.3-0.5 tons/hectare"},
    "castor":     {"season": "Kharif",      "yield": "1-1.5 tons/hectare"},
    "tobacco":    {"season": "Rabi",        "yield": "1.5-2.5 tons/hectare"},
    # Merged categories
    "gourd":      {"season": "Summer",  "yield": "15-25 tons/hectare"},
    "cole_crop":  {"season": "Rabi",    "yield": "25-35 tons/hectare"},
    "citrus":     {"season": "Winter",  "yield": "15-20 tons/hectare"},
}


def sync_crops_to_db(
    hf_crops: List[str] | None = None,
    synthetic_crops: List[str] | None = None,
) -> Tuple[int, int, int]:
    """
    Merge original (HF) + synthetic crop lists and create missing
    ``Crop`` objects in the database.  **Idempotent** — safe to run
    multiple times.

    Parameters
    ----------
    hf_crops : list[str] | None
        If None, fetches from HF automatically.
    synthetic_crops : list[str] | None
        If None, uses the hardcoded list.

    Returns
    -------
    (created, skipped, total)
    """
    from apps.models import Crop  # local import to avoid circular deps

    if hf_crops is None:
        hf_crops = fetch_hf_crops()
    if synthetic_crops is None:
        synthetic_crops = get_synthetic_crops()

    all_crops: Set[str] = set()
    all_crops.update(c.lower().strip() for c in hf_crops if c)
    all_crops.update(c.lower().strip() for c in synthetic_crops if c)

    created = 0
    skipped = 0

    for crop_name in sorted(all_crops):
        meta = _CROP_METADATA.get(crop_name, {})
        _, was_created = Crop.objects.get_or_create(
            name__iexact=crop_name,
            defaults={
                "name": crop_name,
                "season": meta.get("season"),
                "expected_yield": meta.get("yield"),
                "description": f"Crop: {crop_name}",
            },
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    total = Crop.objects.count()
    return created, skipped, total


# ═════════════════════════════════════════════════════════════════════════
# 4) Auto-assign image URLs from GitHub raw content
# ═════════════════════════════════════════════════════════════════════════

_GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/Henilshingala/"
    "crop-recomandation-system/main/Backend/app/media/crops/"
)

# Map: crop_name → [image1, image2, image3]  (None = no image for that slot)
# Derived from the actual files in Backend/app/media/crops/
_CROP_IMAGES: Dict[str, List[str | None]] = {
    "apple":        [None, "apple2.jpg", "apple3.jpg"],
    "banana":       ["b1.webp", "b2.jpg", None],
    "blackgram":    [None, "blackgram2.webp", None],
    "brinjal":      ["brinjal1.avif", "brinjal2.jpg", "brinjal3.webp"],
    "carrot":       ["carrot1.webp", "carrot2.webp", "carrot3.jpg"],
    "castor":       [None, None, "castor3.jpg"],
    "chickpea":     ["c1.webp", "c2.jpg", "c3.jpg"],
    "citrus":       [None, None, "citrus3.jpg"],
    "coconut":      ["coconut1.jpg", "coconut2.webp", "coconut3.jpg"],
    "coffee":       ["coffee1.jpg", "coffee2.avif", "coffee3.jpg"],
    "cole_crop":    [None, "cole_crop2.jpg", "cole_crop3.jpg"],
    "cotton":       ["c1.webp", "c2.jpg", "c3.jpg"],
    "date_palm":    ["date_palm1.webp", None, None],
    "gourd":        ["gourd1.webp", "gourd2.jpg", None],
    "grapes":       ["grapes1.webp", None, "grapes3.jpg"],
    "green_chilli": ["green_chilli1.jpg", "green_chilli2.webp", "green_chilli3.jpg"],
    "groundnut":    [None, None, "groundnut3.jpg"],
    "guava":        ["guava1.jpg", None, None],
    "jute":         ["jute1.webp", None, None],
    "maize":        [None, "maize2.webp", "maize3.jpg"],
    "mango":        [None, "mango2.jpg", "mango3.webp"],
    "mungbean":     ["mungbean1.webp", None, "mungbean3.webp"],
    "muskmelon":    ["muskmelon1.jpg", None, None],
    "mustard":      ["mustard1.avif", None, None],
    "okra":         [None, None, "okra3.jpg"],
    "onion":        ["onion1.jpg", "onion2.webp", "onion3.webp"],
    "papaya":       ["papaya1.jpg", None, "papaya3.webp"],
    "pigeonpeas":   ["pigeonpeas1.jpg", "pigeonpeas2.jpg", None],
    "pomegranate":  ["pomegranate.png", "pomegranate2.jpg", "pomegranate3.jpg"],
    "potato":       ["potato1.jpeg", "potato2.jpg", None],
    "radish":       [None, None, "radish3.jpg"],
    "rice":         ["rice1.jpeg", "rice2.jpg", "rice3.avif"],
    "sapota":       ["sapota1.webp", None, "sapota3.webp"],
    "sesame":       ["sesame1.jpg", "sesame2.webp", None],
    "soybean":      ["soybean1.webp", None, "soybean3.webp"],
    "spinach":      [None, "spinach2.jpg", "spinach3.jpg"],
    "sugarcane":    ["sugarcane1.webp", "sugarcane2.jpg", "sugarcane3.avif"],
    "tobacco":      ["tobacco1.webp", "tobacco.jpg", None],
    "tomato":       ["tomato1.jpg", None, "tomato3.jpg"],
    "watermelon":   ["watermelon1.jpg", None, "watermelon3.webp"],
    "wheat":        [None, "wheat2.jpg", "wheat3.png"],
}


def assign_image_urls() -> Tuple[int, int]:
    """
    For every Crop in the DB, set ``image_url`` / ``image_2_url`` /
    ``image_3_url`` to the GitHub raw URL.  Also clears stale
    ``image`` / ``image_2`` / ``image_3`` file fields that point
    to local files that don't exist on Render.

    **Always overwrites** URL fields — idempotent and safe.

    Returns
    -------
    (updated_count, skipped_count)
    """
    from apps.models import Crop

    updated = 0
    skipped = 0

    for crop in Crop.objects.all():
        images = _CROP_IMAGES.get(crop.name.lower())
        if not images:
            skipped += 1
            continue

        changed = False

        # Slot 1
        if images[0]:
            new_url = f"{_GITHUB_RAW_BASE}{images[0]}"
            if crop.image_url != new_url:
                crop.image_url = new_url
                changed = True
            # Clear stale file field (doesn't exist on Render)
            if crop.image and crop.image.name:
                crop.image = None
                changed = True

        # Slot 2
        if images[1]:
            new_url = f"{_GITHUB_RAW_BASE}{images[1]}"
            if crop.image_2_url != new_url:
                crop.image_2_url = new_url
                changed = True
            if crop.image_2 and crop.image_2.name:
                crop.image_2 = None
                changed = True

        # Slot 3
        if images[2]:
            new_url = f"{_GITHUB_RAW_BASE}{images[2]}"
            if crop.image_3_url != new_url:
                crop.image_3_url = new_url
                changed = True
            if crop.image_3 and crop.image_3.name:
                crop.image_3 = None
                changed = True

        if changed:
            crop.save()
            updated += 1
        else:
            skipped += 1

    return updated, skipped

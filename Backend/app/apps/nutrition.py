"""Nutrition data — loaded once at startup from Nutrient.csv."""

import csv
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

_CACHE: dict[str, dict] | None = None


def _path() -> str:
    env = os.environ.get("AI_ML_DIR")
    if env:
        return os.path.join(env, "Nutrient.csv")
    return os.path.join(settings.BASE_DIR.parent.parent, "Aiml", "Nutrient.csv")


def load_nutrition_cache() -> dict[str, dict]:
    """Load and cache nutrition data. Called at startup via AppConfig.ready()."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    cache = {}
    try:
        path = _path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    food = row.get("food_name", "").lower().strip()
                    if food:
                        cache[food] = {
                            "protein_g": float(row.get("protein_g_per_kg", 0)),
                            "fat_g": float(row.get("fat_g_per_kg", 0)),
                            "carbs_g": float(row.get("carbs_g_per_kg", 0)),
                            "fiber_g": float(row.get("fiber_g_per_kg", 0)),
                            "iron_mg": float(row.get("iron_mg_per_kg", 0)),
                            "calcium_mg": float(row.get("calcium_mg_per_kg", 0)),
                            "vitamin_a_mcg": float(row.get("vitamin_a_mcg_per_kg", 0)),
                            "vitamin_c_mg": float(row.get("vitamin_c_mg_per_kg", 0)),
                            "energy_kcal": float(row.get("energy_kcal_per_kg", 0)),
                            "water_g": float(row.get("water_g_per_kg", 0)),
                        }
            _CACHE = cache
            logger.info("Loaded %d nutrition entries at startup", len(cache))
        else:
            logger.warning("Nutrient.csv not found at %s", path)
    except Exception as e:
        logger.warning("Nutrition CSV load failed: %s", e)
    return _CACHE or {}


def get_nutrition_data(crop_name: str) -> dict | None:
    """Lookup nutrition from cache (loaded at startup)."""
    cache = load_nutrition_cache()
    search = crop_name.lower().strip()
    if search in cache:
        return cache[search]
    for food, data in cache.items():
        if food in search or search in food:
            return data
    return None

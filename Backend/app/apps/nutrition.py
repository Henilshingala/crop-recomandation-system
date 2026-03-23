"""Nutrition data — loaded once at startup from Nutrient.csv."""

import csv
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

_CACHE: dict[str, dict] | None = None


def _path() -> str:
    """Robust path discovery for Nutrient.csv."""
    possible_paths = [
        # Local & Render relative structure
        os.path.join(settings.BASE_DIR, "..", "..", "Aiml", "Nutrient.csv"),
        os.path.join(settings.BASE_DIR, "..", "Aiml", "Nutrient.csv"),
        # Absolute Render path
        "/opt/render/project/src/Aiml/Nutrient.csv",
    ]
    
    for p in possible_paths:
        if p and os.path.exists(p):
            logger.info(f"Found Nutrient.csv at: {p}")
            return p
            
    # Default fallback to parent of parent
    fallback = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "..", "Aiml", "Nutrient.csv"))
    logger.warning(f"Nutrient.csv not found, falling back to: {fallback}")
    return fallback


def load_nutrition_cache() -> dict[str, dict]:
    """Load and cache nutrition data. Called at startup via AppConfig.ready()."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    
    cache = {}
    try:
        path = _path()
        if not os.path.exists(path):
            logger.error(f"Cannot load nutrition: {path} does not exist.")
            return {}

        with open(path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                food = row.get("food_name", "").lower().strip()
                if food:
                    try:
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
                    except ValueError:
                        continue
                        
        _CACHE = cache
        logger.info("Loaded %d nutrition entries from %s", len(cache), path)
    except Exception as e:
        logger.exception("Nutrition CSV load failed")
        
    return _CACHE or {}


def get_nutrition_data(crop_name: str) -> dict | None:
    """Lookup nutrition from cache."""
    cache = load_nutrition_cache()
    if not cache:
        return None
        
    search = crop_name.lower().strip()
    
    # Simple normalization for common crop naming variations
    if search in cache:
        return cache[search]
        
    # Partial matching for names like "rice (white)"
    for food, data in cache.items():
        if food in search or search in food:
            return data
            
    return None


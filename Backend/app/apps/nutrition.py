"""Nutrition data — loaded once at startup from Nutrient.csv."""

import csv
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

_CACHE: dict[str, dict] | None = None


def _path() -> str:
    """Robust path discovery for Nutrient.csv (upward search)."""
    # 1. Check environment variable first
    env_path = os.environ.get("AI_ML_DIR")
    if env_path:
        p = os.path.join(env_path, "Nutrient.csv")
        if os.path.exists(p): return p

    # 2. Aggressive upward search from BASE_DIR
    # This handles both root-based and Backend/app-based execution
    curr = settings.BASE_DIR
    for _ in range(4):
        # Check in Aiml/ sibling or child
        p1 = os.path.join(curr, "Aiml", "Nutrient.csv")
        if os.path.exists(p1): return p1
        
        # Check in current dir directly
        p2 = os.path.join(curr, "Nutrient.csv")
        if os.path.exists(p2): return p2
        
        # Go up one level
        parent = os.path.dirname(curr)
        if parent == curr: break
        curr = parent

    # 3. Last resort hardcoded paths
    hardcoded = [
        "/opt/render/project/src/Aiml/Nutrient.csv",
        os.path.abspath(os.path.join(settings.BASE_DIR, "..", "..", "Aiml", "Nutrient.csv")),
    ]
    for h in hardcoded:
        if os.path.exists(h): return h
            
    return hardcoded[-1]


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
    """Lookup nutrition from cache with robust fuzzy matching."""
    cache = load_nutrition_cache()
    if not cache:
        return None
        
    search = crop_name.lower().strip()
    
    # 1. Exact match
    if search in cache:
        return cache[search]
        
    # 2. Match without parentheses (e.g. "mustard (sarson)" -> "mustard")
    def clean(s: str) -> str:
        # Remove anything in (...) and [...]
        import re
        s = re.sub(r'\(.*?\)', '', s)
        s = re.sub(r'\[.*?\]', '', s)
        return s.strip().lower()

    clean_search = clean(search)
    if not clean_search:
        return None

    # Try exact match on cleaned name
    if clean_search in cache:
        return cache[clean_search]

    # 3. Partial matching on cleaned names
    for food, data in cache.items():
        clean_food = clean(food)
        if clean_food == clean_search or clean_food in clean_search or clean_search in clean_food:
            return data
            
    # 4. First-word match (e.g. "mustard" matches "mustard (seed)")
    search_parts = clean_search.split()
    if search_parts:
        first_word = search_parts[0]
        for food, data in cache.items():
            if clean(food).startswith(first_word):
                return data
                
    return None


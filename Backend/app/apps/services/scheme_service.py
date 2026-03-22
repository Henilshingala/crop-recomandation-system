import json
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

_SCHEMES_CACHE = None
_CATEGORIES_CACHE = None
_STATES_CACHE = None

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    "All India"
]

def load_schemes():
    """Load multilingual schemes JSON file (raw, unprocessed)."""
    global _SCHEMES_CACHE
    if _SCHEMES_CACHE is not None:
        return _SCHEMES_CACHE

    json_path = Path(str(getattr(settings, 'SCHEMES_JSON_PATH', 'agriculture_schemes_multilingual.json')))

    if not json_path.exists():
        logger.error(f"Multilingual schemes JSON not found at {json_path}")
        _SCHEMES_CACHE = []
        return _SCHEMES_CACHE

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            _SCHEMES_CACHE = json.load(f)
        logger.info(f"Loaded {len(_SCHEMES_CACHE)} multilingual schemes.")
        return _SCHEMES_CACHE
    except Exception as e:
        logger.exception(f"Error loading schemes: {e}")
        _SCHEMES_CACHE = []
        return _SCHEMES_CACHE


def get_filter_options():
    """Get available states and categories for frontend dropdowns."""
    global _CATEGORIES_CACHE, _STATES_CACHE

    if _CATEGORIES_CACHE and _STATES_CACHE:
        return {"states": _STATES_CACHE, "categories": _CATEGORIES_CACHE}

    try:
        schemes = load_schemes()
        all_states = set()
        all_categories = set()

        for scheme in schemes:
            if not isinstance(scheme, dict): continue
            
            en = scheme.get("en") or {}
            name = str(en.get("scheme_name") or en.get("name") or "")
            desc = str(en.get("description") or "")
            cat = str(en.get("category") or "")

            # Categories (add all unique categories split by comma)
            if cat:
                for c in cat.split(","):
                    if c.strip():
                        all_categories.add(c.strip())

            # Infer states from English text (name+desc)
            text = f"{name} {desc}".lower()
            found = False
            for state in INDIAN_STATES:
                if state.lower() in text and state != "All India":
                    all_states.add(state)
                    found = True
            if not found:
                all_states.add("All India")

        _CATEGORIES_CACHE = sorted(list(all_categories))
        _STATES_CACHE = sorted(list(all_states))
        
        # Ensure 'All India' is at the top of the states list
        if "All India" in _STATES_CACHE:
            _STATES_CACHE.remove("All India")
        _STATES_CACHE.insert(0, "All India")

        return {"states": _STATES_CACHE, "categories": _CATEGORIES_CACHE}
    except Exception as e:
        logger.exception(f"Error in get_filter_options: {e}")
        return {"states": ["All India"], "categories": ["Agriculture"]}


def get_filtered_schemes(state="", category="", keyword="", farmer_type="",
                          income_level="", land_size="", language="en",
                          page=1, per_page=1000):
    """Filter schemes and return content in requested language with pagination."""
    try:
        schemes = load_schemes()

        state_lower   = str(state).lower().strip()
        keyword_lower = str(keyword).lower().strip()
        category_lower = str(category).lower().strip()
        filtered = []
        
        # Format language parameter securely, fallback 'hi-IN' to 'hi'
        target_lang = str(language).split('-')[0].lower() if language else "en"

        for scheme in schemes:
            if not isinstance(scheme, dict): continue
            
            # Always base filtering on English content
            en = scheme.get("en") or {}
            name        = str(en.get("scheme_name") or en.get("name") or "").strip()
            desc        = str(en.get("description") or "").strip()
            benefits    = str(en.get("benefits") or "").strip()
            eligibility = str(en.get("eligibility") or "").strip()
            cat         = str(en.get("category") or "").strip()

            text_all = f"{name} {desc} {benefits} {cat}".lower()

            # State filter
            if state_lower and state_lower != "all india":
                if state_lower not in text_all:
                    continue

            # Category filter (on English)
            if category_lower:
                if category_lower not in cat.lower():
                    continue

            # Keyword filter (on English)
            if keyword_lower:
                if keyword_lower not in text_all:
                    continue

            # Build response in requested language, fallback to English block
            lang_block = scheme.get(target_lang) or scheme.get("en") or {}

            # Using English as definitive fallback for each field if missing or empty
            t_name        = str(lang_block.get("scheme_name") or lang_block.get("name") or name).strip()
            t_desc        = str(lang_block.get("description") or desc).strip()
            t_benefits    = str(lang_block.get("benefits") or benefits).strip()
            t_eligibility = str(lang_block.get("eligibility") or eligibility).strip()
            t_category    = str(lang_block.get("category") or cat).strip()

            # Infer states from English text
            scheme_states = [s for s in INDIAN_STATES if s.lower() in text_all and s != "All India"]
            if not scheme_states:
                scheme_states = ["All India"]

            filtered.append({
                "scheme_name":       t_name,
                "description":       t_desc,
                "short_description": t_desc[:150] + "..." if len(t_desc) > 150 else t_desc,
                "benefits":          t_benefits,
                "eligibility":       t_eligibility,
                "categories":        [c.strip() for c in t_category.split(",") if c.strip()] or ["Agriculture"],
                "states":            scheme_states,
                "url":               str(scheme.get("url") or ""),
            })

        # Pagination
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered[start:end]

        return {
            "results": paginated,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
        }
    except Exception as e:
        logger.exception(f"Error in get_filtered_schemes: {e}")
        return {
            "results": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "pages": 0,
        }
import json
import time
import os
from deep_translator import GoogleTranslator

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

INPUT_FILE    = r"agriculture_schemes.json"
OUTPUT_FILE   = r"agriculture_schemes_multilingual.json"
PROGRESS_FILE = r"progress.json"

# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE CODES (Google Translate codes)
# ─────────────────────────────────────────────────────────────────────────────

LANG_CODES = {
    "hi":  "hi",
    "gu":  "gu",
    "bn":  "bn",
    "mr":  "mr",
    "ta":  "ta",
    "te":  "te",
    "kn":  "kn",
    "ml":  "ml",
    "pa":  "pa",
    "or":  "or",
    "as":  "as",
    "ne":  "ne",
    "sd":  "sd",
    "sa":  "sa",
    "mai": "mai",
    "mni": "mni-Mtei",
    "ks":  "ks",
    "gom": "kok",
    "brx": "hi",    # Bodo not supported → fallback Hindi
    "sat": "sat",
    "doi": "hi",    # Dogri not supported → fallback Hindi
    "ur":  "ur",
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(results):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def translate_text(text, google_code):
    """Translate English text to target language. Returns original on failure."""
    if not text or not text.strip():
        return text
    try:
        result = GoogleTranslator(source="en", target=google_code).translate(text)
        return result if result else text
    except Exception as e:
        print(f"      Warning: translate to {google_code} failed: {e}")
        return text  # fallback to English

def translate_scheme(scheme):
    """
    Translate one scheme into all 22 languages.
    Returns dict with lang_code → {scheme_name, description, benefits, eligibility, category}
    """
    name        = scheme.get("scheme_name", "")
    description = scheme.get("description", "")
    benefits    = scheme.get("benefits", "")
    eligibility = scheme.get("eligibility", "")
    category    = scheme.get("category", "")

    lang_blocks = {}

    for our_code, google_code in LANG_CODES.items():
        print(f"      → {our_code} ({google_code})")
        lang_blocks[our_code] = {
            "scheme_name": translate_text(name, google_code),
            "description": translate_text(description, google_code),
            "benefits":    translate_text(benefits, google_code),
            "eligibility": translate_text(eligibility, google_code),
            "category":    translate_text(category, google_code),
        }
        time.sleep(0.1)  # small delay between each language

    return lang_blocks

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Load input
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        schemes = json.load(f)

    total = len(schemes)
    print(f"Total schemes: {total}")

    # Load progress (resume support)
    progress = load_progress()
    print(f"Already done: {len(progress)}\n")

    for i, scheme in enumerate(schemes):
        scheme_id = str(i + 1)

        if scheme_id in progress:
            print(f"[{i+1}/{total}] Skipping {scheme.get('scheme_name','')[:50]} (already done)")
            continue

        print(f"\n[{i+1}/{total}] {scheme.get('scheme_name','')[:60]}")

        try:
            lang_blocks = translate_scheme(scheme)

            # Build output entry in your expected format
            entry = {
                "id":  scheme_id,
                "url": scheme.get("url", ""),
                "en": {
                    "name":        scheme.get("scheme_name", ""),
                    "description": scheme.get("description", ""),
                    "benefits":    scheme.get("benefits", ""),
                    "eligibility": scheme.get("eligibility", ""),
                    "category":    scheme.get("category", ""),
                },
            }
            # Add all language blocks
            entry.update(lang_blocks)

            progress[scheme_id] = entry
            save_progress(progress)
            print(f"  Saved scheme {scheme_id}")

            time.sleep(0.3)  # pause between schemes

        except Exception as e:
            print(f"  Error on scheme {scheme_id}: {e} — skipping")
            time.sleep(5)

    # Write final output as a list sorted by id
    final = [progress[str(i+1)] for i in range(total) if str(i+1) in progress]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(final)} schemes saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
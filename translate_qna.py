import json
import time
import os
from deep_translator import GoogleTranslator

# Google Translate language codes mapping
LANG_CODES = {
    "en": "en",
    "as": "as",
    "bn": "bn",
    "brx": "hi",   # Bodo not supported → fallback Hindi
    "doi": "hi",   # Dogri not supported → fallback Hindi
    "gom": "kok",  # Konkani
    "gu": "gu",
    "hi": "hi",
    "kn": "kn",
    "ks": "ks",
    "mai": "mai",
    "ml": "ml",
    "mni": "mni-Mtei",  # Manipuri
    "mr": "mr",
    "ne": "ne",
    "or": "or",
    "pa": "pa",
    "sa": "sa",
    "sat": "sat",  # Santali
    "sd": "sd",
    "ta": "ta",
    "te": "te",
    "ur": "ur"
}

PROGRESS_FILE = "progress.json"
OUTPUT_FILE   = "multilingual_qna.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(results):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def translate_text(text, target_lang):
    """Translate text to target language using Google Translate (free)."""
    if target_lang == "en":
        return text
    try:
        translated = GoogleTranslator(source="en", target=target_lang).translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"    Warning: Could not translate to {target_lang}: {e}")
        return text  # fallback to English

def process_qna(qna_id, item):
    """Translate one Q&A into all languages."""
    translations = {}
    for our_code, google_code in LANG_CODES.items():
        print(f"    Translating → {our_code}...")
        translations[our_code] = {
            "question": translate_text(item["question"], google_code),
            "answer":   translate_text(item["answer"],   google_code)
        }
        time.sleep(0.3)  # small delay to avoid rate limit
    return {"translations": translations}

def main():
# NEW - use utf-8-sig to remove hidden BOM:
    with open("qna_input.json", "r", encoding="utf-8-sig") as f:
        qna_data = json.load(f)

    total = len(qna_data)
    print(f"Total Q&As: {total}")

    results = load_progress()
    print(f"Already done: {len(results)}")

    for i, item in enumerate(qna_data):
        qna_id = f"QNA{i + 1}"

        if qna_id in results:
            continue  # skip already done

        print(f"\n[{i+1}/{total}] Processing {qna_id}...")
        print(f"  Q: {item['question'][:60]}...")

        try:
            results[qna_id] = process_qna(qna_id, item)
            save_progress(results)
            print(f"  Saved {qna_id}")
            time.sleep(1.0)  # pause between Q&As

        except Exception as e:
            print(f"  Error on {qna_id}: {e}, skipping...")
            time.sleep(5)

    # Save final file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(results)} Q&As saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
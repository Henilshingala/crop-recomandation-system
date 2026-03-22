import json
import os
import time
import requests
import re
from aiohttp import ClientSession
import asyncio

INPUT_FILE = r'D:\downloads\CRS\Frontend\src\locales\ai_en.json'
OUTPUT_FILE = r'D:\downloads\CRS\Frontend\src\locales\ai_multilingual.json'

LANG_MAP = {
    "as": "as", "bn": "bn", "brx": "brx", "doi": "doi", "gom": "gom",
    "gu": "gu", "hi": "hi", "kn": "kn", "ks": "ks", "mai": "mai",
    "ml": "ml", "mni": "mni", "mr": "mr", "ne": "ne", "or": "or",
    "pa": "pa", "sa": "sa", "sat": "sat", "sd": "sd", "ta": "ta",
    "te": "te", "ur": "ur"
}

# The public undocumented Google Translate API.
def get_google_translate_url(target):
    # Some overrides since Google might use slightly different codes in the free API
    target = 'mni-Mtei' if target == 'mni' else target
    return f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target}&dt=t"

async def translate_batch(session, texts, target_lang):
    """
    Translates a list of texts by concatenating them with a unique delimiter.
    Google API limits to ~5000 chars per GET.
    """
    delimiter = "\n ||| \n"
    # Ensure chunking respects length limits
    batches = []
    current_batch = []
    current_len = 0
    for text in texts:
        l = len(text) + len(delimiter)
        if current_len + l > 3500: # Safe margin
            batches.append(current_batch)
            current_batch = [text]
            current_len = l
        else:
            current_batch.append(text)
            current_len += l
            
    if current_batch:
        batches.append(current_batch)
        
    translated_texts = []
    for b in batches:
        joined_text = delimiter.join(b)
        url = get_google_translate_url(target_lang)
        params = {'q': joined_text}
        
        # Retry mechanism
        for attempt in range(3):
            try:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res_str = ''.join([part[0] for part in data[0] if part[0]])
                        
                        # Split back
                        parts = [p.strip() for p in res_str.split('|||')]
                        # Handle cases where google eats or duplicates delimiters
                        if len(parts) == len(b):
                            translated_texts.extend(parts)
                        else:
                            # Fallback: if splitting fails, keep english
                            translated_texts.extend(b)
                        break
                    else:
                        await asyncio.sleep(1)
            except Exception as e:
                await asyncio.sleep(1)
        else:
            # If all 3 attempts fail, fallback to English
            translated_texts.extend(b)
            
    return translated_texts

async def process_language(session, lang_code, questions, answers, data, results):
    print(f"Translating into {lang_code}...")
    try:
        translated_qs = await translate_batch(session, questions, lang_code)
        translated_as = await translate_batch(session, answers, lang_code)
        
        # Validate lengths
        if len(translated_qs) != len(questions):
            translated_qs = questions
        if len(translated_as) != len(answers):
            translated_as = answers
            
    except Exception as e:
        print(f"Error {lang_code}: {e}")
        translated_qs = questions
        translated_as = answers
        
    # Inject back into results dictionary
    for idx, item in enumerate(data):
        qna_id = f"QNA{idx + 1}"
        results[qna_id]["translations"][lang_code] = {
            "question": translated_qs[idx],
            "answer": translated_as[idx]
        }

async def async_main():
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} items.")
    questions = [item['question'] for item in data]
    answers = [item['answer'] for item in data]
    
    results = {}
    for idx in range(len(data)):
        qna_id = f"QNA{idx + 1}"
        results[qna_id] = {
            "translations": {
                "en": {
                    "question": questions[idx],
                    "answer": answers[idx]
                }
            }
        }
    
    # Process 4 languages concurrently to balance speed and rate limits
    async with ClientSession() as session:
        sem = asyncio.Semaphore(4)
        
        async def sem_task(lang_code):
            async with sem:
                await process_language(session, lang_code, questions, answers, data, results)
                
        tasks = [sem_task(lang) for lang in LANG_MAP.keys()]
        await asyncio.gather(*tasks)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Saved multilingual JSON to {OUTPUT_FILE}")

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    start = time.time()
    main()
    print(f"Done in {time.time() - start:.1f}s")

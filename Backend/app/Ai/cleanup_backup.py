import json
import re
import os

LANGUAGES = [
    "English", "Gujarati", "Hindi", "Marathi", "Tamil", "Telugu", 
    "Kannada", "Bengali", "Punjabi", "Malayalam", "Odia", "Urdu", 
    "Assamese", "Nepali", "Sanskrit", "Maithili", "Dogri", "Konkani", 
    "Manipuri", "Santali", "Sindhi", "Kashmiri"
]

def clean_and_format():
    file_path = "D:/downloads/CRS/Backend/app/Ai/Ai_backup.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all list blocks [...]
    # We look for blocks starting with "[" and ending with "]" that contain quoted strings
    blocks = re.findall(r'\[\s*(?:"[^"]*"(?:\s*,\s*"[^"]*")*)\s*\]', content, re.DOTALL)
    
    # Filter out small blocks and ensure we have enough
    blocks = [b for b in blocks if len(b) > 100]
    
    print(f"Detected {len(blocks)} language blocks.")
    
    result = {}
    for i, block_str in enumerate(blocks):
        if i >= len(LANGUAGES):
            break
        
        lang_name = LANGUAGES[i]
        
        # Parse the block safely
        # Fix some common errors like "word" "word" (missing comma) or "word", ] (extra comma)
        cleaned_block = block_str.strip()
        # Ensure commas between quotes if missing
        cleaned_block = re.sub(r'\"\s+\"', '", "', cleaned_block)
        # Remove trailing comma before closing bracket
        cleaned_block = re.sub(r',\s*\]', ']', cleaned_block)
        
        try:
            phrases = json.loads(cleaned_block)
            # Remove any empty strings or duplicates
            phrases = [p.strip() for p in phrases if p.strip()]
            result[lang_name] = phrases
        except Exception as e:
            print(f"Failed to parse {lang_name} block: {e}")
            # Fallback regex extraction if json.loads fails
            phrases = re.findall(r'\"([^\"]+)\"', cleaned_block)
            result[lang_name] = [p.strip() for p in phrases if p.strip()]

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(result)} languages to {file_path}")

if __name__ == "__main__":
    clean_and_format()

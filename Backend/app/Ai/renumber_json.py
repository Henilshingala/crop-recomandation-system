import json
import os
import re

def extract_number(key):
    match = re.search(r'QNA(\d+)', key)
    return int(match.group(1)) if match else 0

def renumber_json(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Loading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Sort keys numerically
    sorted_keys = sorted(data.keys(), key=extract_number)
    
    new_data = {}
    print(f"Renumbering {len(sorted_keys)} entries...")
    
    for i, old_key in enumerate(sorted_keys, 1):
        new_key = f"QNA{i}"
        new_data[new_key] = data[old_key]

    # Save to a temporary file first
    temp_file = file_path + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    # Rename temp to original
    os.replace(temp_file, file_path)
    print(f"Successfully renumbered and saved to {file_path}")

if __name__ == "__main__":
    ai_json_path = os.path.join(os.path.dirname(__file__), "Ai.json")
    renumber_json(ai_json_path)

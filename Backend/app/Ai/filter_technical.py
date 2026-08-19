import json
import os

filepath = r"D:\downloads\CRS\Backend\app\Ai\Ai.json"
backup_path = r"D:\downloads\CRS\Backend\app\Ai\Ai_backup.json"

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Original size: {len(data)} entries")

# Keywords that indicate the question is about the system's technical implementation
tech_keywords = [
    "frontend", "back-end", "backend", "react", "django", "vite", "typescript",
    "ml model", "machine learning model", "random forest", "accuracy",
    "database", "sqlite", "server", "hosting", "render.com", "vercel",
    "api", "endpoint", "how does this system work", "how does the system work",
    "how is this system built", "what technology is used", "source code",
    "github repository", "how are crops recommended", "algorithm",
    "who developed", "who created", "who made", "developer", "creator",
    "architecture", "framework", "css", "html", "javascript"
]

filtered_data = {}
removed_count = 0

for key, entry in data.items():
    en_trans = entry.get("translations", {}).get("en", {})
    q = en_trans.get("question", "").lower()
    a = en_trans.get("answer", "").lower()
    
    # Check if any tech keyword is in the question or answer
    is_technical = False
    for kw in tech_keywords:
        if kw in q or kw in a:
            is_technical = True
            break
            
    if not is_technical:
        filtered_data[key] = entry
    else:
        removed_count += 1
        # print(f"Removed [{key}]: {q[:50]}...")

print(f"Removed {removed_count} technical entries.")
print(f"New size: {len(filtered_data)} entries")

# Backup the original
import shutil
shutil.copy2(filepath, backup_path)
print(f"Original backed up to: {backup_path}")

# Save the filtered data
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=4)
print("Saved filtered Ai.json")

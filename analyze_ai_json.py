import json
import os

path = r'd:\downloads\CRS\Frontend\src\locales\Ai.json'
size = os.path.getsize(path)
print(f"File size: {size / (1024*1024):.2f} MB")

with open(path, encoding='utf-8') as f:
    data = json.load(f)

print(f"Num QNA objects: {len(data)}")
first_key = list(data.keys())[0]
langs = list(data[first_key]['translations'].keys())
print(f"Num languages: {len(langs)}")
print(f"Languages: {', '.join(langs)}")

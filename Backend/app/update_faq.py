import json

# Load the Ai.json file
with open(r'D:\downloads\CRS\Backend\app\Ai\Ai.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all unique questions from all languages
all_questions = set()

for qna_key, qna_value in data.items():
    translations = qna_value.get('translations', {})
    for lang, content in translations.items():
        question = content.get('question', '').strip()
        if question:
            all_questions.add(question)

# Sort questions alphabetically
sorted_questions = sorted(all_questions)

# Write to faq_questions.txt
with open(r'D:\downloads\CRS\Backend\app\Ai\faq_questions.txt', 'w', encoding='utf-8') as f:
    for question in sorted_questions:
        f.write(question + '\n')

print(f"Updated faq_questions.txt with {len(sorted_questions)} questions from Ai.json")
print(f"First 10 questions:")
for i, q in enumerate(sorted_questions[:10]):
    print(f"{i+1}. {q}")

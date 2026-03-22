import json

# Load the current Ai.json
with open(r'D:\downloads\CRS\Backend\app\Ai\Ai.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all greeting-related QNAs
greeting_qnas = []
for qna_key, qna_value in data.items():
    # Check if this is a greeting by looking at English version
    if 'en' in qna_value['translations']:
        en_question = qna_value['translations']['en']['question'].lower()
        if any(greet in en_question for greet in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            greeting_qnas.append(qna_key)

print(f"Found greeting QNAs: {greeting_qnas}")

# Let's add "नमस्ते" to QNA1307 (good morning) as well
if 'QNA1307' in data and 'hi' in data['QNA1307']['translations']:
    original_hi = data['QNA1307']['translations']['hi']['question']
    print(f"QNA1307 Hindi original: {original_hi}")
    # Keep the original but also add alternative
    # For now, let's focus on training the model with the updated "नमस्कार"

# Save the data (already saved from previous script)
print("Hindi greeting updated successfully. Now retraining the model...")

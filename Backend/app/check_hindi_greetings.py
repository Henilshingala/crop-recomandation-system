import pickle
import re

path = r'D:\downloads\CRS\Backend\app\Ai\trained_model.pkl'
with open(path, 'rb') as f:
    m = pickle.load(f)

print('Searching for any Hindi greetings or similar words:')
hindi_greeting_patterns = ['नमस्कार', 'नमस्ते', 'राम', 'प्रणाम', 'जय']

found_greetings = []
for meta in m['metadata']:
    if meta['lang'] == 'hi':
        question = meta['original_question'].lower()
        for pattern in hindi_greeting_patterns:
            if pattern in question:
                found_greetings.append((meta['original_question'], meta['qna_key']))
                break

if found_greetings:
    print('Found Hindi greetings:')
    for greeting, qna_key in found_greetings:
        print(f'  {greeting} (QNA: {qna_key})')
else:
    print('No Hindi greetings found in the model')
    
print('\nChecking if there are any greeting translations:')
# Check if QNA1301 (the greeting) has Hindi translation
for meta in m['metadata']:
    if meta['qna_key'] == 'QNA1301' and meta['lang'] == 'hi':
        print(f'Found Hindi greeting: {meta["original_question"]}')
        break
else:
    print('No Hindi translation found for greeting QNA1301')

import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from Ai.nlp_utils import tokenize_and_clean

# Test the exact same logic as the view
path = r'D:\downloads\CRS\Backend\app\Ai\trained_model.pkl'
with open(path, 'rb') as f:
    m = pickle.load(f)

user_question = "नमस्कार"
requested_lang = "gu"

# Step 1 & 2 & 3: Tokenize and clean input
cleaned_input = tokenize_and_clean(user_question)
print(f'User question: {user_question}')
print(f'Cleaned input: {cleaned_input}')

# Auto detect language if not provided
from Ai.nlp_utils import detect_language
detected_lang = detect_language(user_question)
lang_to_use = requested_lang if requested_lang else detected_lang
print(f'Detected language: {detected_lang}')
print(f'Language to use: {lang_to_use}')

# Step 4: Match against Ai.json
vectorizer = m['vectorizer']
vectors = m['vectors']
metadata = m['metadata']

input_vector = vectorizer.transform([cleaned_input])
similarities = cosine_similarity(input_vector, vectors).flatten()

# ── INTENT RECOGNITION & TRANSLATION LOOKUP ──────────────
# 1) Find the absolute best match across ALL languages to understand the intent
best_idx = int(np.argmax(similarities))
best_score = similarities[best_idx]

print(f'Best score: {best_score}')
print(f'Threshold: 0.25')

best_match = None

if best_score >= 0.25:
    matched_meta = metadata[best_idx]
    matched_qna_key = matched_meta['qna_key']
    
    print(f'Matched QNA key: {matched_qna_key}')
    print(f'Matched meta: {matched_meta}')
    
    # 2) We know what they asked. Now find the answer in their REQUESTED language.
    target_translation = None
    for meta in metadata:
        if meta['qna_key'] == matched_qna_key and meta['lang'] == lang_to_use:
            target_translation = meta
            break
            
    print(f'Target translation found: {target_translation is not None}')
    
    # Use the requested language if available, else fallback to the language they asked in
    if target_translation:
        best_match = target_translation
        print(f'Using requested language translation')
    else:
        best_match = matched_meta
        print(f'Using fallback language: {matched_meta["lang"]}')
else:
    print('Score below threshold, no match found')

if best_match:
    print(f'Final answer: {best_match["answer"]}')
    print(f'Language used: {best_match["lang"]}')
else:
    print('No best match found')

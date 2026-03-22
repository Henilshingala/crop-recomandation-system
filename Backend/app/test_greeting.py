import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from Ai.nlp_utils import tokenize_and_clean

path = r'D:\downloads\CRS\Backend\app\Ai\trained_model.pkl'
with open(path, 'rb') as f:
    m = pickle.load(f)

vectorizer = m['vectorizer']
vectors = m['vectors']
metadata = m['metadata']

# Test similarity between "नमस्कार" and "hi"
test_question = "नमस्कार"
cleaned_input = tokenize_and_clean(test_question)
print(f'"नमस्कार" cleaned: {cleaned_input}')

# Find "hi" in the model
hi_index = None
for i, meta in enumerate(metadata):
    if meta['original_question'] == 'hi' and meta['lang'] == 'en':
        hi_index = i
        break

if hi_index:
    hi_meta = metadata[hi_index]
    hi_cleaned = hi_meta['cleaned_question']
    print(f'"hi" cleaned: {hi_cleaned}')
    
    # Calculate direct similarity
    input_vector = vectorizer.transform([cleaned_input])
    hi_vector = vectors[hi_index:hi_index+1]
    similarity = cosine_similarity(input_vector, hi_vector).flatten()[0]
    print(f'Direct similarity: {similarity:.4f}')

# Also test with "नमस्ते"
test_question2 = "नमस्ते"
cleaned_input2 = tokenize_and_clean(test_question2)
print(f'\n"नमस्ते" cleaned: {cleaned_input2}')

input_vector2 = vectorizer.transform([cleaned_input2])
if hi_index:
    similarity2 = cosine_similarity(input_vector2, hi_vector).flatten()[0]
    print(f'Direct similarity with "hi": {similarity2:.4f}')

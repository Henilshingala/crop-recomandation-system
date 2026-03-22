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
print(f'Original: {test_question}')
print(f'Cleaned: {cleaned_input}')

input_vector = vectorizer.transform([cleaned_input])
similarities = cosine_similarity(input_vector, vectors).flatten()

# Find top matches
top_indices = np.argsort(similarities)[::-1][:5]
print(f'\nTop 5 matches for "{test_question}":')
for i, idx in enumerate(top_indices):
    score = similarities[idx]
    meta = metadata[idx]
    print(f'{i+1}. [{meta["lang"]}] {meta["original_question"]} - Score: {score:.4f}')

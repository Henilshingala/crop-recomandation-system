import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from .nlp_utils import tokenize_and_clean

# Consistency: use normalized paths
AI_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Ai.json')
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained_model.pkl')

import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from .nlp_utils import tokenize_and_clean

# Consistency: use normalized paths
AI_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Ai.json')
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained_model.pkl')

def train_model():
    with open(AI_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_questions = []
    all_metadata = []
    
    for qna_key, qna_value in data.items():
        translations = qna_value.get('translations', {})
        for lang, content in translations.items():
            question = content.get('question', '')
            answer = content.get('answer', '')
            if question and answer:
                cleaned = tokenize_and_clean(question)
                all_questions.append(cleaned)
                all_metadata.append({
                    'qna_key': qna_key,
                    'lang': lang,
                    'original_question': question,
                    'answer': answer,
                    'cleaned_question': cleaned
                })
    
    print(f"Training on {len(all_questions)} questions across all languages...")
    
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 4),
        max_features=50000
    )
    vectors = vectorizer.fit_transform(all_questions)
    
    model_data = {
        'vectorizer': vectorizer,
        'vectors': vectors,
        'metadata': all_metadata,
        'all_questions': all_questions
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Total vectors: {vectors.shape}")
    return model_data

if __name__ == '__main__':
    train_model()

import json
import logging
import os
import pickle
import numpy as np
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from sklearn.metrics.pairwise import cosine_similarity
from .nlp_utils import tokenize_and_clean, detect_language
from .models import MissingQuestion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)) )
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained_model.pkl')

THRESHOLD = 0.25

_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(MODEL_PATH):
            from .train import train_model
            _model_cache = train_model()
        else:
            with open(MODEL_PATH, 'rb') as f:
                _model_cache = pickle.load(f)
    return _model_cache

@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    try:
        user_question = request.data.get('question', '').strip()
        requested_lang = request.data.get('language', 'en')
        if not user_question:
            return JsonResponse({'error': 'Question is empty'}, status=400)
        cleaned_input = tokenize_and_clean(user_question)
        detected_lang = detect_language(user_question)
        lang_to_use = requested_lang if requested_lang else detected_lang
        model = get_model()
        vectorizer = model['vectorizer']
        vectors = model['vectors']
        metadata = model['metadata']
        input_vector = vectorizer.transform([cleaned_input])
        similarities = cosine_similarity(input_vector, vectors).flatten()
        top_indices = np.argsort(similarities)[::-1][:5]
        top_score = similarities[top_indices[0]]
        if top_score >= THRESHOLD:
            best_match = None
            best_score = 0
            for idx in top_indices:
                score = similarities[idx]
                if score < THRESHOLD:
                    break
                meta = metadata[idx]
                if meta['lang'] == lang_to_use and score > best_score:
                    best_match = meta
                    best_score = score
            if not best_match:
                best_match = metadata[top_indices[0]]
                best_score = top_score
            return JsonResponse({
                'answer': best_match['answer'],
                'matched': True,
                'score': round(float(best_score), 4),
                'matched_question': best_match['original_question'],
                'language_used': best_match['lang'],
                'qna_key': best_match['qna_key']
            })
        else:
            existing = MissingQuestion.objects.filter(
                question__iexact=user_question,
                language=lang_to_use
            ).first()
            if existing:
                existing.asked_count += 1
                existing.detected_language = detected_lang
                existing.save()
            else:
                MissingQuestion.objects.create(
                    question=user_question,
                    language=lang_to_use,
                    detected_language=detected_lang
                )
            return JsonResponse({
                'answer': "I can't answer this right now. Our team has been notified.",
                'matched': False,
                'score': round(float(top_score), 4)
            })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Chat endpoint error")
        return JsonResponse({'error': 'Internal server error'}, status=500)

def health(request):
    try:
        model = get_model()
        return JsonResponse({
            "status":    "ok",
            "questions": len(model['metadata']),
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": "Internal server error"}, status=500)


@staff_member_required
def missing_questions(request):
    if request.method == 'GET':
        questions = MissingQuestion.objects.filter(
            is_resolved=False
        ).order_by('-asked_count')[:50]

        data = [{
            'id': q.id,
            'question': q.question,
            'language': q.language,
            'asked_count': q.asked_count,
            'first_asked': q.first_asked.isoformat(),
        } for q in questions]

        return JsonResponse({
            'missing_questions': data,
            'total': len(data)
        })

    return JsonResponse({'error': 'GET required'}, status=405)

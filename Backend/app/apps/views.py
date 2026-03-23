"""
Crop Recommendation System - API Views
======================================
REST API endpoints for crop prediction and management.

V7 Unified Advisory:
  POST /api/predict/  → calls HF /recommend (no mode exposed)
"""

import csv
import logging
import os
import requests

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .models import Crop, PredictionLog
from .ml_inference import recommend_crops, predict_top_crops, get_predictor, get_available_crops
from .serializers import CropSerializer, PredictionLogSerializer
from .validators import SecurePredictionSerializer, FEATURE_RANGES, SAFE_RANGES
from .nutrition import get_nutrition_data
from .services.scheme_service import get_filtered_schemes, get_filter_options

logger = logging.getLogger(__name__)


# SecurePredictionSerializer and get_nutrition_data are now imported from centralized modules.


# ═════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════

# get_nutrition_data helper moved to nutrition.py


def index(request):
    return render(request, "apps/index.html")


# ═════════════════════════════════════════════════════════════════════════
# Prediction endpoint
# ═════════════════════════════════════════════════════════════════════════

class CropPredictionView(APIView):
    """
    POST /api/predict/

    Crop prediction via HuggingFace Space gateway.

    Request body
    ────────────
    {
        "N": 90, "P": 42, "K": 43,
        "temperature": 24.5, "humidity": 68,
        "ph": 6.7, "rainfall": 120,
        "mode": "soil",              // optional, default "soil" (aliases: original, synthetic)
        "soil_type": 1,              // optional, default 1 (loamy)
        "irrigation": 0,             // optional, default 0 (rainfed)
        "moisture": 43.5             // optional, accepted for compat
    }

    Response (200)
    ──────────────
    {
        "mode": "soil",
        "top_1": { "crop": "rice", "confidence": 98.6, "risk_level": "low", ... },
        "top_3": [ ... ],
        "model_info": { "coverage": 51, "type": "stacked-ensemble-v6", "version": "6.0" }
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # Use enhanced secure validation
        serializer = SecurePredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vd = serializer.validated_data

        # Add security warnings if any
        response_data = {}
        if hasattr(serializer, '_warnings'):
            response_data['security_warnings'] = serializer._warnings

        try:
            # V7 unified recommendation — no mode parameter.
            # All 3 models run internally; aggregated Top-3 returned.
            result = recommend_crops(
                n=vd["N"],
                p=vd["P"],
                k=vd["K"],
                temperature=vd["temperature"],
                humidity=vd["humidity"],
                ph=vd["ph"],
                rainfall=vd["rainfall"],
                soil_type=vd.get("soil_type", 1),
                irrigation=vd.get("irrigation", 0),
                moisture=vd.get("moisture", 43.5),
            )

            # Enrich top_3 with DB metadata (images, yield, season)
            result["top_3"] = [self._enrich(request, r) for r in result["top_3"]]

            # Derive top_1 from top_3[0] for backward compat
            if result["top_3"]:
                result["top_1"] = result["top_3"][0]
            else:
                result["top_1"] = {"crop": "unknown", "confidence": 0, "risk_level": "high"}

            # Log prediction
            self._log_prediction(request, vd, result)

            # Merge with any security warnings
            response_data.update(result)
            return Response(response_data, status=status.HTTP_200_OK)

        except (FileNotFoundError, ConnectionError, TimeoutError) as e:
            logger.error("ML service unavailable: %s", e)
            return Response(
                {"error": "ML service temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as e:
            logger.error("Invalid ML response format: %s", e)
            return Response(
                {"error": "Invalid response from ML service"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.exception("Unexpected prediction error")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ── enrichment ──────────────────────────────────────────────────────

    def _enrich(self, request, rec: dict) -> dict:
        """Add image URLs, yield, season, and nutrition to a recommendation dict."""
        crop_name = rec["crop"]
        try:
            crop = Crop.objects.get(name__iexact=crop_name)
            image_urls = [
                self._abs_image_url(request, crop, 1),
                self._abs_image_url(request, crop, 2),
                self._abs_image_url(request, crop, 3),
            ]
            rec["image_url"]      = image_urls[0]
            rec["image_urls"]     = image_urls
            rec["expected_yield"] = crop.expected_yield
            rec["season"]         = crop.season
        except Crop.DoesNotExist:
            placeholder = f"https://via.placeholder.com/300x200?text={crop_name}"
            rec.setdefault("image_url", placeholder)
            rec.setdefault("image_urls", [placeholder] * 3)
            rec.setdefault("expected_yield", None)
            rec.setdefault("season", None)

        # Prioritize local nutrition data if the API result is empty/null
        local_nutrition = get_nutrition_data(crop_name)
        if local_nutrition and not rec.get("nutrition"):
            rec["nutrition"] = local_nutrition
            
        return rec

    @staticmethod
    def _abs_image_url(request, crop: Crop, num: int) -> str:
        """Return the image URL — already absolute (GitHub/placeholder)."""
        url = crop.get_image_url(num)
        if not url:
            return f"https://via.placeholder.com/300x200?text={crop.name}+{num}"
        
        # If it's already an absolute URL (GitHub, placeholder, etc.) return as-is
        if url.startswith(("http://", "https://")):
            return url
        # Local media file — make absolute via request
        return request.build_absolute_uri(url)

    # ── logging ─────────────────────────────────────────────────────────

    @staticmethod
    def _log_prediction(request, input_data: dict, result: dict):
        try:
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
            PredictionLog.objects.create(
                nitrogen=input_data["N"],
                phosphorus=input_data["P"],
                potassium=input_data["K"],
                temperature=input_data["temperature"],
                humidity=input_data["humidity"],
                ph=input_data["ph"],
                rainfall=input_data["rainfall"],
                moisture=input_data.get("moisture"),
                soil_type=input_data.get("soil_type"),
                irrigation=input_data.get("irrigation"),
                mode="unified",
                model_version=result.get("model_info", {}).get("version", "7.1"),
                predictions=result.get("top_3", []),
                ip_address=ip,
            )
        except (KeyError, TypeError) as e:
            logger.error("Invalid input data for logging: %s", e)
        except Exception as e:
            logger.error("Database logging failed: %s", e)


# ═════════════════════════════════════════════════════════════════════════
# Media helpers (Cloudinary redirect)
# ═════════════════════════════════════════════════════════════════════════

def media_crops_list(request):
    crops = Crop.objects.all()
    html = "<h1>Index of /media/crops/</h1><hr><ul>"
    for crop in crops:
        for i in range(1, 4):
            url = crop.get_image_url(i)
            if url and not url.startswith("http"):
                html += f'<li><a href="/media/crops/{url.split("/")[-1]}">{url.split("/")[-1]}</a></li>'
            elif url:
                name = url.split("/")[-1]
                html += f'<li><a href="{url}">{name} (Cloudinary)</a></li>'
    html += "</ul>"
    return HttpResponse(html)


def media_crops_redirect(request, filename):
    """
    Smart proxy for crop images. 
    1. If a crop has an external URL, redirect to it.
    2. If it's a local file, serve it directly from the media folder.
    This prevents infinite redirect loops caused by the cache-busting v= query param.
    """
    import os
    from django.conf import settings
    from django.http import FileResponse, Http404

    # 1. Try to serve locally first (most common for repo-based images)
    local_path = os.path.join(settings.MEDIA_ROOT, 'crops', filename)
    if os.path.exists(local_path):
        return FileResponse(open(local_path, 'rb'))

    # 2. Otherwise, find the crop that owns this filename and check for external URL
    crops = Crop.objects.all()
    for crop in crops:
        for i in range(1, 4):
            url = crop.get_image_url(i)
            # Only redirect if it's a REAL remote URL (Cloudinary, GitHub, etc.)
            if url and filename in url and url.startswith(('http://', 'https://')):
                # Check that we aren't redirecting to OURSELVES
                if request.get_host() not in url:
                    return redirect(url)

    return HttpResponse("File not found or redirect loop prevented", status=404)


# ═════════════════════════════════════════════════════════════════════════
# Crop CRUD
# ═════════════════════════════════════════════════════════════════════════

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


# ═════════════════════════════════════════════════════════════════════════
# Health & utility endpoints
# ═════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """GET /api/health/ — verifies DB + ML availability."""
    info = {
        "status": "healthy",
        "database": "ok",
        "ml_model": "ok",
        "modes": ["soil", "extended", "both"],
    }

    # Simple DB check - avoid heavy queries
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        info["crop_count"] = "ok"
    except Exception:
        info["database"] = "error"
        info["status"] = "unhealthy"

    # ML crop counts (static lists — no network call)
    try:
        from .nutrition import load_nutrition_cache
        info["soil_crops"] = len(get_available_crops("soil"))
        info["extended_crops"] = len(get_available_crops("extended"))
        info["nutrition_cache_size"] = len(load_nutrition_cache())
    except Exception:
        info["ml_model"] = "error"
        info["status"] = "unhealthy"

    code = status.HTTP_200_OK if info["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(info, status=code)


@api_view(["GET"])
@permission_classes([AllowAny])
def available_crops(request):
    """GET /api/crops/available/?mode=soil|extended|both"""
    VALID_MODES = {"soil", "extended", "both"}
    mode = request.query_params.get("mode", "soil")
    if mode not in VALID_MODES:
        return Response(
            {"error": f"Invalid mode. Must be one of: {', '.join(sorted(VALID_MODES))}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        crops = get_available_crops(mode)
        return Response({"mode": mode, "count": len(crops), "crops": crops})
    except Exception as e:
        logger.error("Failed to get available crops: %s", e)
        return Response({"error": "Service temporarily unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def model_limits(request):
    """GET /api/model/limits/ — single source of truth for feature validation ranges.

    Returns the full feature_ranges.json content including:
      - acceptance: hard input limits used by Pydantic, Django, and the frontend
      - v6_soil_model: per-feature training statistics for V6 stacked ensemble
    """
    if FEATURE_RANGES:
        return Response(FEATURE_RANGES)
    # Fallback: return acceptance ranges only
    return Response({"acceptance": SAFE_RANGES})


# ═════════════════════════════════════════════════════════════════════════
# AI Assistant (Hybrid FAQ + OpenRouter)
# ═════════════════════════════════════════════════════════════════════════

from .services.faq_search import search_faq
from .services.openrouter_client import call_openrouter, FALLBACK_RESPONSE, _get_fallback
from .services.translator import translate_text, translate_to_english, _is_language_change_request

# English-only static messages (localized versions live in frontend JSON files;
# these are used only when the LLM translate_text call is needed as a fallback).
LANGUAGE_CHANGE_MSG_EN = (
    "To change the assistant language, please select your preferred "
    "language from the language menu in the website header. "
    "I will automatically respond in whichever language you select there. 🌐"
)
GREETING_EN = "Hello! I am Krishi Mitra 🌱. How can I help you with farming today?"


@api_view(["POST"])
@permission_classes([AllowAny])
def assistant_chat(request):
    """
    POST /api/assistant/chat/

    Hybrid FAQ search + OpenRouter LLM fallback.
    English is the internal processing language.
    Translation happens exactly once at the end.
    """
    user_message = request.data.get("message", "").strip()
    lang_code = request.data.get("lang", "en")

    if not user_message:
        return Response(
            {"error": "Message is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── Step 0: Detect in-chat language change requests ─────────────
    if _is_language_change_request(user_message):
        answer_en = LANGUAGE_CHANGE_MSG_EN
        final_answer = translate_text(answer_en, lang_code) if lang_code != "en" else answer_en
        return Response({"answer": final_answer, "source": "system"})

    # ── Step 1: Translate user message → English ────────────────────
    if lang_code != "en":
        user_message_en = translate_to_english(user_message, lang_code)
    else:
        user_message_en = user_message

    # ── Step 2: Handle simple greetings ─────────────────────────────
    GREETINGS = {"hi", "hello", "hey", "hii", "helo", "namaste", "namaskar"}
    if user_message_en.lower().strip() in GREETINGS:
        answer_en = GREETING_EN
        final_answer = translate_text(answer_en, lang_code) if lang_code != "en" else answer_en
        return Response({"answer": final_answer, "source": "greeting"})

    # ── Step 3: FAQ search (English) ────────────────────────────────
    try:
        faq_answer, score = search_faq(user_message_en)
        if faq_answer:
            logger.info("FAQ match (score=%.3f) for: %s", score, user_message_en[:80])
            answer_en = faq_answer
            final_answer = translate_text(answer_en, lang_code) if lang_code != "en" else answer_en
            return Response({"answer": final_answer, "source": "faq", "confidence": round(score, 3)})
    except Exception as e:
        logger.error("FAQ search failed: %s", e)

    # ── Step 4: LLM fallback (English) ──────────────────────────────────
    try:
        answer_en = call_openrouter(user_message_en)
    except Exception as e:
        logger.error("OpenRouter fallback failed: %s", e)
        answer_en = FALLBACK_RESPONSE

    # ── Step 5: Translate final answer → user's language (via NLLB) ─────
    final_answer = translate_text(answer_en, lang_code) if lang_code != "en" else answer_en
    return Response({"answer": final_answer, "source": "llm"})


class PredictionLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PredictionLog.objects.all()
    serializer_class = PredictionLogSerializer
    permission_classes = [IsAuthenticated]


# ═════════════════════════════════════════════════════════════════════════
# Scheme Recommendations
# ═════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([AllowAny])
def get_schemes(request):
    """GET /api/schemes/"""
    state = request.query_params.get("state", "")
    category = request.query_params.get("category", "")
    keyword = request.query_params.get("keyword", "")
    farmer_type = request.query_params.get("farmer_type", "")
    income_level = request.query_params.get("income_level", "")
    land_size = request.query_params.get("land_size", "")
    language = request.query_params.get("language", "en")

    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = min(1500, max(1, int(request.query_params.get("per_page", 1000))))
    except (ValueError, TypeError):
        per_page = 1000

    results = get_filtered_schemes(
        state=state,
        category=category,
        keyword=keyword,
        farmer_type=farmer_type,
        income_level=income_level,
        land_size=land_size,
        language=language,
        page=page,
        per_page=per_page,
    )
    return Response(results)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_scheme_options(request):
    """GET /api/schemes/options/ — returns available states and categories for filters."""
    options = get_filter_options()
    return Response(options)


@api_view(["GET"])
@permission_classes([AllowAny])
def nutrition_debug(request):
    """GET /api/debug/nutrition/?crop=mustard — diagnostic endpoint."""
    crop = request.query_params.get("crop", "rice")
    from .nutrition import get_nutrition_data, load_nutrition_cache, _path
    
    path = _path()
    exists = os.path.exists(path)
    cache = load_nutrition_cache()
    data = get_nutrition_data(crop)
    
    return Response({
        "crop": crop,
        "path": path,
        "exists": exists,
        "cache_size": len(cache),
        "data": data,
        "base_dir": settings.BASE_DIR,
    })


# ═════════════════════════════════════════════════════════════════════════
# Geocoding Proxy (Weather Feature)
# ═════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([AllowAny])
def geocode_location(request):
    """
    GET /api/geocode/?q=Mumbai,+Maharashtra,+India
    Proxies OpenCage API so the API key remains securely on the backend (Render).
    """
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"error": "Missing 'q' parameter"}, status=status.HTTP_400_BAD_REQUEST)

    api_key = os.environ.get("OPENCAGE_API_KEY") or os.environ.get("VITE_OPENCAGE_API_KEY")
    if not api_key:
        return Response({"error": "Geocoding API key not configured on server"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": query,
        "key": api_key,
        "limit": 1,
        "countrycode": "in",
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 402 or res.status_code == 429:
            return Response({"error": "Rate limit exceeded on Geocoding API"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        res.raise_for_status()
        return Response(res.json())
    except requests.RequestException as e:
        logger.error("Geocoding failed: %s", e)
        return Response({"error": "Failed to fetch geocoding data"}, status=status.HTTP_502_BAD_GATEWAY)


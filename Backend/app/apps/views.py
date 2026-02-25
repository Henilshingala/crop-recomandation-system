"""
Crop Recommendation System - API Views
======================================
REST API endpoints for crop prediction and management.

Prediction modes:
  POST /api/predict/  { ..., "mode": "original" | "synthetic" | "both" }
"""

import csv
import logging
import os

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
from .ml_inference import predict_top_crops, get_predictor, get_available_crops
from .serializers import CropSerializer, PredictionLogSerializer

logger = logging.getLogger(__name__)


class SecurePredictionSerializer(serializers.Serializer):
    """Simple secure serializer for prediction input."""
    N = serializers.FloatField(min_value=0, max_value=300)
    P = serializers.FloatField(min_value=0, max_value=200)
    K = serializers.FloatField(min_value=0, max_value=200)
    temperature = serializers.FloatField(min_value=-10, max_value=55)
    humidity = serializers.FloatField(min_value=0, max_value=100)
    ph = serializers.FloatField(min_value=0, max_value=14)
    rainfall = serializers.FloatField(min_value=0, max_value=1000)
    moisture = serializers.FloatField(min_value=0, max_value=100, required=False, default=43.5)
    season = serializers.IntegerField(min_value=0, max_value=2, required=False)
    soil_type = serializers.IntegerField(min_value=0, max_value=4, required=False)
    irrigation = serializers.IntegerField(min_value=0, max_value=1, required=False)
    top_n = serializers.IntegerField(min_value=1, max_value=10, required=False, default=3)
    mode = serializers.ChoiceField(choices=['original', 'synthetic', 'both'], default='both')


# ═════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════

def _nutrition_csv_path() -> str:
    env = os.environ.get("AI_ML_DIR")
    if env:
        return os.path.join(env, "Nutrient.csv")
    return os.path.join(settings.BASE_DIR.parent.parent, "Aiml", "Nutrient.csv")


def get_nutrition_data(crop_name: str) -> dict | None:
    """Lookup nutrition data from CSV."""
    try:
        path = _nutrition_csv_path()
        with open(path, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                food = row["food_name"].lower().strip()
                search = crop_name.lower().strip()
                if food == search or food in search or search in food:
                    return {
                        "protein_g":      float(row["protein_g_per_kg"]),
                        "fat_g":          float(row["fat_g_per_kg"]),
                        "carbs_g":        float(row["carbs_g_per_kg"]),
                        "fiber_g":        float(row["fiber_g_per_kg"]),
                        "iron_mg":        float(row["iron_mg_per_kg"]),
                        "calcium_mg":     float(row["calcium_mg_per_kg"]),
                        "vitamin_a_mcg":  float(row["vitamin_a_mcg_per_kg"]),
                        "vitamin_c_mg":   float(row["vitamin_c_mg_per_kg"]),
                        "energy_kcal":    float(row["energy_kcal_per_kg"]),
                        "water_g":        float(row["water_g_per_kg"]),
                    }
    except FileNotFoundError:
        logger.warning("Nutrition CSV file not found at %s", path)
    except (KeyError, ValueError) as e:
        logger.warning("Invalid nutrition data format for %s: %s", crop_name, e)
    except IOError as e:
        logger.warning("IO error reading nutrition CSV for %s: %s", crop_name, e)
    return None


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
        "mode": "original",          // optional, default "original"
        "soil_type": 1,              // optional, default 1 (loamy)
        "irrigation": 0,             // optional, default 0 (rainfed)
        "moisture": 43.5             // optional, default 43.5
    }

    Response (200)
    ──────────────
    {
        "mode": "original",
        "top_1": { "crop": "rice", "confidence": 98.6, "risk_level": "low", ... },
        "top_3": [ ... ],
        "model_info": { "coverage": 19, "type": "stacked-ensemble-v3", "version": "3.0" }
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
        mode = vd.get("mode", "original")
        
        # Add security warnings if any
        response_data = {}
        if hasattr(serializer, '_warnings'):
            response_data['security_warnings'] = serializer._warnings

        try:
            result = predict_top_crops(
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
                mode=mode,
            )

            # Enrich top_3 with DB metadata + nutrition
            result["top_3"] = [self._enrich(request, r) for r in result["top_3"]]

            # Derive top_1 from top_3[0]
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

        rec.setdefault("nutrition", get_nutrition_data(crop_name))
        return rec

    @staticmethod
    def _abs_image_url(request, crop: Crop, num: int) -> str:
        """Return the image URL — already absolute (GitHub/placeholder)."""
        url = crop.get_image_url(num)
        # If it's already an absolute URL (GitHub, placeholder, etc.) return as-is
        if url and url.startswith(("http://", "https://")):
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
    crops = Crop.objects.all()
    for crop in crops:
        for i in range(1, 4):
            url = crop.get_image_url(i)
            if url and filename in url:
                return redirect(url)
    return HttpResponse("File not found", status=404)


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
        "modes": ["original", "synthetic", "both"],
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
        info["original_crops"] = len(get_available_crops("original"))
        info["synthetic_crops"] = len(get_available_crops("synthetic"))
    except Exception:
        info["ml_model"] = "error"
        info["status"] = "unhealthy"

    code = status.HTTP_200_OK if info["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(info, status=code)


@api_view(["GET"])
@permission_classes([AllowAny])
def available_crops(request):
    """GET /api/crops/available/?mode=original|synthetic|both"""
    mode = request.query_params.get("mode", "original")
    try:
        crops = get_available_crops(mode)
        return Response({"mode": mode, "count": len(crops), "crops": crops})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PredictionLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PredictionLog.objects.all()
    serializer_class = PredictionLogSerializer
    permission_classes = [IsAuthenticated]

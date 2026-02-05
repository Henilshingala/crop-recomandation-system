"""
Crop Recommendation System - API Views
======================================
REST API endpoints for crop prediction and management.
"""

import logging
import csv
import os
from requests import request
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView 
from django.db import transaction
from django.shortcuts import render
from .models import Crop, PredictionLog
from .serializers import (
    CropSerializer,
    PredictionInputSerializer,
    PredictionResponseSerializer,
    PredictionLogSerializer
)
from .ml_inference import predict_top_crops, get_predictor

logger = logging.getLogger(__name__)

def get_nutrition_data(crop_name: str) -> dict:
    """
    Get nutrition data for a crop from CSV file.
    Returns nutrition information or None if not found.
    """
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AiMl', 'Nutrient.csv')
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Match crop name (case-insensitive, handle variations)
                food_name = row['food_name'].lower().strip()
                search_name = crop_name.lower().strip()
                
                # Direct match or partial match
                if food_name == search_name or food_name in search_name or search_name in food_name:
                    return {
                        'protein_g': float(row['protein_g_per_kg']),
                        'fat_g': float(row['fat_g_per_kg']),
                        'carbs_g': float(row['carbs_g_per_kg']),
                        'fiber_g': float(row['fiber_g_per_kg']),
                        'iron_mg': float(row['iron_mg_per_kg']),
                        'calcium_mg': float(row['calcium_mg_per_kg']),
                        'vitamin_a_mcg': float(row['vitamin_a_mcg_per_kg']),
                        'vitamin_c_mg': float(row['vitamin_c_mg_per_kg']),
                        'energy_kcal': float(row['energy_kcal_per_kg']),
                        'water_g': float(row['water_g_per_kg'])
                    }
        return None
    except Exception as e:
        logger.warning(f"Failed to get nutrition data for {crop_name}: {e}")
        return None

def index(request):
    return render(request, 'apps/index.html')

class CropPredictionView(APIView):
    """
    POST /api/predict/
    
    Main prediction endpoint that takes soil/climate parameters
    and returns top 3 crop recommendations with metadata.
    
    Request Body:
    {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 24.5,
        "humidity": 68,
        "ph": 6.7,
        "rainfall": 120
    }
    
    Response:
    {
        "recommendations": [
            {
                "crop": "rice",
                "confidence": 98.6,
                "image_url": "...",
                "expected_yield": "2-3 tons/hectare",
                "season": "Kharif"
            },
            ...
        ]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Validate input data
        serializer = PredictionInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            # Get ML predictions (top 3 crops with confidence)
            predictions = predict_top_crops(
                n=validated_data['N'],
                p=validated_data['P'],
                k=validated_data['K'],
                temperature=validated_data['temperature'],
                humidity=validated_data['humidity'],
                ph=validated_data['ph'],
                rainfall=validated_data['rainfall'],
                top_n=3
            )
            
            # Enrich predictions with crop metadata from database
            recommendations = []
            for pred in predictions:
                crop_name = pred['crop']
                confidence = pred['confidence']
                
                # Try to find crop in database for additional metadata
                try:
                    crop = Crop.objects.get(name__iexact=crop_name)
                    # Get all 3 image URLs for carousel
                    image_urls = [
                        self._get_absolute_image_url(request, crop, 1),
                        self._get_absolute_image_url(request, crop, 2),
                        self._get_absolute_image_url(request, crop, 3)
                    ]
                    recommendation = {
                        'crop': crop_name,
                        'confidence': confidence,
                        'image_url': image_urls[0],  # First image as default
                        'image_urls': image_urls,    # All 3 images for carousel
                        'expected_yield': crop.expected_yield,
                        'season': crop.season,
                        'nutrition': get_nutrition_data(crop_name)
                    }
                except Crop.DoesNotExist:
                    # Crop not in database - return basic info with placeholder
                    logger.warning(f"Crop '{crop_name}' not found in database")
                    placeholder_url = f"https://via.placeholder.com/300x200?text={crop_name}"
                    recommendation = {
                        'crop': crop_name,
                        'confidence': confidence,
                        'image_url': placeholder_url,
                        'image_urls': [placeholder_url, placeholder_url, placeholder_url],
                        'expected_yield': None,
                        'season': None,
                        'nutrition': get_nutrition_data(crop_name)
                    }
                
                recommendations.append(recommendation)
            
            # Log prediction for analytics (async-safe)
            self._log_prediction(request, validated_data, predictions)
            
            response_data = {'recommendations': recommendations}
            
            # Validate response format
            response_serializer = PredictionResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except FileNotFoundError as e:
            logger.error(f"ML model files not found: {e}")
            return Response(
                {"error": "ML model not available. Please contact admin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.exception(f"Prediction error: {e}")
            return Response(
                {"error": "Prediction failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_absolute_image_url(self, request, crop: Crop, image_number: int = 1) -> str:
        """Build absolute URL for crop image."""
        image_url = crop.get_image_url(image_number)
        
        # If it's an uploaded file, build absolute URL
        if image_number == 1 and crop.image and hasattr(crop.image, 'url'):
            return request.build_absolute_uri(image_url)
        elif image_number == 2 and crop.image_2 and hasattr(crop.image_2, 'url'):
            return request.build_absolute_uri(image_url)
        elif image_number == 3 and crop.image_3 and hasattr(crop.image_3, 'url'):
            return request.build_absolute_uri(image_url)
        
        return image_url
    
    def _log_prediction(self, request, input_data: dict, predictions: list):
        """
        Log prediction request for analytics.
        Non-blocking - errors won't affect the response.
        """
        try:
            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            PredictionLog.objects.create(
                nitrogen=input_data['N'],
                phosphorus=input_data['P'],
                potassium=input_data['K'],
                temperature=input_data['temperature'],
                humidity=input_data['humidity'],
                ph=input_data['ph'],
                rainfall=input_data['rainfall'],
                predictions=predictions,
                ip_address=ip_address
            )
        except Exception as e:
            logger.warning(f"Failed to log prediction: {e}")


class CropViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Crop model.
    
    GET /api/crops/ - List all crops
    GET /api/crops/{id}/ - Get specific crop
    POST /api/crops/ - Create crop (admin only)
    PUT /api/crops/{id}/ - Update crop (admin only)
    DELETE /api/crops/{id}/ - Delete crop (admin only)
    """
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    
    def get_permissions(self):
        """Only admins can create/update/delete."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    GET /api/health/
    
    Health check endpoint for monitoring.
    Verifies database and ML model availability.
    """
    health_status = {
        'status': 'healthy',
        'database': 'ok',
        'ml_model': 'ok',
        'available_crops': []
    }
    
    # Check database
    try:
        crop_count = Crop.objects.count()
        health_status['crop_count'] = crop_count
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check ML model
    try:
        predictor = get_predictor()
        health_status['available_crops'] = predictor.get_available_crops()
    except Exception as e:
        health_status['ml_model'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_crops(request):
    """
    GET /api/crops/available/
    
    Returns list of all crop labels the ML model can predict.
    Useful for frontend validation and debugging.
    """
    try:
        predictor = get_predictor()
        crops = predictor.get_available_crops()
        return Response({'crops': crops}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class PredictionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to prediction logs (for admin analytics).
    
    GET /api/logs/ - List all prediction logs
    GET /api/logs/{id}/ - Get specific log entry
    """
    queryset = PredictionLog.objects.all()
    serializer_class = PredictionLogSerializer
    permission_classes = [IsAuthenticated]

